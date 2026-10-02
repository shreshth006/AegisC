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
