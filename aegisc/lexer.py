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

    # -- main loop ---------------------------------------------------------
    def tokenize(self) -> list[Token]:
        while self.pos < len(self.src):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                self._skip_line_comment()
            elif ch == "/" and self._peek(1) == "*":
                self._skip_block_comment()
            elif ch.isdigit():
                self._number()
            elif ch.isalpha() or ch == "_":
                self._identifier()
            elif ch == '"':
                self._string()
            else:
                self._operator()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens

    # -- scanners ----------------------------------------------------------
    def _skip_line_comment(self) -> None:
        while self.pos < len(self.src) and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        line, col = self.line, self.col
        self._advance(); self._advance()  # consume /*
        while self.pos < len(self.src):
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance(); self._advance()
                return
            self._advance()
        self._error("unterminated block comment", line, col)

    def _number(self) -> None:
        line, col, start = self.line, self.col, self.pos
        while self._peek().isdigit():
            self._advance()
        # `123abc` is one malformed token, not INT followed by IDENT.
        if self._peek().isalpha() or self._peek() == "_":
            while self._peek().isalnum() or self._peek() == "_":
                self._advance()
            self._error(f"invalid numeric literal '{self.src[start:self.pos]}'", line, col)
            return
        text = self.src[start:self.pos]
        value = int(text)
        if value > INT_MAX:
            self._error(f"integer literal {text} exceeds 32-bit range", line, col)
            value = INT_MAX
        self.tokens.append(Token(TokenType.INT_LIT, text, line, col, value))

    def _identifier(self) -> None:
        line, col, start = self.line, self.col, self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.src[start:self.pos]
        ttype = KEYWORDS.get(text, TokenType.IDENT)
        value = {"true": True, "false": False}.get(text) if ttype in (TokenType.TRUE, TokenType.FALSE) else None
        self.tokens.append(Token(ttype, text, line, col, value))

    def _string(self) -> None:
        line, col, start = self.line, self.col, self.pos
        self._advance()  # opening quote
        chars: list[str] = []
        while True:
            ch = self._peek()
            if ch == "" or ch == "\n":
                self._error("unterminated string literal", line, col)
                return
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                esc_line, esc_col = self.line, self.col
                self._advance()
                nxt = self._peek()
                if nxt in ESCAPES:
                    chars.append(ESCAPES[nxt])
                    self._advance()
                else:
                    self._error(f"unknown escape sequence '\\{nxt}'", esc_line, esc_col)
                continue
            chars.append(self._advance())
        self.tokens.append(Token(TokenType.STRING_LIT, self.src[start:self.pos], line, col, "".join(chars)))

    def _operator(self) -> None:
        line, col = self.line, self.col
        two = self._peek() + self._peek(1)
        if two in TWO_CHAR_OPS:
            self._advance(); self._advance()
            self.tokens.append(Token(TWO_CHAR_OPS[two], two, line, col))
            return
        ch = self._peek()
        if ch in ONE_CHAR_OPS:
            self._advance()
            self.tokens.append(Token(ONE_CHAR_OPS[ch], ch, line, col))
            return
        self._advance()
        hint = " (did you mean '&&' or '||'?)" if ch in "&|" else ""
        self._error(f"unexpected character '{ch}'{hint}", line, col)


def tokenize(source: str) -> tuple[list[Token], list[Diagnostic]]:
    lx = Lexer(source)
    tokens = lx.tokenize()
    return tokens, lx.diagnostics
