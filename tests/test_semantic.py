from aegisc.diagnostics import Severity
from aegisc.lexer import tokenize
from aegisc.parser import parse
from aegisc.semantic import analyze


def check(src):
    toks, ld = tokenize(src)
    prog, pd = parse(toks)
    assert not ld and not pd, [d.message for d in ld + pd]
    table, diags = analyze(prog)
    errors = [d.message for d in diags if d.severity is Severity.ERROR]
    warnings = [d.message for d in diags if d.severity is Severity.WARNING]
    return prog, table, errors, warnings


def errors_of(src):
    return check(src)[2]


def test_valid_program_has_no_errors_or_warnings():
    _, _, errs, warns = check("""
        int fib(untrusted int n) {
            if (n <= 1) { return n; }
            return fib(n - 1) + fib(n - 2);
        }
        int main() {
            untrusted int n = input_int();
            string s = "x" + input();
            for (int i = 0; i < 3; i++) { print(i, s, fib(n)); }
            return 0;
        }""")
    assert errs == [] and warns == []


def test_forward_call_and_mutual_recursion():
    errs = errors_of("""
        bool even(int n) { if (n == 0) { return true; } return odd(n - 1); }
        bool odd(int n) { if (n == 0) { return false; } return even(n - 1); }
        int main() { print(even(4)); return 0; }""")
    assert errs == []


def test_undeclared_and_out_of_scope():
    errs = errors_of("""
        int main() {
            { int inner = 1; print(inner); }
            print(inner);
            print(nope);
            return 0;
        }""")
    assert errs == ["use of undeclared identifier 'inner'", "use of undeclared identifier 'nope'"]


def test_redeclaration_vs_shadowing():
    errs = errors_of("""
        int main() {
            int x = 1; int x = 2;
            { int x = 3; print(x); }
            return x;
        }""")
    assert len(errs) == 1 and "'x' is already declared in this scope" in errs[0]


def test_parameter_cannot_be_redeclared_in_body():
    errs = errors_of("int f(int a) { int a = 2; return a; } int main() { return f(1); }")
    assert "'a' is already declared" in errs[0]


def test_type_errors_in_expressions():
    errs = errors_of("""
        int main() {
            int a = "hello";
            bool b = 1 + true;
            string s = "a" - "b";
            int c = -"x";
            bool d = !5;
            bool e = 1 == "1";
            bool f = 1 && 2;
            print(a, b, s, c, d, e, f);
            return 0;
        }""")
    assert errs == [
        "cannot initialise int variable 'a' with a value of type string",
        "operator '+' cannot be applied to int and bool",
        "operator '-' cannot be applied to string and string",
        "operator '-' needs an int operand, got string",
        "operator '!' needs a bool operand, got int",
        "cannot compare int with string using '=='",
        "operator '&&' needs bool operands, got int and int",
    ]


def test_conditions_must_be_bool():
    errs = errors_of("int main() { int n = 3; while (n) { n--; } if (n) { } return 0; }")
    assert errs == ["while condition must be bool, got int", "if condition must be bool, got int"]


def test_assignment_rules():
    errs = errors_of("""
        int main() {
            int x = 0; string s = "a"; bool b = true;
            x = "no";
            s += "ok";
            s += 1;
            b += 1;
            b++;
            return x;
        }""")
    assert errs == [
        "cannot assign string to 'x' of type int",
        "cannot append int to string 's'",
        "operator '+=' needs an int variable, got bool",
        "operator '++' needs an int variable, got bool",
    ]


def test_call_checks():
    errs = errors_of("""
        int add(int a, int b) { return a + b; }
        int main() {
            int x = 1;
            add(1);
            add(1, "two");
            x(3);
            missing();
            len(5);
            return add;
        }""")
    assert errs == [
        "'add' expects 2 argument(s), got 1",
        "argument 2 of 'add' should be int, got string",
        "'x' is an int variable, not a function",
        "call to undeclared function 'missing'",
        "argument 1 of 'len' should be string, got int",
        "'add' is a function, not a variable",
    ]


def test_return_checks():
    errs = errors_of("""
        void v() { return 1; }
        int a() { return; }
        int b() { return "s"; }
        int c(bool f) { if (f) { return 1; } }
        int d(bool f) { if (f) { return 1; } else { return 2; } }
        int e() { while (true) { return 1; } }
        int main() { return 0; }""")
    assert errs == [
        "void function 'v' cannot return a value",
        "'a' must return a value of type int",
        "'b' returns int, but this expression has type string",
        "function 'c' must return a value of type int on every path",
    ]


def test_void_variable_and_param():
    errs = errors_of("void f(void p) { } int main() { void x; return 0; }")
    assert errs == ["parameter 'p' cannot have type void", "variable 'x' cannot have type void"]


def test_function_redefinition_and_builtin_clash():
    errs = errors_of("int f() { return 1; } int f() { return 2; } int print() { return 0; } int main() { return 0; }")
    assert errs[0].startswith("function 'f' redefined (already declared at 1:1)")
    assert errs[1] == "function 'print' redefined (a built-in function)"


def test_literal_division_by_zero():
    assert errors_of("int main() { return 1 / 0; }") == ["division by zero"]


def test_errors_do_not_cascade():
    # One undeclared name should yield exactly one error, not a chain of type errors.
    assert errors_of("int main() { int y = nope + 1 * 2; return y; }") == ["use of undeclared identifier 'nope'"]


def test_warnings_unused_and_missing_main():
    _, _, errs, warns = check("int f() { int unused = 1; return 0; }")
    assert errs == []
    assert "variable 'unused' is declared but never used" in warns
    assert "program has no 'int main()' entry point" in warns


def test_types_are_annotated_on_ast():
    prog, _, _, _ = check('int main() { string s = "a" + "b"; bool b = 1 < 2; print(s, b); return 0; }')
    body = prog.decls[0].body.body
    assert body[0].init.ty == "string"
    assert body[1].init.ty == "bool"


def test_symbol_table_records_untrusted_and_scopes():
    _, table, _, _ = check("""
        int f(untrusted int n) { return n; }
        int main() { untrusted string q = input(); int k = f(len(q)); return k; }""")
    names = [s.name for s in table.scopes]
    assert names == ["global", "fn f", "fn main"]
    f_scope, main_scope = table.scopes[1], table.scopes[2]
    assert f_scope.symbols["n"].untrusted and f_scope.symbols["n"].kind == "parameter"
    assert main_scope.symbols["q"].untrusted and not main_scope.symbols["k"].untrusted
    assert table.global_scope.symbols["input"].untrusted  # built-in untrusted source
    assert table.global_scope.symbols["f"].param_untrusted == [True]
