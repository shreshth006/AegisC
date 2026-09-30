"""Token definitions for AegisC."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    # literals and names
    IDENT = "IDENT"
    INT_LIT = "INT_LIT"
    STRING_LIT = "STRING_LIT"

    # keywords
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    VOID = "void"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    FOR = "for"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    UNTRUSTED = "untrusted"
    SPAWN = "spawn"

    # operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"
    ASSIGN = "="
    PLUS_ASSIGN = "+="
    MINUS_ASSIGN = "-="
    STAR_ASSIGN = "*="
    SLASH_ASSIGN = "/="
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    AND = "&&"
    OR = "||"
    NOT = "!"
    INC = "++"
    DEC = "--"

    # delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    COMMA = ","
    SEMI = ";"

    EOF = "EOF"


KEYWORDS: dict[str, TokenType] = {
    t.value: t
    for t in (
        TokenType.INT, TokenType.STRING, TokenType.BOOL, TokenType.VOID,
        TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.FOR,
        TokenType.RETURN, TokenType.TRUE, TokenType.FALSE,
        TokenType.UNTRUSTED, TokenType.SPAWN,
    )
}

TYPE_KEYWORDS = frozenset({TokenType.INT, TokenType.STRING, TokenType.BOOL, TokenType.VOID})
