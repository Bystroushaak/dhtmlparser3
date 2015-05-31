#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import pytest

import dhtmlparser


# Functions & objects =========================================================
def test_raw_split():
    splitted = dhtmlparser._raw_split(
        """<html><tag params="true"></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<tag params="true">'
    assert splitted[2] == "</html>"


def test_raw_split_text():
    splitted = dhtmlparser._raw_split(
        """   <html>asd asd"as das</html>   """
    )

    assert splitted
    assert len(splitted) == 5
    assert splitted[0] == "   "
    assert splitted[1] == "<html>"
    assert splitted[2] == 'asd asd"as das'
    assert splitted[3] == "</html>"
    assert splitted[4] == "   "


def test_raw_split_parameters():
    splitted = dhtmlparser._raw_split(
        """<html><tag params="<html_tag>"></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<tag params="<html_tag>">'
    assert splitted[2] == "</html>"


def test_raw_split_parameters_quotes():
    splitted = dhtmlparser._raw_split(
        """<html><tag params="some \\"<quoted>\\" text"></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<tag params="some \\"<quoted>\\" text">'
    assert splitted[2] == "</html>"


def test_raw_split_comments():
    splitted = dhtmlparser._raw_split(
        """<html><!-- asd " asd" > asd --></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<!-- asd " asd" > asd -->'
    assert splitted[2] == "</html>"


def test_index_of_end_tag():
    tag_list = [
        dhtmlparser.HTMLElement("<h1>"),
        dhtmlparser.HTMLElement("<br />"),
        dhtmlparser.HTMLElement("</h1>"),
    ]

    assert dhtmlparser._indexOfEndTag(tag_list) == 2
    assert dhtmlparser._indexOfEndTag(tag_list[1:]) == 0
    assert dhtmlparser._indexOfEndTag(tag_list[2:]) == 0

    tag_list = [
        dhtmlparser.HTMLElement("<h1>"),
        dhtmlparser.HTMLElement("</h1>"),
        dhtmlparser.HTMLElement("</h1>"),
    ]

    assert dhtmlparser._indexOfEndTag(tag_list) == 1


def test_parse_dom():
    tag_list = [
        dhtmlparser.HTMLElement("<h1>"),
        dhtmlparser.HTMLElement("<xx>"),
        dhtmlparser.HTMLElement("<xx>"),
        dhtmlparser.HTMLElement("</h1>"),
    ]

    dom = dhtmlparser._parseDOM(tag_list)

    assert len(dom) == 2
    assert len(dom[0].childs) == 2
    assert dom[0].childs[0].getTagName() == "xx"
    assert dom[0].childs[1].getTagName() == "xx"
    assert dom[0].childs[0].isNonPairTag()
    assert dom[0].childs[1].isNonPairTag()

    assert not dom[0].isNonPairTag()
    assert not dom[1].isNonPairTag()

    assert dom[0].isOpeningTag()
    assert dom[1].isEndTag()

    assert dom[0].endtag == dom[1]
    assert dom[1].openertag == dom[0]

    assert dom[1].isEndTagTo(dom[0])


def test_parseString():
    dom = dhtmlparser.parseString(
        """<html><tag PARAM="true"></html>"""
    )

    assert dom.childs
    assert len(dom.childs) == 2

    assert dom.childs[0].getTagName() == "html"
    assert dom.childs[1].getTagName() == "html"

    assert dom.childs[0].isOpeningTag()
    assert dom.childs[1].isEndTag()

    assert dom.childs[0].childs
    assert not dom.childs[1].childs

    assert dom.childs[0].childs[0].getTagName() == "tag"
    assert dom.childs[0].childs[0].params
    assert not dom.childs[0].childs[0].childs

    assert "param" in dom.childs[0].childs[0].params
    assert dom.childs[0].childs[0].params["param"] == "true"


def test_parseString_cip():
    dom = dhtmlparser.parseString(
        """<html><tag PARAM="true"></html>""",
        cip=False
    )

    assert dom.childs
    assert len(dom.childs) == 2

    assert dom.childs[0].getTagName() == "html"
    assert dom.childs[1].getTagName() == "html"

    assert dom.childs[0].isOpeningTag()
    assert dom.childs[1].isEndTag()

    assert dom.childs[0].childs
    assert not dom.childs[1].childs

    assert dom.childs[0].childs[0].getTagName() == "tag"
    assert dom.childs[0].childs[0].params
    assert not dom.childs[0].childs[0].childs

    assert "param" not in dom.childs[0].childs[0].params
    assert "PARAM" in dom.childs[0].childs[0].params

    assert dom.childs[0].childs[0].params["PARAM"] == "true"

    with pytest.raises(KeyError):
        dom.childs[0].childs[0].params["param"]


def test_makeDoubleLinked():
    dom = dhtmlparser.parseString(
        """<html><tag PARAM="true"></html>"""
    )

    dhtmlparser.makeDoubleLinked(dom)

    assert dom.childs[0].parent == dom
    assert dom.childs[1].parent == dom

    assert dom.childs[0].childs[0].parent == dom.childs[0]


def test_remove_tags():
    dom = dhtmlparser.parseString("a<b>xax<i>xe</i>xi</b>d")
    assert dhtmlparser.removeTags(dom) == "axaxxexid"

    dom = dhtmlparser.parseString("<b></b>")
    assert not dhtmlparser.removeTags(dom)

    dom = dhtmlparser.parseString("<b><i></b>")
    assert not dhtmlparser.removeTags(dom)

    dom = dhtmlparser.parseString("<b><!-- asd --><i></b>")
    assert not dhtmlparser.removeTags(dom)


def test_remove_tags_str_input():
    inp = "a<b>xax<i>xe</i>xi</b>d"

    assert dhtmlparser.removeTags(inp) == "axaxxexid"


def test_recovery_after_invalid_tag():
    inp = """<sometag />
<invalid tag=something">notice that quote is not properly started</invalid>
<something_parsable />
"""

    dom = dhtmlparser.parseString(inp)

    assert dom.find("sometag")
    assert not dom.find("invalid")
    assert dom.find("something_parsable")


def test_recovery_after_unclosed_tag():
    inp = """<code>Já vím... je to příliž krátké a chybí diakritika - je to můj první článek kterej jsem kdy o Linux psal.</code
<!-- -->

    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser.parseString(inp)

    assert dom.find("div", {"class": "rating"})


def test_recovery_after_is_smaller_than_sign():
    inp = """<code>5 < 10.</code>
    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser.parseString(inp)

    code = dom.find("code")

    assert code
    assert code[0].getContent() == "5 < 10."
    assert dom.find("div", {"class": "rating"})
