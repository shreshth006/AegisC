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

## C. Resource-aware and linear type systems

| # | Work | Contribution | Gap with respect to AegisC |
|---|---|---|---|
| C1 | K. Crary, S. Weirich, *Resource Bound Certification*, POPL 2000. | A decidable type system that certifies bounds on resource consumption such as running time. | Static certification. Programs that can't be proved bounded are rejected rather than instrumented, and bounds are not tied to input provenance. |
| C2 | J. Hoffmann, K. Aehlig, M. Hofmann, *Multivariate Amortized Resource Analysis*, POPL 2011 (**RAML**). | Automatically derives polynomial resource bounds as functions of input sizes. | *Estimates* bounds and doesn't enforce them at run time. It could later be used to set an initial budget. |
| C3 | A. Das, S. Balzer, J. Hoffmann, F. Pfenning, I. Santurkar, *Resource-Aware Session Types for Digital Contracts* (**Nomos**), IEEE CSF 2021 (arXiv:1902.06056). | Linear types stop assets from being duplicated or discarded. Amortised analysis bounds gas. | Linearity protects *assets* (money). AegisC applies it to the *permission to compute* that is derived from untrusted input. |
| C4 | Linear and affine types in general (Wadler's linear types; Rust's ownership and move semantics). | Values that can't be implicitly copied. | The mechanism AegisC borrows for its budget capability. |

## D. Compiler education and LLM tutors

| # | Work | Contribution | Gap with respect to AegisC |
|---|---|---|---|
| D1 | A. V. Aho, M. S. Lam, R. Sethi, J. D. Ullman, *Compilers: Principles, Techniques, and Tools* (2nd ed.). | Standard reference for the phase structure, TAC and data-flow analysis that AegisC implements. | A textbook. It isn't interactive. |
| D2 | Compiler Explorer (godbolt.org). | Shows source alongside generated assembly for real compilers. | Shows only the final output. The front-end and middle-end phases aren't visible and nothing is explained. |
| D3 | P. Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020 (arXiv:2005.11401). | Grounds generation in retrieved documents. | The technique AegisC's tutor uses to ground answers in course notes. |
| D4 | Recent studies of LLM course assistants in CS courses, e.g. arXiv:2509.08862 (student interaction with LLM course assistants) and TAMIGO, arXiv:2407.16805 (LLM-assisted viva and code assessment). | Evidence that LLM assistants are used, and are useful, in CS teaching. | General-purpose assistants. They aren't wired into a compiler's actual internal state. |
