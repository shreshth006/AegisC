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
