# AegisC

A small, teachable compiler for a C-like language that **shows every compilation stage**, explains each one with an **LLM tutor grounded in course notes (RAG)**, and adds a novel security pass, **AegisBudget**. AegisBudget gives each piece of untrusted input a computation budget that cannot be duplicated, and every computation derived from that input draws from the same budget.

```
Source ─► Lexer ─► Parser/AST ─► Semantic ─► TAC ─► Optimizer ─► PROBE (AegisBudget) ─► C output
            │          │            │          │        │              │
            └──────────┴────────────┴──────────┴────────┴──────────────┴──► "Why?" → LLM tutor (RAG over course PDFs)
```

## Status (Review 1)

| Stage | Status |
|---|---|
| Lexical analysis (tokens, positions, error recovery) | ✅ done |
| Syntax analysis (recursive-descent parser, AST, panic-mode recovery) | ✅ done |
| Symbol table (nested scopes) | ✅ done |
| Semantic analysis (types, scopes, calls, returns, `untrusted` qualifier) | ✅ done |
| CLI that dumps every stage (pretty or JSON) | ✅ done |
| Three-address code (TAC) generation | ⏳ next |
| Optimizer (constant folding/propagation, dead code) | ⏳ planned |
| PROBE: provenance analysis + budget instrumentation | ⏳ planned |
| Web visualizer + LLM tutor with RAG | ⏳ planned |

## Quick start

```bash
python -m aegisc examples/hello.aeg              # all stages, pretty output
python -m aegisc examples/hello.aeg --stage tokens
python -m aegisc examples/errors.aeg             # see diagnostics from each stage
python -m aegisc examples/fib_untrusted.aeg --json > out.json
python -m pytest
```

Requires Python 3.10+. No third-party dependencies for the compiler core.
