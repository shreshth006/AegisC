# 2. Literature Survey

The survey covers four threads that AegisC draws on: (A) algorithmic-complexity denial of service, (B) resource accounting and enforcement, (C) resource-aware and linear type systems, and (D) LLM/RAG tutoring for programming education. Each entry gives what the work does and how AegisC relates to it.

## A. Algorithmic-complexity denial of service

| # | Work | Contribution | Gap with respect to AegisC |
|---|---|---|---|
| A1 | S. A. Crosby, D. S. Wallach, *Denial of Service via Algorithmic Complexity Attacks*, USENIX Security 2003. | Showed that low-bandwidth inputs can force worst-case behaviour in hash tables and trees (Perl, Squid, Bro). Mitigation: universal hashing. | Fixes specific data structures. It provides no general mechanism tying work to the input that caused it. |
| A2 | MITRE, **CWE-407** *Inefficient Algorithmic Complexity*. | Classifies attacker-triggerable worst-case complexity as a software weakness. Consequences: CPU and memory exhaustion. | A taxonomy, not a defence. It motivates the problem. |
| A3 | T. Petsios, J. Zhao, A. D. Keromytis, S. Jana, *SlowFuzz: Automated Domain-Independent Detection of Algorithmic Complexity Vulnerabilities*, ACM CCS 2017. | Resource-guided evolutionary fuzzing that finds inputs maximising resource use (bzip2, PCRE). | *Detects* worst-case inputs in testing. It doesn't *enforce* limits in deployed code. |

## B. Resource accounting and enforcement

| # | Work | Contribution | Gap with respect to AegisC |
|---|---|---|---|
| B1 | G. Banga, P. Druschel, J. C. Mogul, *Resource Containers: A New Facility for Resource Management in Server Systems*, OSDI 1999. | Separates the "resource principal" from the process or thread, so that an activity such as a request can be charged across kernel and application. | An OS abstraction. The application has to bind work to containers by hand, and the compiler plays no part. |
| B2 | W. Binder, J. Hulaas et al., **J-RAF2**, *A Portable CPU Management Framework for Java* (c. 2004–05). | Bytecode rewriting inserts instruction counters, giving portable CPU accounting per thread. | Accounts per thread or component, not per input lineage. Copying or fanning out data doesn't share an allowance. |
| B3 | WebAssembly / blockchain **gas metering**, e.g. the `wasm-instrument` crate's `gas_metering` module. | Statically injects gas charges at the start of each block and on branch or loop edges. Execution stops when gas runs out. | One global budget per execution. It doesn't track *which* input caused the work. **This is the closest prior art for guard insertion.** |
| B4 | *Mitigating Low-volume DoS Attacks with Data-driven Resource Accounting* (**ROKI**), arXiv:2205.00056, 2022. | Attributes kernel and application resource use to individual packets or sessions, and reclaims resources from malicious ones when exhaustion occurs. | Attribution happens at run time in the kernel and application layers. Nothing is synthesised by a compiler from program data flow, and there is no duplication-proof budget. |
