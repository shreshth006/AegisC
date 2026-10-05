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
