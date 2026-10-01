"""Lexical analysis: source text -> list of tokens.

A hand-written scanner (no regex engine), so each step mirrors the DFA
description in the course notes. On a bad character the lexer reports a
diagnostic, skips the character and carries on, so that a single typo
doesn't hide the rest of the token stream from the visualizer.
"""
from __future__ import annotations

from .diagnostics import Diagnostic, Severity
from .tokens import KEYWORDS, ONE_CHAR_OPS, TWO_CHAR_OPS, Token, TokenType

INT_MAX = 2**31 - 1
ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.diagnostics: list[Diagnostic] = []

    # -- character helpers -------------------------------------------------
    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _error(self, msg: str, line: int, col: int) -> None:
        self.diagnostics.append(Diagnostic("lexer", Severity.ERROR, msg, line, col))
