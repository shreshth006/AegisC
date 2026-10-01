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
