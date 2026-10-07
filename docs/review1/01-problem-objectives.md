# 1. Problem Identification and Objectives

## 1.1 Context

Compiler Design is usually taught as a chain of phases: lexical analysis, syntax analysis, semantic analysis, intermediate code, optimisation and code generation. Each phase is easy to state and hard to *see*. Students meet a token stream, a parse tree or a block of three-address code in a textbook figure. They rarely watch the phases run on their own programs, and they almost never get an answer to the question they actually have: "*why* did the compiler do that?"

Separately, real compilers enforce almost nothing about how much work a program may do. A small, attacker-chosen input can drive a loop, a recursion or a fan-out of tasks into millions of operations. This is the algorithmic-complexity denial-of-service class catalogued as CWE-407 (*Inefficient Algorithmic Complexity*). The usual defences sit outside the program and know nothing about which input caused which work: request timeouts, CPU quotas, container limits, rate limiters and hand-written counters.

## 1.2 Problem statement

We address two linked problems:

1. **Pedagogical opacity.** There is no single tool in which a student can type a program, step through every compilation phase on that program (tokens → AST → symbol table → diagnostics → TAC → optimised TAC), and ask for an explanation of any step grounded in their own course material.

2. **Input-amplification exhaustion.** Existing compile-time and run-time mechanisms do not tie the computation a program performs to the untrusted input that caused it. As a result, copying an input or fanning it out into several calls or tasks multiplies the work an attacker can trigger, and the compiler, which has the full data-flow and control-flow picture, takes no part in preventing this.

## 1.3 Objectives

| # | Objective | Measurable outcome |
|---|---|---|
| O1 | Design **AegisC**, a small C-like language that's expressive enough to show every compiler phase and the resource-amplification patterns (loops, recursion, `spawn` fan-out), with an `untrusted` qualifier. | Formal EBNF grammar and typing rules ([language.md](../language.md)) |
| O2 | Implement a complete, error-recovering **compiler front end**: lexer, recursive-descent parser, AST, scoped symbol table, and semantic and type analysis. | Every stage produces a machine-readable output and position-accurate diagnostics; covered by automated tests |
| O3 | Implement the **middle end**: three-address code (TAC) generation, a control-flow graph, and classical optimisations (constant folding and propagation, dead-code elimination), with a before/after record of every transformation. | Each optimisation is logged as *(rule, before, after, location)* so it can be visualised and explained |
| O4 | Implement **PROBE**, the AegisBudget pass: provenance analysis from untrusted sources, detection of amplification points, creation of a budget capability per input lineage, and propagation of a **budget that cannot be duplicated** through calls, copies and `spawn`, with guards inserted only at amplification points. | Instrumented output in which the total work of every descendant of an input is ≤ that input's budget; an attack demo where the guard fires and benign inputs are unaffected |
| O5 | Build an **interactive visualizer** that shows each phase on the user's own program and links source locations across phases. | Web UI: tokens, AST tree, symbol table, diagnostics, TAC, optimised TAC, PROBE report |
| O6 | Integrate an **LLM tutor with retrieval-augmented generation (RAG)** over the course's Compiler Design notes, so that "Why?" on any token, node, diagnostic or optimisation returns an explanation grounded in that material. | Explanations cite the retrieved note passages; evaluated against a set of questions |
| O7 | **Evaluate** the project: correctness (test suite), PROBE overhead (instrumented vs. uninstrumented operation counts), attack mitigation (time or operations to exhaustion), and tutor answer quality. | Results tables in the final report |

## 1.4 Scope boundaries

- AegisC is deliberately small: `int`, `string`, `bool`, functions, recursion, `if`/`while`/`for`, `spawn`, plus `input`, `input_int`, `len` and `print`. It has no pointers, arrays or structs in v1.
- `spawn` runs synchronously in v1. Concurrent execution and asynchronous budget propagation are research extensions.
- The back end emits C, not machine code.
- The LLM explains what the compiler did. It never decides what the compiler does. All analyses and transformations are deterministic.
