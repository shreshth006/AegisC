from aegisc import ast as A
from aegisc.lexer import tokenize
from aegisc.parser import parse


def parse_ok(src):
    toks, ld = tokenize(src)
    assert not ld
    prog, pd = parse(toks)
    assert not pd, [d.message for d in pd]
    return prog


def parse_errs(src):
    toks, _ = tokenize(src)
    _, pd = parse(toks)
    return pd


def first_expr(src):
    """Parse `src` as the body of `void f() { <src>; }` and return the expression."""
    prog = parse_ok(f"void f() {{ {src}; }}")
    return prog.decls[0].body.body[0].expr


def test_function_with_untrusted_param():
    prog = parse_ok("int f(untrusted int n, string s) { return n; }")
    fn = prog.decls[0]
    assert isinstance(fn, A.FuncDecl) and fn.name == "f" and fn.ret_type == "int"
    assert [(p.name, p.type, p.untrusted) for p in fn.params] == [("n", "int", True), ("s", "string", False)]


def test_global_and_untrusted_declarations():
    prog = parse_ok("int g = 1; untrusted string q;")
    assert isinstance(prog.decls[0], A.VarDecl) and prog.decls[0].init.value == 1
    assert prog.decls[1].untrusted and prog.decls[1].init is None


def test_precedence_mul_over_add():
    e = first_expr("1 + 2 * 3")
    assert isinstance(e, A.Binary) and e.op == "+"
    assert isinstance(e.right, A.Binary) and e.right.op == "*"


def test_left_associativity():
    e = first_expr("10 - 4 - 3")
    assert e.op == "-" and isinstance(e.left, A.Binary) and e.left.op == "-"


def test_logical_precedence_and_parentheses():
    e = first_expr("a || b && c")
    assert e.op == "||" and e.right.op == "&&"
    e = first_expr("(1 + 2) * 3")
    assert e.op == "*" and e.left.op == "+"


def test_assignment_is_right_associative():
    e = first_expr("a = b += 3")
    assert isinstance(e, A.Assign) and e.op == "="
    assert isinstance(e.value, A.Assign) and e.value.op == "+="


def test_unary_incdec_and_calls():
    e = first_expr("-f(1, x) + !b")
    assert isinstance(e.left, A.Unary) and isinstance(e.left.operand, A.Call)
    assert len(e.left.operand.args) == 2
    assert isinstance(first_expr("i++"), A.IncDec) and not first_expr("i++").prefix
    assert first_expr("--i").prefix
