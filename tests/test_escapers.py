from dhtmlparser3.quoter import escape


def test_escape():
    assert escape('"') == '&quot;'
    assert escape('printf("hello world");') == r"printf(&quot;hello world&quot;);"
