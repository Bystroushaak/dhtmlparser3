import pytest

import dhtmlparser3
from dhtmlparser3 import first
from dhtmlparser3.tokenizer import Tokenizer

from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import ParameterToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import EntityToken

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


def test_recovery_after_invalid_tag():
    inp = """<sometag />
<invalid tag=something">notice that quote is not properly started</invalid>
<something_parsable />
"""

    dom = dhtmlparser3.parse(inp)

    assert len(dom.content) == 3

    assert dom.content[0].name == "sometag"
    assert dom.content[0].is_non_pair

    assert dom.content[2].name == "something_parsable"
    assert dom.content[2].is_non_pair

    # assert dom.find("sometag")
    # assert not dom.find("invalid")
    # assert dom.find("something_parsable")


def _test_recovery_after_unclosed_tag():
    inp = """<code>Já vím... je to příliž krátké a chybí diakritika - je to můj první článek kterej jsem kdy o Linux psal.</code
<!-- -->

    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parseString(inp)

    assert dom.find("div", {"class": "rating"})


def _test_recovery_after_is_smaller_than_sign():
    inp = """<code>5 < 10.</code>
    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parseString(inp)

    code = dom.find("code")

    assert code
    assert first(code).getContent() == "5 < 10."
    assert dom.find("div", {"class": "rating"})


def _test_multiline_attribute():
    inp = """<sometag />
<ubertag attribute="long attribute
                    continues here">
    <valid>notice that quote is not properly started</valid>
</ubertag>
<something_parsable />
"""

    dom = dhtmlparser3.parseString(inp)

    assert dom.find("sometag")
    assert dom.find("valid")
    assert dom.find("ubertag")
    assert (
        first(dom.find("ubertag")).params["attribute"]
        == """long attribute
                    continues here"""
    )
    assert dom.find("something_parsable")


# def _test_equality_of_output_with_comment():
#     inp = """<head>
#     <!-- <link rel="stylesheet" type="text/css" href="style.css"> -->
# </head>
# """
#     dom = dhtmlparser3.parseString(inp)
#
#     assert dom.__str__() == inp
