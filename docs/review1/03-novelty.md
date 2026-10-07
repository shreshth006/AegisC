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
