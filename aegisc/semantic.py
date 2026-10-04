"""Semantic analysis: scope resolution and type checking.

Two passes over the AST:
  1. Collect every function signature, so calls may come before
     definitions and mutual recursion works.
  2. Walk each function body: declare and resolve names, compute the type
     of every expression (written into `Expr.ty`), and check statements,
     calls and returns.

This phase does not do taint/provenance propagation; that belongs to the
PROBE pass. Here, `untrusted` declarations are only recorded in the
symbol table so that PROBE has its seeds.
"""
from __future__ import annotations

from typing import Optional

from . import ast as A
from .diagnostics import Diagnostic, Severity
from .symbols import Symbol, SymbolTable

INT, STRING, BOOL, VOID, ERROR = "int", "string", "bool", "void", "<error>"

# name -> (return type, param types or None for variadic, returns untrusted data)
BUILTINS: dict[str, tuple[str, Optional[list[str]], bool]] = {
    "print": (VOID, None, False),
    "input": (STRING, [], True),
    "input_int": (INT, [], True),
    "len": (INT, [STRING], False),
}
UNTRUSTED_SOURCES = frozenset(n for n, (_, _, src) in BUILTINS.items() if src)


def _a(t: str) -> str:
    """'an int', 'a string' -- for readable messages."""
    return f"an {t}" if t[:1] in "aeiou" else f"a {t}"


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.table = SymbolTable()
        self.diagnostics: list[Diagnostic] = []
        self.current_fn: Optional[A.FuncDecl] = None
        for name, (ret, params, src) in BUILTINS.items():
            self.table.declare(Symbol(name, "builtin", ret, params=params, untrusted=src))

    # -- reporting ---------------------------------------------------------
    def _err(self, node: A.Node, msg: str) -> None:
        self.diagnostics.append(Diagnostic("semantic", Severity.ERROR, msg, node.line, node.col))

    def _warn(self, node_or_sym, msg: str) -> None:
        self.diagnostics.append(Diagnostic("semantic", Severity.WARNING, msg, node_or_sym.line, node_or_sym.col))

    # -- entry ---------------------------------------------------------------
    def analyze(self, prog: A.Program) -> None:
        # Pass 1: signatures (globals are declared in order during pass 2).
        for d in prog.decls:
            if isinstance(d, A.FuncDecl):
                sym = Symbol(d.name, "function", d.ret_type, d.line, d.col,
                             params=[p.type for p in d.params],
                             param_untrusted=[p.untrusted for p in d.params])
                prev = self.table.declare(sym)
                if prev:
                    what = "a built-in function" if prev.kind == "builtin" else f"already declared at {prev.line}:{prev.col}"
                    self._err(d, f"function '{d.name}' redefined ({what})")

        # Pass 2: bodies and globals.
        for d in prog.decls:
            if isinstance(d, A.FuncDecl):
                self._function(d)
            elif isinstance(d, A.VarDecl):
                self._var_decl(d, global_=True)

        main = self.table.global_scope.lookup_local("main")
        if main is None or main.kind != "function":
            self.diagnostics.append(Diagnostic("semantic", Severity.WARNING,
                                               "program has no 'int main()' entry point", 1, 1))
        elif main.type != INT or main.params:
            self._warn(main, "'main' should be declared as 'int main()'")

        for scope in self.table.scopes[1:]:
            for sym in scope.symbols.values():
                if sym.kind == "variable" and not sym.used:
                    self._warn(sym, f"variable '{sym.name}' is declared but never used")

    # -- declarations ------------------------------------------------------------
    def _function(self, fn: A.FuncDecl) -> None:
        self.current_fn = fn
        self.table.enter(f"fn {fn.name}")
        for p in fn.params:
            if p.type == VOID:
                self._err(p, f"parameter '{p.name}' cannot have type void")
            prev = self.table.declare(Symbol(p.name, "parameter", p.type, p.line, p.col, untrusted=p.untrusted))
            if prev:
                self._err(p, f"duplicate parameter '{p.name}'")
        # The body block shares the function scope, so a local can't silently shadow a parameter.
        for stmt in fn.body.body:
            self._stmt(stmt)
        if fn.ret_type != VOID and not self._always_returns(fn.body):
            self._err(fn, f"function '{fn.name}' must return a value of type {fn.ret_type} on every path")
        self.table.exit()
        self.current_fn = None

    def _var_decl(self, d: A.VarDecl, global_: bool = False) -> None:
        if d.type == VOID:
            self._err(d, f"variable '{d.name}' cannot have type void")
        if d.init is not None:
            t = self._expr(d.init)
            self._require(d.init, t, d.type, f"cannot initialise {d.type} variable '{d.name}' with a value of type {t}")
        sym = Symbol(d.name, "variable", d.type, d.line, d.col, untrusted=d.untrusted)
        if global_:
            sym.used = True  # don't nag about unused globals
        prev = self.table.declare(sym)
        if prev:
            self._err(d, f"'{d.name}' is already declared in this scope (at {prev.line}:{prev.col})")

    # -- statements ----------------------------------------------------------------
    def _stmt(self, s: A.Stmt) -> None:
        if isinstance(s, A.VarDecl):
            self._var_decl(s)
        elif isinstance(s, A.Block):
            self.table.enter(f"block@{s.line}:{s.col}")
            for x in s.body:
                self._stmt(x)
            self.table.exit()
        elif isinstance(s, A.If):
            self._cond(s.cond, "if")
            self._stmt(s.then)
            if s.else_:
                self._stmt(s.else_)
        elif isinstance(s, A.While):
            self._cond(s.cond, "while")
            self._stmt(s.body)
        elif isinstance(s, A.For):
            self.table.enter(f"for@{s.line}:{s.col}")
            if s.init:
                self._stmt(s.init)
            if s.cond:
                self._cond(s.cond, "for")
            if s.update:
                self._expr(s.update)
            self._stmt(s.body)
            self.table.exit()
        elif isinstance(s, A.Return):
            self._return(s)
        elif isinstance(s, A.Spawn):
            self._expr(s.call)
        elif isinstance(s, A.ExprStmt):
            self._expr(s.expr)

    def _cond(self, e: A.Expr, kw: str) -> None:
        t = self._expr(e)
        self._require(e, t, BOOL, f"{kw} condition must be bool, got {t}")

    def _return(self, r: A.Return) -> None:
        fn = self.current_fn
        assert fn is not None
        if r.value is None:
            if fn.ret_type != VOID:
                self._err(r, f"'{fn.name}' must return a value of type {fn.ret_type}")
            return
        t = self._expr(r.value)
        if fn.ret_type == VOID:
            self._err(r, f"void function '{fn.name}' cannot return a value")
        else:
            self._require(r.value, t, fn.ret_type, f"'{fn.name}' returns {fn.ret_type}, but this expression has type {t}")

    def _always_returns(self, s: Optional[A.Stmt]) -> bool:
        if s is None:
            return False
        if isinstance(s, A.Return):
            return True
        if isinstance(s, A.Block):
            return any(self._always_returns(x) for x in s.body)
        if isinstance(s, A.If):
            return self._always_returns(s.then) and self._always_returns(s.else_)
        if isinstance(s, A.While) and isinstance(s.cond, A.BoolLiteral) and s.cond.value:
            return True  # `while (true)` only exits through a return
        return False

    # -- expressions -----------------------------------------------------------------
    def _require(self, node: A.Node, got: str, want: str, msg: str) -> None:
        if got != want and ERROR not in (got, want):
            self._err(node, msg)

    def _expr(self, e: A.Expr) -> str:
        e.ty = self._infer(e)
        return e.ty

    def _resolve_var(self, ident: A.Identifier) -> Optional[Symbol]:
        sym = self.table.lookup(ident.name)
        if sym is None:
            self._err(ident, f"use of undeclared identifier '{ident.name}'")
            return None
        if sym.kind in ("function", "builtin"):
            self._err(ident, f"'{ident.name}' is a function, not a variable")
            return None
        sym.used = True
        return sym
