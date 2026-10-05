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
