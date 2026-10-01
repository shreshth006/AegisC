from aegisc.lexer import tokenize
from aegisc.tokens import TokenType as T


def types(src):
    toks, diags = tokenize(src)
    assert not diags, diags
    return [t.type for t in toks]


def test_keywords_identifiers_and_eof():
    assert types("int x untrusted spawn foo_1") == [T.INT, T.IDENT, T.UNTRUSTED, T.SPAWN, T.IDENT, T.EOF]


def test_longest_match_operators():
    assert types("a<=b==c&&d||!e++ --f += 1") == [
        T.IDENT, T.LE, T.IDENT, T.EQ, T.IDENT, T.AND, T.IDENT, T.OR, T.NOT, T.IDENT,
        T.INC, T.DEC, T.IDENT, T.PLUS_ASSIGN, T.INT_LIT, T.EOF,
    ]


def test_literal_values():
    toks, _ = tokenize('42 "hi\\n\\"x\\"" true false')
    assert toks[0].value == 42
    assert toks[1].value == 'hi\n"x"'
    assert toks[2].value is True and toks[3].value is False


def test_positions_are_one_based_and_track_newlines():
    toks, _ = tokenize("int\n  x;")
    assert (toks[0].line, toks[0].col) == (1, 1)
    assert (toks[1].line, toks[1].col) == (2, 3)
    assert (toks[2].line, toks[2].col) == (2, 4)


def test_comments_are_skipped():
    assert types("a // line\n/* block\n comment */ b") == [T.IDENT, T.IDENT, T.EOF]


def test_unterminated_block_comment_reported():
    _, diags = tokenize("a /* never closed")
    assert len(diags) == 1 and "unterminated block comment" in diags[0].message


def test_unterminated_string_reported_with_position():
    _, diags = tokenize('x = "abc\ny;')
    assert diags[0].message == "unterminated string literal"
    assert (diags[0].line, diags[0].col) == (1, 5)


def test_bad_escape_reported():
    _, diags = tokenize('"a\\qb"')
    assert "unknown escape" in diags[0].message
