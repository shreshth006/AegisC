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
