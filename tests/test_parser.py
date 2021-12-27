import pytest

import dhtmlparser3
from dhtmlparser3 import first
from dhtmlparser3.tokenizer import Tokenizer

from dhtmlparser3.tags.tag import Tag

from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import ParameterToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import EntityToken


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
    assert dom.c[2].c[1].c[0].content == "notice that quote is not properly started"

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
    assert dom.c[2].c[0].content == "notice that quote is not properly started"
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
    assert dom.c[0] == TextToken("Bla</code\n")
    assert dom.c[1] == CommentToken(" ")
    assert dom.c[3].name == "div"
    assert dom.c[3].p == {"class": "rating"}


def _test_recovery_after_is_smaller_than_sign():
    inp = """<code>5 < 10.</code>
    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parseString(inp)

    code = dom.find("code")

    assert code
    assert first(code).getContent() == "5 < 10."
    assert dom.find("div", {"class": "rating"})



# def _test_makeDoubleLinked():
#     dom = dhtmlparser3.parseString("""<html><tag PARAM="true"></html>""")
#
#     dhtmlparser3.makeDoubleLinked(dom)
#
#     assert dom.childs[0].parent == dom
#     assert dom.childs[1].parent == dom
#
#     assert dom.childs[0].childs[0].parent == dom.childs[0]
#
#
# def _test_remove_tags():
#     dom = dhtmlparser3.parseString("a<b>xax<i>xe</i>xi</b>d")
#     assert dhtmlparser3.removeTags(dom) == "axaxxexid"
#
#     dom = dhtmlparser3.parseString("<b></b>")
#     assert not dhtmlparser3.removeTags(dom)
#
#     dom = dhtmlparser3.parseString("<b><i></b>")
#     assert not dhtmlparser3.removeTags(dom)
#
#     dom = dhtmlparser3.parseString("<b><!-- asd --><i></b>")
#     assert not dhtmlparser3.removeTags(dom)
#
#
# def _test_remove_tags_str_input():
#     inp = "a<b>xax<i>xe</i>xi</b>d"
#
#     assert dhtmlparser3.removeTags(inp) == "axaxxexid"


# def _test_equality_of_output_with_comment():
#     inp = """<head>
#     <!-- <link rel="stylesheet" type="text/css" href="style.css"> -->
# </head>
# """
#     dom = dhtmlparser3.parseString(inp)
#
#     assert dom.__str__() == inp


#
# def _test_index_of_end_tag():
#     tag_list = [
#         dhtmlparser3.HTMLElement("<h1>"),
#         dhtmlparser3.HTMLElement("<br />"),
#         dhtmlparser3.HTMLElement("</h1>"),
#     ]
#
#     assert dhtmlparser3._indexOfEndTag(tag_list) == 2
#     assert dhtmlparser3._indexOfEndTag(tag_list[1:]) == 0
#     assert dhtmlparser3._indexOfEndTag(tag_list[2:]) == 0
#
#     tag_list = [
#         dhtmlparser3.HTMLElement("<h1>"),
#         dhtmlparser3.HTMLElement("</h1>"),
#         dhtmlparser3.HTMLElement("</h1>"),
#     ]
#
#     assert dhtmlparser3._indexOfEndTag(tag_list) == 1
#
#
# def _test_parse_dom():
#     tag_list = [
#         dhtmlparser3.HTMLElement("<h1>"),
#         dhtmlparser3.HTMLElement("<xx>"),
#         dhtmlparser3.HTMLElement("<xx>"),
#         dhtmlparser3.HTMLElement("</h1>"),
#     ]
#
#     dom = dhtmlparser3._parseDOM(tag_list)
#
#     assert len(dom) == 2
#     assert len(first(dom).childs) == 2
#     assert first(dom).childs[0].getTagName() == "xx"
#     assert first(dom).childs[1].getTagName() == "xx"
#     assert first(dom).childs[0].isNonPairTag()
#     assert first(dom).childs[1].isNonPairTag()
#
#     assert not dom[0].isNonPairTag()
#     assert not dom[1].isNonPairTag()
#
#     assert dom[0].isOpeningTag()
#     assert dom[1].isEndTag()
#
#     assert dom[0].is_end_tag == dom[1]
#     assert dom[1].openertag == dom[0]
#
#     assert dom[1].isEndTagTo(dom[0])