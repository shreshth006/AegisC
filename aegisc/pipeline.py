"""Runs the compiler stage by stage and collects every intermediate result.

The result is the single data structure the CLI, the web visualizer and the
LLM tutor all consume. Each stage records its output and its diagnostics.
A stage that can't safely run because an earlier stage failed is marked
"skipped" instead of being run on broken input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import ast as A
from .diagnostics import Diagnostic, has_errors
from .lexer import tokenize
from .parser import parse
from .semantic import analyze
from .symbols import SymbolTable
from .tokens import Token

STAGES = ("lexer", "parser", "semantic")


@dataclass
class StageResult:
    name: str
    status: str = "skipped"            # "ok" | "error" | "skipped"
    diagnostics: list[Diagnostic] = field(default_factory=list)
    output: Any = None

    def to_dict(self) -> dict:
        out = self.output
        if self.name == "lexer" and out is not None:
            out = [t.to_dict() for t in out]
        elif self.name == "parser" and out is not None:
            out = out.to_dict()
        elif self.name == "semantic" and out is not None:
            out = {"scopes": out.to_dict()}
        return {
            "stage": self.name,
            "status": self.status,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "output": out,
        }
