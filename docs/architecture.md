# Architecture

```
                         ┌──────────────────────────── aegisc (Python package) ─────────────────────────────┐
 source ──► lexer.py ──► parser.py ──► semantic.py ──► tac.py ──► optimizer.py ──► probe/ ──► codegen_c.py ──► .c
              │             │               │             │            │              │
           tokens          AST        symbol table      TAC     opt. event log   PROBE report
              └─────────────┴───────────────┴─────────────┴────────────┴──────────────┘
                                                │
                                          pipeline.py  ──►  CompilationResult (JSON)
                                                │
                    ┌───────────────────────────┼─────────────────────────────┐
                    ▼                           ▼                             ▼
                 cli.py                  web visualizer                 tutor service
           (pretty / --json)          (stage panels, linked          (RAG over course notes,
                                       by source position)            explains structured events)
```

Implemented for Review 1: `lexer`, `parser`, `ast`, `symbols`, `semantic`, `pipeline`, `cli`. Everything to the right of `semantic` is planned.

## Design principles

1. **Every stage is data.** Each stage returns a serialisable result plus a list of `Diagnostic`s. `pipeline.compile_source()` collects them into one `CompilationResult`, which is the only interface the CLI, the visualizer and the tutor depend on.
2. **Errors are reported, not raised.** The lexer skips bad characters. The parser uses panic-mode recovery at the statement and top level. Semantic analysis uses an `<error>` type so a single mistake produces a single message. A learner sees *all* the independent mistakes in one run.
3. **Positions everywhere.** Every token, AST node, symbol and diagnostic carries `line:col`, so the UI can link a TAC instruction back to its AST node and source text.
4. **Deterministic compiler, explanatory LLM.** The LLM never changes compilation. It only explains structured events the compiler has already recorded.
5. **No third-party dependencies in the core.** The compiler is plain Python 3.10+, so anyone on the team can run it and the examiners can audit it.
