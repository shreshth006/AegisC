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
