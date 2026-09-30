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

    def format(self, source: str | None = None) -> str:
        """Render as `line:col: severity [stage]: message`, plus a caret
        under the offending column when the source text is available."""
        head = f"{self.line}:{self.col}: {self.severity.value} [{self.stage}]: {self.message}"
        if not source:
            return head
        lines = source.splitlines()
        if not 1 <= self.line <= len(lines):
            return head
        text = lines[self.line - 1].expandtabs(4)
        gutter = f"{self.line:>4} | "
        caret = " " * (len(gutter) + max(self.col - 1, 0)) + "^"
        return f"{head}\n{gutter}{text}\n{caret}"
