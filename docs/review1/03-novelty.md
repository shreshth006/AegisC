# 3. Novelty

AegisC makes two contributions. The **educational** one is a compiler that shows every phase of its work and can explain it. The **research** one is AegisBudget, a compiler pass that treats computation caused by untrusted input as a conserved resource. This document is careful about which parts are new and which are reused.

## 3.1 What is *not* claimed as new

Being explicit about this is what makes the actual claim believable in Q&A.

| Idea | Why it isn't novel | Prior art |
|---|---|---|
| Finding loops and recursion that depend on user input | Taint analysis combined with loop and call-graph analysis is standard | SlowFuzz, static taint tools in general |
| A compiler inserting counters or gas checks | Done by bytecode and Wasm metering | J-RAF2; Wasm gas metering |
| Static resource-bound analysis | Well developed | Crary & Weirich; RAML |
| Charging resources to a request, packet or session | Done in OS and run-time work | Resource containers; ROKI |
| Linear types that stop duplication | Long-established | Linear/affine types; Rust; Nomos (for assets) |
| Showing compiler output in a browser | Exists for final output | Compiler Explorer |

## 3.2 Core novel idea: provenance-carried budgets that can't be duplicated

> **AegisBudget.** The compiler identifies data that comes from untrusted sources. For each independent input lineage it creates a *budget capability*. It then transforms the program so that every computation derived from that input (through assignments, copies, function calls, recursion and `spawn`) draws on the **same** capability. Copying the data never creates a new allowance. Guards are inserted only at points that amplify work, such as loop back-edges, recursive calls and task creation.

The invariant, for an input *i* with lineage *Lᵢ* and budget *Bᵢ*:

$$\sum_{c \,\in\, \text{descendants}(L_i)} \mathrm{Work}(c) \;\le\; B_i$$

This holds no matter how many copies, calls or tasks are derived from *i*.

The new part is the **combination** of four things. None of the prior works in the survey has all of them:

1. **Provenance as ownership.** Taint analysis is usually used to find bugs. Here it decides *who pays* for a computation.
2. **Linear capability over computation.** The budget is affine: it can be shared (all holders draw on one counter) or explicitly split (500 + 500 = 1000), but never cloned. Prior linear-type work protects assets, not permission to compute.
3. **Compiler-synthesised enforcement.** The pass adds hidden budget parameters to functions that receive tainted arguments and threads the capability through calls automatically. The programmer writes nothing.
4. **Fan-out-aware.** Under `spawn`, *N* tasks share one allowance rather than getting *N* allowances. Per-thread or per-process quotas can't express this.

### How it compares with the closest prior art

| | Wasm gas metering | Resource containers / ROKI | **AegisBudget** |
|---|---|---|---|
| Who is charged | the whole execution | the request, packet or session (at run time) | the **input lineage** (derived at compile time) |
| Effect of copying an input | not applicable | not tracked | copies share one budget |
| Effect of fanning out to N tasks | one global counter | depends on manual binding | N tasks, one budget, by construction |
| Where checks go | every block or branch | kernel and application hooks | **only** at amplification points that touch tainted data |
| Effect on untainted code | metered | accounted | **untouched**, so no overhead on trusted paths |
