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
