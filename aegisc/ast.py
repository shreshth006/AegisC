"""Abstract syntax tree for AegisC.

Every node records its source position. Expression nodes also get a `ty`
slot that semantic analysis fills in, so the visualizer can show the type
of each subtree. `to_dict()` gives the JSON form the front end draws as a
tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional


@dataclass
class Node:
    line: int = field(default=0, kw_only=True)
    col: int = field(default=0, kw_only=True)

    @property
    def kind(self) -> str:
        return type(self).__name__

    def children(self) -> list["Node"]:
        out: list[Node] = []
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, Node):
                out.append(v)
            elif isinstance(v, list):
                out.extend(x for x in v if isinstance(x, Node))
        return out

    def to_dict(self) -> dict:
        d: dict = {"kind": self.kind}
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, Node):
                d[f.name] = v.to_dict()
            elif isinstance(v, list):
                d[f.name] = [x.to_dict() if isinstance(x, Node) else x for x in v]
            else:
                d[f.name] = v
        return d


# --------------------------------------------------------------- expressions
@dataclass
class Expr(Node):
    ty: Optional[str] = field(default=None, kw_only=True)  # set by semantic analysis


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class BoolLiteral(Expr):
    value: bool


@dataclass
class Identifier(Expr):
    name: str
