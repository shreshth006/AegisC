"""Scoped symbol table.

Scopes form a tree: global, then one scope per function, then one per block.
Every scope is kept after analysis finishes, not just the live chain, so
the visualizer can show the whole table with the nesting intact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Symbol:
    name: str
    kind: str                     # "variable" | "parameter" | "function" | "builtin"
    type: str                     # value type, or return type for functions
    line: int = 0
    col: int = 0
    untrusted: bool = False       # declared with `untrusted` (provenance seed for PROBE)
    params: Optional[list[str]] = None   # parameter types for functions; None = variadic
    param_untrusted: Optional[list[bool]] = None
    used: bool = False

    def to_dict(self) -> dict:
        d = {
            "name": self.name, "kind": self.kind, "type": self.type,
            "line": self.line, "col": self.col, "untrusted": self.untrusted,
            "used": self.used,
        }
        if self.kind in ("function", "builtin"):
            d["params"] = self.params
        return d


@dataclass
class Scope:
    id: int
    name: str                     # "global", "fn main", "block@3:5", ...
    parent: Optional["Scope"]
    level: int
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        s: Optional[Scope] = self
        while s is not None:
            if name in s.symbols:
                return s.symbols[name]
            s = s.parent
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "parent": self.parent.id if self.parent else None,
            "symbols": [sym.to_dict() for sym in self.symbols.values()],
        }
