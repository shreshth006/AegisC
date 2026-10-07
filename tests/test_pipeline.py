import json
import pathlib

import pytest

from aegisc.cli import main
from aegisc.pipeline import compile_source

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"


def test_clean_program_runs_all_stages():
    res = compile_source("int main() { return 0; }")
    assert res.ok
    assert [s.status for s in res.stages.values()] == ["ok", "ok", "ok"]


def test_syntax_error_skips_semantic_stage():
    res = compile_source("int main() { return 0 }")
    assert not res.ok
    assert res.stages["parser"].status == "error"
    assert res.stages["semantic"].status == "skipped" and res.symbols is None


def test_lexer_errors_still_produce_tokens_and_parse_attempt():
    res = compile_source("int main() { int x = 1 @ 2; return x; }")
    assert res.stages["lexer"].status == "error"
    assert res.tokens and res.ast is not None
    assert res.stages["semantic"].status == "skipped"


def test_warnings_do_not_fail_compilation():
    res = compile_source("int helper() { return 1; }")   # no main -> warning only
    assert res.ok and res.diagnostics


def test_json_shape_is_stable():
    d = compile_source("int main() { untrusted int n = input_int(); return n; }").to_dict()
    json.dumps(d)
    assert [s["stage"] for s in d["stages"]] == ["lexer", "parser", "semantic"]
    lexer, parser, semantic = d["stages"]
    assert lexer["output"][0] == {"type": "INT", "category": "keyword", "lexeme": "int",
                                  "value": None, "line": 1, "col": 1}
    assert parser["output"]["kind"] == "Program"
    scopes = semantic["output"]["scopes"]
    main_scope = next(s for s in scopes if s["name"] == "fn main")
    assert main_scope["symbols"][0]["untrusted"] is True


@pytest.mark.parametrize("name,ok", [
    ("hello.aeg", True), ("fib_untrusted.aeg", True), ("fanout.aeg", True),
    ("errors.aeg", False), ("syntax_errors.aeg", False),
])
def test_examples_compile_as_expected(name, ok):
    res = compile_source((EXAMPLES / name).read_text())
    assert res.ok is ok
