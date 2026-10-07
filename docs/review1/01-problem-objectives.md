# 1. Problem Identification and Objectives

## 1.1 Context

Compiler Design is usually taught as a chain of phases: lexical analysis, syntax analysis, semantic analysis, intermediate code, optimisation and code generation. Each phase is easy to state and hard to *see*. Students meet a token stream, a parse tree or a block of three-address code in a textbook figure. They rarely watch the phases run on their own programs, and they almost never get an answer to the question they actually have: "*why* did the compiler do that?"

Separately, real compilers enforce almost nothing about how much work a program may do. A small, attacker-chosen input can drive a loop, a recursion or a fan-out of tasks into millions of operations. This is the algorithmic-complexity denial-of-service class catalogued as CWE-407 (*Inefficient Algorithmic Complexity*). The usual defences sit outside the program and know nothing about which input caused which work: request timeouts, CPU quotas, container limits, rate limiters and hand-written counters.

## 1.2 Problem statement

We address two linked problems:

1. **Pedagogical opacity.** There is no single tool in which a student can type a program, step through every compilation phase on that program (tokens → AST → symbol table → diagnostics → TAC → optimised TAC), and ask for an explanation of any step grounded in their own course material.

2. **Input-amplification exhaustion.** Existing compile-time and run-time mechanisms do not tie the computation a program performs to the untrusted input that caused it. As a result, copying an input or fanning it out into several calls or tasks multiplies the work an attacker can trigger, and the compiler, which has the full data-flow and control-flow picture, takes no part in preventing this.
