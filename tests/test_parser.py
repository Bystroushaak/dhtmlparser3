import pytest

import dhtmlparser3
from dhtmlparser3 import first
from dhtmlparser3 import Tokenizer

from dhtmlparser3.tokens import Text
from dhtmlparser3.tokens import Element
from dhtmlparser3.tokens import Parameter
from dhtmlparser3.tokens import Comment
from dhtmlparser3.tokens import Entity


def test_entity_consumption():
    tokenizer = Tokenizer("&nbsp;")

    assert tokenizer.tokenize() == [Entity("&nbsp;")]


def test_text_consumption():
    tokenizer = Tokenizer("Some text.")

    assert tokenizer.tokenize() == [Text("Some text.")]


def test_text_and_entity_consumption():
    tokenizer = Tokenizer("&entity;Some text.&entity2;")

    assert tokenizer.tokenize() == [
        Entity("&entity;"),
        Text("Some text."),
        Entity("&entity2;")
    ]

def test_entity_mixup_consumption():
    tokenizer = Tokenizer("&entity Some text")

    assert tokenizer.tokenize() == [
        Text("&entity Some text"),
    ]


def test_long_entity():
    tokenizer = Tokenizer("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;")

    assert tokenizer.tokenize() == [
        Text("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;"),
    ]


def test_possible_entity():
    tokenizer = Tokenizer("aaaa&a a;")

    assert tokenizer.tokenize() != [
        Text("aaaa"),
        Text("&a a;"),
    ]

    assert tokenizer.tokens == [Text("aaaa&a a;")]


def test_entity_at_the_end():
    tokenizer = Tokenizer("&a a")

    assert tokenizer.tokenize() == [
        Text("&a a"),
    ]


def test_comment():
    tokenizer = Tokenizer("aaa <!-- comment -->")

    assert tokenizer.tokenize() == [
        Text("aaa "),
        Comment(" comment ")
    ]


def test_comment_without_end():
    tokenizer = Tokenizer("aaa <!-- comment ")

    assert tokenizer.tokenize() == [
        Text("aaa <!-- comment "),
    ]


def test_empty_tag():
    tokenizer = Tokenizer("<>")

    assert tokenizer.tokenize() == [Text("<>")]


def test_empty_tag_continuation():
    tokenizer = Tokenizer("<> ")

    assert tokenizer.tokenize() == [Text("<> ")]


def test_tag():
    tokenizer = Tokenizer("<tag>")

    assert tokenizer.tokenize() == [Element("tag")]


def test_tag_with_whitespaces_before_tag_name():
    tokenizer = Tokenizer("<  tag>")

    assert tokenizer.tokenize() == [Element("tag")]


def test_tag_with_whitespaces_after_tag_name():
    tokenizer = Tokenizer("<  tag  >")

    assert tokenizer.tokenize() == [Element("tag")]


def _test_raw_split():
    tokenizer = Tokenizer("""<html><tag params="true"></html>""")
    tokenizer.tokenize()

    # assert tokenizer
    # assert len(splitted) == 3
    # assert splitted[0] == "<html>"
    # assert splitted[1] == '<tag params="true">'
    # assert splitted[2] == "</html>"


def _test_raw_split_text():
    splitted = dhtmlparser3._raw_split(
        """   <html>asd asd"as das</html>   """
    )

    assert splitted
    assert len(splitted) == 5
    assert splitted[0] == "   "
    assert splitted[1] == "<html>"
    assert splitted[2] == 'asd asd"as das'
    assert splitted[3] == "</html>"
    assert splitted[4] == "   "


