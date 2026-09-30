"""Diagnostics shared by every compiler stage.

Every stage reports problems as Diagnostic objects rather than raising, so
the visualizer can show all errors from a stage at once and the LLM tutor
can be asked to explain any one of them.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Diagnostic:
    stage: str          # "lexer" | "parser" | "semantic" | ...
    severity: Severity
    message: str
    line: int
    col: int

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d
