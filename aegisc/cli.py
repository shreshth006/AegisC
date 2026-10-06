"""Command-line front end: `python -m aegisc FILE [--stage ...] [--json]`."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .ast import dump
from .pipeline import CompilationResult, compile_source

CHOICES = ("all", "tokens", "ast", "symbols", "diagnostics")


def _rule(title: str) -> str:
    return f"\n== {title} " + "=" * max(4, 60 - len(title))


def render_tokens(res: CompilationResult) -> str:
    rows = [f"{'LINE:COL':<9} {'TYPE':<13} {'CATEGORY':<11} LEXEME"]
    for t in res.tokens or []:
        d = t.to_dict()
        rows.append(f"{f'{t.line}:{t.col}':<9} {d['type']:<13} {d['category']:<11} {t.lexeme}")
    return "\n".join(rows)


def render_symbols(res: CompilationResult) -> str:
    table = res.symbols
    if table is None:
        return "(skipped: earlier stage had errors)"
    out = []
    for scope in table.scopes:
        indent = "  " * scope.level
        out.append(f"{indent}[{scope.name}]")
        for s in scope.symbols.values():
            if s.kind == "builtin":
                continue
            flags = " untrusted" if s.untrusted else ""
            sig = f"({', '.join(s.params)})" if s.params is not None and s.kind == "function" else ""
            out.append(f"{indent}  {s.name:<12} {s.kind:<10} {s.type}{sig}{flags}  @{s.line}:{s.col}")
    return "\n".join(out)


def render_diagnostics(res: CompilationResult) -> str:
    diags = res.diagnostics
    if not diags:
        return "no diagnostics"
    return "\n\n".join(d.format(res.source) for d in diags)


def render(res: CompilationResult, stage: str) -> str:
    parts = []
    if stage in ("all", "tokens"):
        parts += [_rule("Lexical analysis: tokens"), render_tokens(res)]
    if stage in ("all", "ast"):
        parts += [_rule("Syntax analysis: AST"),
                  dump(res.ast) if res.ast is not None else "(no AST)"]
    if stage in ("all", "symbols"):
        parts += [_rule("Semantic analysis: symbol table"), render_symbols(res)]
    if stage in ("all", "diagnostics"):
        parts += [_rule("Diagnostics"), render_diagnostics(res)]
    if stage == "all":
        summary = ", ".join(f"{s.name}={s.status}" for s in res.stages.values())
        parts += [_rule("Summary"), summary]
    return "\n".join(parts).lstrip("\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aegisc", description="AegisC: a compiler that shows its work.")
    ap.add_argument("file", help="AegisC source file ('-' for stdin)")
    ap.add_argument("--stage", choices=CHOICES, default="all", help="which stage output to print")
    ap.add_argument("--json", action="store_true", help="emit every stage as JSON (for the visualizer)")
    ap.add_argument("--version", action="version", version=f"aegisc {__version__}")
    args = ap.parse_args(argv)

    try:
        source = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    except OSError as exc:
        print(f"aegisc: cannot read {args.file}: {exc.strerror}", file=sys.stderr)
        return 2

    res = compile_source(source)
    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
    else:
        print(render(res, args.stage))
    return 0 if res.ok else 1
