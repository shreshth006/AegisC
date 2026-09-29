# AegisC

A small, teachable compiler for a C-like language that **shows every compilation stage**, explains each one with an **LLM tutor grounded in course notes (RAG)**, and adds a novel security pass, **AegisBudget**. AegisBudget gives each piece of untrusted input a computation budget that cannot be duplicated, and every computation derived from that input draws from the same budget.

```
Source ─► Lexer ─► Parser/AST ─► Semantic ─► TAC ─► Optimizer ─► PROBE (AegisBudget) ─► C output
            │          │            │          │        │              │
            └──────────┴────────────┴──────────┴────────┴──────────────┴──► "Why?" → LLM tutor (RAG over course PDFs)
```
