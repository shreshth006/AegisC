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


@dataclass
class CompilationResult:
    source: str
    stages: dict[str, StageResult]

    @property
    def ok(self) -> bool:
        return all(s.status == "ok" for s in self.stages.values())

    @property
    def tokens(self) -> list[Token] | None:
        return self.stages["lexer"].output

    @property
    def ast(self) -> A.Program | None:
        return self.stages["parser"].output

    @property
    def symbols(self) -> SymbolTable | None:
        return self.stages["semantic"].output

    @property
    def diagnostics(self) -> list[Diagnostic]:
        return [d for s in self.stages.values() for d in s.diagnostics]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "source": self.source,
            "stages": [s.to_dict() for s in self.stages.values()],
        }
