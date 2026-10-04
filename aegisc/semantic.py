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
