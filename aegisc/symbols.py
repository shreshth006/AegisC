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


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: list[Scope] = []
        self.current: Scope = self._new_scope("global", None)

    def _new_scope(self, name: str, parent: Optional[Scope]) -> Scope:
        scope = Scope(len(self.scopes), name, parent, 0 if parent is None else parent.level + 1)
        self.scopes.append(scope)
        return scope

    @property
    def global_scope(self) -> Scope:
        return self.scopes[0]

    def enter(self, name: str) -> Scope:
        self.current = self._new_scope(name, self.current)
        return self.current

    def exit(self) -> None:
        assert self.current.parent is not None, "cannot exit global scope"
        self.current = self.current.parent

    def declare(self, sym: Symbol) -> Optional[Symbol]:
        """Declare in the current scope. Returns the existing symbol on a
        redeclaration, in which case nothing is added."""
        existing = self.current.lookup_local(sym.name)
        if existing:
            return existing
        self.current.symbols[sym.name] = sym
        return None

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.current.lookup(name)

    def to_dict(self) -> list[dict]:
        return [s.to_dict() for s in self.scopes]
