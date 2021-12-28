import pytest

import dhtmlparser3
from dhtmlparser3.tags.comment import Comment


def test_parse_simple_string():
    dom = dhtmlparser3.parse("""<html><tag PARAM="true"></html>""")

    assert dom.name == "html"
    assert dom.content
    assert len(dom.content) == 1

    assert dom.content[0].name == "tag"
    assert "PARAM" in dom.content[0].p
    assert dom.content[0].p["PARAM"] == "true"
    assert dom.content[0].p["param"] == "true"


def test_parse_simple_string_cip():
    dom = dhtmlparser3.parse(
        """<html><tag PARAM="true"></html>""",
        case_insensitive_parameters=False
    )

    assert dom.name == "html"
    assert dom.content
    assert len(dom.content) == 1

    assert dom.content[0].name == "tag"
    assert "PARAM" in dom.content[0].p
    assert dom.content[0].p["PARAM"] == "true"

    assert "param" not in dom.content[0].p

    with pytest.raises(KeyError):
         assert dom.content[0].p["param"]


def test_parse_single_quoted_params():
    dom = dhtmlparser3.parse("<div ID='xa' a='b'>")

    assert dom.name == "div"
    assert dom.p["ID"] == "xa"
    assert dom.p["a"] == "b"


def test_multiline_attribute():
    inp = """<sometag />
<ubertag attribute="long attribute
                    continues here">
    <valid>notice that quote is not properly started</valid>
</ubertag>
<something_parsable />
"""

    dom = dhtmlparser3.parse(inp)

    assert dom.c[0].name == "sometag"
    assert dom.c[0].is_non_pair

    assert dom.c[2].name == "ubertag"
    assert not dom.c[2].is_non_pair
    assert "attribute" in dom.c[2].p
    assert dom.c[2].p["ATTRIBUTE"] == """long attribute
                    continues here"""

    assert dom.c[2].c[1].name == "valid"
    assert not dom.c[2].c[1].is_non_pair
    assert dom.c[2].c[1].c[0] == "notice that quote is not properly started"

    assert dom.c[4].name == "something_parsable"
    assert dom.c[4].is_non_pair


def test_recovery_after_invalid_tag():
    inp = """<sometag />
<invalid tag=something">notice that quote is not properly started</invalid>
<something_parsable />
"""

    dom = dhtmlparser3.parse(inp)

    assert len(dom.content) == 6

    assert dom.content[0].name == "sometag"
    assert dom.content[0].is_non_pair

    assert dom.content[2].name == "invalid"
    assert dom.c[2].parameters == {"tag": "something"}
    assert dom.c[2].c[0] == "notice that quote is not properly started"
    assert not dom.content[2].is_non_pair

    assert dom.content[4].name == "something_parsable"
    assert dom.content[4].is_non_pair


def test_recovery_after_unclosed_tag():
    inp = """<code>Bla</code
<!-- -->

    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parse(inp)

    assert len(dom.c) == 5

    assert dom.name == "code"
    assert dom.c[0] == "Bla</code\n"
    assert dom.c[1] == Comment(" ")
    assert dom.c[3].name == "div"
    assert dom.c[3].p == {"class": "rating"}


def test_recovery_after_is_smaller_than_sign():
    inp = """<code>5 < 10.</code>
    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parse(inp)

    assert dom.c[0].name == "code"
    assert dom.c[0].c[0] == "5 < 10."
    assert dom.c[2].name == "div"


def test_non_pair_structure():
    dom = dhtmlparser3.parse("""<div><br><img><hr></div>""")

    assert dom.name == "div"
    assert len(dom.c) == 3

    assert dom.c[0].name == "br"
    assert not dom.c[0].content
    assert dom.c[1].name == "img"
    assert not dom.c[1].content
    assert dom.c[2].name == "hr"
    assert not dom.c[2].content
