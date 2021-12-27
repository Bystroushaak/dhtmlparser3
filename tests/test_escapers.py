from dhtmlparser3.quoter import escape
from dhtmlparser3.quoter import unescape


def test_unescape():
    assert unescape(r"""\' \\ \" \n""") == r"""\' \\ " \n"""
    assert unescape(r"""\' \\ \" \n""", "'") == r"""' \\ \" \n"""
    assert unescape(r"""\' \\" \n""") == r"""\' \\" \n"""
    assert unescape(r"""\' \\" \n""") == r"""\' \\" \n"""
    assert unescape(r"printf(\"hello \t world\");") == r'printf("hello \t world");'


def test_escape():
    assert escape(r"'", "'") == r"""\'"""
    assert escape(r"\\", "'") == "\\\\"
    assert escape(r"""printf("hello world");""") == r"""printf(\"hello world\");"""