def _test_raw_split_parameters():
    splitted = dhtmlparser3._raw_split(
        """<html><tag params="<html_tag>"></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<tag params="<html_tag>">'
    assert splitted[2] == "</html>"


def _test_raw_split_parameters_quotes():
    splitted = dhtmlparser3._raw_split(
        """<html><tag params="some \\"<quoted>\\" text"></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<tag params="some \\"<quoted>\\" text">'
    assert splitted[2] == "</html>"


def _test_raw_split_comments():
    splitted = dhtmlparser3._raw_split(
        """<html><!-- asd " asd" > asd --></html>"""
    )

    assert splitted
    assert len(splitted) == 3
    assert splitted[0] == "<html>"
    assert splitted[1] == '<!-- asd " asd" > asd -->'
    assert splitted[2] == "</html>"


def _test_index_of_end_tag():
    tag_list = [
        dhtmlparser3.HTMLElement("<h1>"),
        dhtmlparser3.HTMLElement("<br />"),
        dhtmlparser3.HTMLElement("</h1>"),
    ]

    assert dhtmlparser3._indexOfEndTag(tag_list) == 2
    assert dhtmlparser3._indexOfEndTag(tag_list[1:]) == 0
    assert dhtmlparser3._indexOfEndTag(tag_list[2:]) == 0

    tag_list = [
        dhtmlparser3.HTMLElement("<h1>"),
        dhtmlparser3.HTMLElement("</h1>"),
        dhtmlparser3.HTMLElement("</h1>"),
    ]

    assert dhtmlparser3._indexOfEndTag(tag_list) == 1


def _test_parse_dom():
    tag_list = [
        dhtmlparser3.HTMLElement("<h1>"),
        dhtmlparser3.HTMLElement("<xx>"),
        dhtmlparser3.HTMLElement("<xx>"),
        dhtmlparser3.HTMLElement("</h1>"),
    ]

    dom = dhtmlparser3._parseDOM(tag_list)

    assert len(dom) == 2
    assert len(first(dom).childs) == 2
    assert first(dom).childs[0].getTagName() == "xx"
    assert first(dom).childs[1].getTagName() == "xx"
    assert first(dom).childs[0].isNonPairTag()
    assert first(dom).childs[1].isNonPairTag()

    assert not dom[0].isNonPairTag()
    assert not dom[1].isNonPairTag()

    assert dom[0].isOpeningTag()
    assert dom[1].isEndTag()

    assert dom[0].endtag == dom[1]
    assert dom[1].openertag == dom[0]

    assert dom[1].isEndTagTo(dom[0])


def _test_parseString():
    dom = dhtmlparser3.parseString(
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


def _test_parseString_cip():
    dom = dhtmlparser3.parseString(
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


def _test_makeDoubleLinked():
    dom = dhtmlparser3.parseString(
        """<html><tag PARAM="true"></html>"""
    )

    dhtmlparser3.makeDoubleLinked(dom)

    assert dom.childs[0].parent == dom
    assert dom.childs[1].parent == dom

    assert dom.childs[0].childs[0].parent == dom.childs[0]


def _test_remove_tags():
    dom = dhtmlparser3.parseString("a<b>xax<i>xe</i>xi</b>d")
    assert dhtmlparser3.removeTags(dom) == "axaxxexid"

    dom = dhtmlparser3.parseString("<b></b>")
    assert not dhtmlparser3.removeTags(dom)

    dom = dhtmlparser3.parseString("<b><i></b>")
    assert not dhtmlparser3.removeTags(dom)

    dom = dhtmlparser3.parseString("<b><!-- asd --><i></b>")
    assert not dhtmlparser3.removeTags(dom)


def _test_remove_tags_str_input():
    inp = "a<b>xax<i>xe</i>xi</b>d"

    assert dhtmlparser3.removeTags(inp) == "axaxxexid"


def _test_recovery_after_invalid_tag():
    inp = """<sometag />
<invalid tag=something">notice that quote is not properly started</invalid>
<something_parsable />
"""

    dom = dhtmlparser3.parseString(inp)

    assert dom.find("sometag")
    assert not dom.find("invalid")
    assert dom.find("something_parsable")


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
    assert first(dom.find("ubertag")).params["attribute"] == """long attribute
                    continues here"""
    assert dom.find("something_parsable")


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


def _test_equality_of_output_with_comment():
    inp = """<head>
    <!-- <link rel="stylesheet" type="text/css" href="style.css"> -->
</head>
"""
    dom = dhtmlparser3.parseString(inp)

    assert dom.__str__() == inp
