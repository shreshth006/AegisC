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

## Module responsibilities

| Module | Responsibility |
|---|---|
| `tokens.py` | Token types, keyword table, operator maps, token categories for colouring |
| `lexer.py` | Hand-written scanner: comments, escapes, longest-match operators, 32-bit literal check, error recovery |
| `ast.py` | Dataclass AST; `to_dict()` for JSON, `dump()` for the terminal |
| `parser.py` | Recursive descent, one function per EBNF rule; precedence climbing; panic-mode recovery |
| `symbols.py` | Scope tree (global → function → block/for); keeps every scope for display |
| `semantic.py` | Two-pass analysis: signatures, then bodies; type inference written to `Expr.ty`; return-path check; `untrusted` recorded as a provenance seed |
| `pipeline.py` | Runs the stages; skips semantic analysis when the tree is broken |
| `cli.py` | Terminal rendering and `--json` export |

## Planned: PROBE (AegisBudget) pass

1. **Source identification.** Seeds are `input()`, `input_int()` and anything declared `untrusted`.
2. **Provenance propagation.** A forward data-flow analysis over the CFG, made interprocedural through function summaries. Each value is tagged with the set of input lineages it derives from.
3. **Amplification detection.** Finds loop back-edges whose condition depends on tainted data, recursive call cycles reachable with tainted arguments, and `spawn` sites.
4. **Budget creation.** One `BudgetCapability` per lineage, with size `base + α·size(input)` (the policy is configurable).
5. **Capability threading.** Adds a hidden budget parameter to every function that receives a tainted argument. Copies and `spawn`s *share* the capability; an explicit `split` partitions it.
6. **Guard insertion.** Inserts `consume(B, cost)` only at amplification points. When the budget is exhausted, it raises a controlled `RESOURCE_BUDGET_EXCEEDED` for that lineage only.
