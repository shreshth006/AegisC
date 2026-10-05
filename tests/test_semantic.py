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
