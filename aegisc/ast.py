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


@dataclass
class Binary(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Unary(Expr):
    op: str            # "-" or "!"
    operand: Expr


@dataclass
class IncDec(Expr):
    op: str            # "++" or "--"
    target: Identifier
    prefix: bool


@dataclass
class Assign(Expr):
    op: str            # "=", "+=", "-=", "*=", "/="
    target: Identifier
    value: Expr


@dataclass
class Call(Expr):
    callee: str
    args: list[Expr]


# ---------------------------------------------------------------- statements
@dataclass
class Stmt(Node):
    pass


@dataclass
class VarDecl(Stmt):
    type: str
    name: str
    init: Optional[Expr]
    untrusted: bool = False


@dataclass
class Block(Stmt):
    body: list[Stmt]


@dataclass
class If(Stmt):
    cond: Expr
    then: Stmt
    else_: Optional[Stmt]


@dataclass
class While(Stmt):
    cond: Expr
    body: Stmt


@dataclass
class For(Stmt):
    init: Optional[Stmt]       # VarDecl or ExprStmt
    cond: Optional[Expr]
    update: Optional[Expr]
    body: Stmt


@dataclass
class Return(Stmt):
    value: Optional[Expr]


@dataclass
class Spawn(Stmt):
    call: Call


@dataclass
class ExprStmt(Stmt):
    expr: Expr


# -------------------------------------------------------------- declarations
@dataclass
class Param(Node):
    type: str
    name: str
    untrusted: bool = False


@dataclass
class FuncDecl(Node):
    ret_type: str
    name: str
    params: list[Param]
    body: Block


@dataclass
class Program(Node):
    decls: list[Node]          # FuncDecl | VarDecl


def dump(node: Node, indent: str = "") -> str:
    """Readable indented tree, used by the CLI."""
    attrs = []
    for f in fields(node):
        v = getattr(node, f.name)
        if f.name in ("line", "col") or isinstance(v, (Node, list)) or v is None:
            continue
        if f.name == "untrusted" and not v:
            continue
        attrs.append(f"{f.name}={v!r}")
    head = f"{indent}{node.kind}" + (f"({', '.join(attrs)})" if attrs else "") + f"  @{node.line}:{node.col}"
    lines = [head]
    for f in fields(node):
        v = getattr(node, f.name)
        if isinstance(v, Node):
            lines.append(f"{indent}  .{f.name}:")
            lines.append(dump(v, indent + "    "))
        elif isinstance(v, list) and v and isinstance(v[0], Node):
            lines.append(f"{indent}  .{f.name}:")
            lines.extend(dump(x, indent + "    ") for x in v)
    return "\n".join(lines)
