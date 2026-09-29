# AegisC Language Specification (v0.1)

AegisC is a small, statically typed, C-like language. It's large enough to show every classical compiler phase and to express the resource-amplification patterns (loops, recursion, fan-out) that AegisBudget protects against. It's small enough for a student team to implement completely.

## 1. Lexical structure

| Category | Definition |
|---|---|
| Whitespace | space, tab, `\r`, `\n` (ignored, but they advance line/column) |
| Line comment | `//` up to end of line |
| Block comment | `/* ... */` (no nesting; an unterminated comment is a lexical error) |
| Identifier | `[A-Za-z_][A-Za-z0-9_]*`, unless it is a keyword |
| Integer literal | `[0-9]+`; must fit in a signed 32-bit integer |
| String literal | `"..."` with escapes `\n \t \" \\`; cannot span lines |
| Keywords | `int string bool void if else while for return true false untrusted spawn` |
| Operators | `+ - * / % = += -= *= /= == != < <= > >= && \|\| ! ++ --` |
| Delimiters | `( ) { } , ;` |
