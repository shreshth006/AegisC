"""Syntax analysis: tokens -> AST.

This is a recursive-descent parser with one function per grammar rule in
docs/language.md. Expressions are parsed by precedence climbing, one level
per function.

Error recovery is panic mode. When a statement fails to parse, the parser
records a diagnostic, skips ahead to a synchronising token (`;`, `}` or the
start of a statement) and carries on, so one missing semicolon produces one
error instead of a cascade.
"""
from __future__ import annotations

from . import ast as A
from .diagnostics import Diagnostic, Severity
from .tokens import TYPE_KEYWORDS, Token, TokenType as T

ASSIGN_OPS = {T.ASSIGN, T.PLUS_ASSIGN, T.MINUS_ASSIGN, T.STAR_ASSIGN, T.SLASH_ASSIGN}
STMT_STARTS = {T.IF, T.WHILE, T.FOR, T.RETURN, T.SPAWN, T.LBRACE, T.UNTRUSTED} | TYPE_KEYWORDS


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.toks = tokens
        self.i = 0
        self.diagnostics: list[Diagnostic] = []

    # -- token helpers -----------------------------------------------------
    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def _peek(self, k: int = 1) -> Token:
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def _check(self, *types: T) -> bool:
        return self.cur.type in types

    def _advance(self) -> Token:
        tok = self.cur
        if tok.type is not T.EOF:
            self.i += 1
        return tok

    def _match(self, *types: T) -> Token | None:
        return self._advance() if self._check(*types) else None

    def _expect(self, ttype: T, what: str) -> Token:
        if self._check(ttype):
            return self._advance()
        # Report a missing ';' or ')' at the end of the previous token,
        # which is where the user's eye is, not at the next line.
        anchor = self.toks[self.i - 1] if ttype in (T.SEMI, T.RPAREN) and self.i > 0 else self.cur
        col = anchor.col + len(anchor.lexeme) if anchor is not self.cur else anchor.col
        found = "end of file" if self.cur.type is T.EOF else f"'{self.cur.lexeme}'"
        self._error(f"expected {what}, found {found}", anchor.line, col)
        raise ParseError

    def _error(self, msg: str, line: int, col: int) -> None:
        self.diagnostics.append(Diagnostic("parser", Severity.ERROR, msg, line, col))

    @staticmethod
    def _pos(tok: Token) -> dict:
        return {"line": tok.line, "col": tok.col}

    # -- recovery ----------------------------------------------------------
    def _sync_statement(self) -> None:
        while not self._check(T.EOF):
            if self._match(T.SEMI):
                return
            if self._check(T.RBRACE) or self.cur.type in STMT_STARTS:
                return
            self._advance()

    def _sync_toplevel(self) -> None:
        depth = 0
        while not self._check(T.EOF):
            if self._check(T.LBRACE):
                depth += 1
            elif self._check(T.RBRACE):
                depth -= 1
                if depth <= 0:
                    self._advance()
                    return
            elif depth == 0 and self.cur.type in TYPE_KEYWORDS | {T.UNTRUSTED}:
                return
            self._advance()

    # -- declarations --------------------------------------------------------
    def parse_program(self) -> A.Program:
        start = self.cur
        decls: list[A.Node] = []
        while not self._check(T.EOF):
            before = self.i
            try:
                decls.append(self._declaration())
            except ParseError:
                self._sync_toplevel()
                if self.i == before:  # guarantee progress
                    self._advance()
        return A.Program(decls, **self._pos(start))

    def _type(self) -> Token:
        if self.cur.type in TYPE_KEYWORDS:
            return self._advance()
        self._expect(T.INT, "a type (int, string, bool, void)")
        raise AssertionError  # unreachable

    def _declaration(self) -> A.Node:
        start = self.cur
        untrusted = self._match(T.UNTRUSTED) is not None
        ty = self._type()
        name = self._expect(T.IDENT, "an identifier")
        if self._check(T.LPAREN) and not untrusted:
            return self._func_rest(start, ty.lexeme, name.lexeme)
        return self._var_decl_rest(start, untrusted, ty.lexeme, name.lexeme)

    def _func_rest(self, start: Token, ret: str, name: str) -> A.FuncDecl:
        self._expect(T.LPAREN, "'('")
        params: list[A.Param] = []
        if not self._check(T.RPAREN):
            while True:
                pstart = self.cur
                pu = self._match(T.UNTRUSTED) is not None
                pty = self._type()
                pname = self._expect(T.IDENT, "a parameter name")
                params.append(A.Param(pty.lexeme, pname.lexeme, pu, **self._pos(pstart)))
                if not self._match(T.COMMA):
                    break
        self._expect(T.RPAREN, "')' after parameters")
        body = self._block()
        return A.FuncDecl(ret, name, params, body, **self._pos(start))

    def _var_decl_rest(self, start: Token, untrusted: bool, ty: str, name: str) -> A.VarDecl:
        init = self._expression() if self._match(T.ASSIGN) else None
        self._expect(T.SEMI, "';' after declaration")
        return A.VarDecl(ty, name, init, untrusted, **self._pos(start))

    def _var_decl(self) -> A.VarDecl:
        start = self.cur
        untrusted = self._match(T.UNTRUSTED) is not None
        ty = self._type()
        name = self._expect(T.IDENT, "a variable name")
        return self._var_decl_rest(start, untrusted, ty.lexeme, name.lexeme)

    # -- statements ----------------------------------------------------------
    def _block(self) -> A.Block:
        start = self._expect(T.LBRACE, "'{'")
        body: list[A.Stmt] = []
        while not self._check(T.RBRACE, T.EOF):
            before = self.i
            try:
                body.append(self._statement())
            except ParseError:
                self._sync_statement()
                if self.i == before:
                    self._advance()
        self._expect(T.RBRACE, "'}' to close block")
        return A.Block(body, **self._pos(start))

    def _statement(self) -> A.Stmt:
        tok = self.cur
        if tok.type in TYPE_KEYWORDS or tok.type is T.UNTRUSTED:
            return self._var_decl()
        if tok.type is T.IF:
            return self._if()
        if tok.type is T.WHILE:
            return self._while()
        if tok.type is T.FOR:
            return self._for()
        if tok.type is T.RETURN:
            self._advance()
            value = None if self._check(T.SEMI) else self._expression()
            self._expect(T.SEMI, "';' after return")
            return A.Return(value, **self._pos(tok))
        if tok.type is T.SPAWN:
            self._advance()
            expr = self._expression()
            if not isinstance(expr, A.Call):
                self._error("'spawn' must be followed by a function call", expr.line, expr.col)
                raise ParseError
            self._expect(T.SEMI, "';' after spawn")
            return A.Spawn(expr, **self._pos(tok))
        if tok.type is T.LBRACE:
            return self._block()
        if tok.type is T.ELSE:
            self._error("'else' without a matching 'if'", tok.line, tok.col)
            self._advance()
            raise ParseError
        expr = self._expression()
        self._expect(T.SEMI, "';' after expression")
        return A.ExprStmt(expr, **self._pos(tok))

    def _paren_cond(self, kw: str) -> A.Expr:
        self._expect(T.LPAREN, f"'(' after '{kw}'")
        cond = self._expression()
        self._expect(T.RPAREN, f"')' after {kw} condition")
        return cond

    def _if(self) -> A.If:
        tok = self._advance()
        cond = self._paren_cond("if")
        then = self._statement()
        else_ = self._statement() if self._match(T.ELSE) else None
        return A.If(cond, then, else_, **self._pos(tok))

    def _while(self) -> A.While:
        tok = self._advance()
        cond = self._paren_cond("while")
        return A.While(cond, self._statement(), **self._pos(tok))

    def _for(self) -> A.For:
        tok = self._advance()
        self._expect(T.LPAREN, "'(' after 'for'")
        if self._match(T.SEMI):
            init = None
        elif self.cur.type in TYPE_KEYWORDS or self._check(T.UNTRUSTED):
            init = self._var_decl()
        else:
            istart = self.cur
            e = self._expression()
            self._expect(T.SEMI, "';' after for-initializer")
            init = A.ExprStmt(e, **self._pos(istart))
        cond = None if self._check(T.SEMI) else self._expression()
        self._expect(T.SEMI, "';' after for-condition")
        update = None if self._check(T.RPAREN) else self._expression()
        self._expect(T.RPAREN, "')' after for-clauses")
        return A.For(init, cond, update, self._statement(), **self._pos(tok))

    # -- expressions (lowest to highest precedence) ------------------------------
    def _expression(self) -> A.Expr:
        return self._assignment()

    def _assignment(self) -> A.Expr:
        if self._check(T.IDENT) and self._peek().type in ASSIGN_OPS:
            name = self._advance()
            op = self._advance()
            value = self._assignment()  # right-associative
            target = A.Identifier(name.lexeme, **self._pos(name))
            return A.Assign(op.lexeme, target, value, **self._pos(name))
        expr = self._logic_or()
        if self.cur.type in ASSIGN_OPS:
            self._error("left side of assignment must be a variable", expr.line, expr.col)
            raise ParseError
        return expr

    def _binary_level(self, next_level, ops: set[T]) -> A.Expr:
        left = next_level()
        while self.cur.type in ops:
            op = self._advance()
            right = next_level()
            left = A.Binary(op.lexeme, left, right, **self._pos(op))
        return left

    def _logic_or(self):
        return self._binary_level(self._logic_and, {T.OR})

    def _logic_and(self):
        return self._binary_level(self._equality, {T.AND})

    def _equality(self):
        return self._binary_level(self._comparison, {T.EQ, T.NE})

    def _comparison(self):
        return self._binary_level(self._term, {T.LT, T.LE, T.GT, T.GE})

    def _term(self):
        return self._binary_level(self._factor, {T.PLUS, T.MINUS})

    def _factor(self):
        return self._binary_level(self._unary, {T.STAR, T.SLASH, T.PERCENT})

    def _unary(self) -> A.Expr:
        if self._check(T.NOT, T.MINUS):
            op = self._advance()
            return A.Unary(op.lexeme, self._unary(), **self._pos(op))
        if self._check(T.INC, T.DEC):
            op = self._advance()
            name = self._expect(T.IDENT, f"a variable after '{op.lexeme}'")
            return A.IncDec(op.lexeme, A.Identifier(name.lexeme, **self._pos(name)), True, **self._pos(op))
        return self._postfix()

    def _postfix(self) -> A.Expr:
        expr = self._primary()
        if self._check(T.INC, T.DEC):
            op = self._advance()
            if not isinstance(expr, A.Identifier):
                self._error(f"'{op.lexeme}' can only be applied to a variable", op.line, op.col)
                raise ParseError
            return A.IncDec(op.lexeme, expr, False, line=expr.line, col=expr.col)
        return expr

    def _primary(self) -> A.Expr:
        tok = self.cur
        if self._match(T.INT_LIT):
            return A.IntLiteral(tok.value, **self._pos(tok))
        if self._match(T.STRING_LIT):
            return A.StringLiteral(tok.value, **self._pos(tok))
        if self._match(T.TRUE, T.FALSE):
            return A.BoolLiteral(tok.value, **self._pos(tok))
        if self._match(T.IDENT):
            if self._match(T.LPAREN):
                args: list[A.Expr] = []
                if not self._check(T.RPAREN):
                    args.append(self._expression())
                    while self._match(T.COMMA):
                        args.append(self._expression())
                self._expect(T.RPAREN, "')' after arguments")
                return A.Call(tok.lexeme, args, **self._pos(tok))
            return A.Identifier(tok.lexeme, **self._pos(tok))
        if self._match(T.LPAREN):
            expr = self._expression()
            self._expect(T.RPAREN, "')'")
            return expr
        found = "end of file" if tok.type is T.EOF else f"'{tok.lexeme}'"
        self._error(f"expected an expression, found {found}", tok.line, tok.col)
        raise ParseError


def parse(tokens: list[Token]) -> tuple[A.Program, list[Diagnostic]]:
    p = Parser(tokens)
    prog = p.parse_program()
    return prog, p.diagnostics
