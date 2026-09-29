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

## 2. Grammar (EBNF)

```ebnf
program        = { global_decl | func_decl } EOF ;
global_decl    = var_decl ;
func_decl      = type IDENT "(" [ params ] ")" block ;
params         = param { "," param } ;
param          = [ "untrusted" ] type IDENT ;
type           = "int" | "string" | "bool" | "void" ;

block          = "{" { statement } "}" ;
statement      = var_decl
               | if_stmt | while_stmt | for_stmt
               | return_stmt | spawn_stmt
               | block
               | expr_stmt ;
var_decl       = [ "untrusted" ] type IDENT [ "=" expression ] ";" ;
if_stmt        = "if" "(" expression ")" statement [ "else" statement ] ;
while_stmt     = "while" "(" expression ")" statement ;
for_stmt       = "for" "(" ( var_decl | expr_stmt | ";" )
                       [ expression ] ";" [ expression ] ")" statement ;
return_stmt    = "return" [ expression ] ";" ;
spawn_stmt     = "spawn" call ";" ;
expr_stmt      = expression ";" ;

expression     = assignment ;
assignment     = IDENT ( "=" | "+=" | "-=" | "*=" | "/=" ) assignment
               | logic_or ;
logic_or       = logic_and { "||" logic_and } ;
logic_and      = equality { "&&" equality } ;
equality       = comparison { ( "==" | "!=" ) comparison } ;
comparison     = term { ( "<" | "<=" | ">" | ">=" ) term } ;
term           = factor { ( "+" | "-" ) factor } ;
factor         = unary { ( "*" | "/" | "%" ) unary } ;
unary          = ( "!" | "-" ) unary | ( "++" | "--" ) IDENT | postfix ;
postfix        = primary [ "++" | "--" ] ;
primary        = INT | STRING | "true" | "false"
               | call | IDENT | "(" expression ")" ;
call           = IDENT "(" [ expression { "," expression } ] ")" ;
```

The precedence climbs from `assignment` (lowest, right-associative) to `primary` (highest). Every binary level is left-associative.

## 3. Types and semantics

- Types: `int` (32-bit signed), `string`, `bool`, `void` (return type only).
- Conditions in `if`, `while` and `for` must be `bool`. There's no implicit int→bool conversion, which keeps type errors easy to explain.
- Arithmetic (`+ - * / %`) takes `int` operands. `+` on two `string`s concatenates them.
- Comparisons (`< <= > >=`) take `int` operands and produce `bool`. `==` and `!=` need both operands to have the same type.
- `&&`, `||` and `!` take `bool` operands.
- Variables must be declared before use. Redeclaring a name in the same scope is an error, but shadowing in an inner scope is allowed.
- Functions may be called before their definition, which allows mutual recursion. A non-`void` function must return a value on every path.
- `int main()` is the entry point. If it's missing, the compiler issues a warning.
