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


def test_double_link():
    dom = dhtmlparser3.parse("""<html><tag PARAM="true"></html>""")
    dom.double_link()

    assert dom.c[0].parent == dom


def test_remove_tags():
    dom = dhtmlparser3.parse("a<b>xax<i>xe</i>xi</b>d")
    assert dom.remove_tags() == "axaxxexid"

    dom = dhtmlparser3.parse("<b></b>")
    assert not dom.remove_tags()

    dom = dhtmlparser3.parse("<b><i></b>")
    assert not dom.remove_tags()

    dom = dhtmlparser3.parse("<b><!-- asd --><i></b>")
    assert not dom.remove_tags()


def test_to_string():
    dom = dhtmlparser3.parse("""<html><tag PARAM="true" rectangular /></html>""")

    assert dom.c[0].name == "tag"
    assert dom.c[0].p["param"] == "true"
    assert dom.c[0].p["rectangular"] == ""

    assert dom.c[0].to_string() == '<tag PARAM="true" rectangular />'


def test_depth_first_iterator():
    dom = dhtmlparser3.parse("<div><x>a</x><y>b</y></div>")

    items = list(dom.depth_first_iterator())

    assert items == [
        Tag("div"),
        Tag("x"),
        "a",
        Tag("y"),
        "b",
    ]


def test_depth_first_iterator_tags_only():
    dom = dhtmlparser3.parse("<div><x>a</x><y>b</y></div>")

    items = list(dom.depth_first_iterator(tags_only=True))

    assert items == [
        Tag("div"),
        Tag("x"),
        Tag("y"),
    ]


def test_breadth_first_iterator():
    dom = dhtmlparser3.parse("<div><x>a</x><y>b</y></div>")

    items = list(dom.breadth_first_iterator())

    assert items == [
        Tag("div"),
        Tag("x"),
        Tag("y"),
        "a",
        "b",
    ]


def test_breadth_first_iterator_tags_only():
    dom = dhtmlparser3.parse("<div><x><z /></x><y>b</y></div>")

    items = list(dom.breadth_first_iterator(tags_only=True))

    assert items == [
        Tag("div"),
        Tag("x"),
        Tag("y"),
        Tag("z", is_non_pair=True)
    ]


def _test_find():
    dom = dhtmlparser3.parseString(
        """
        "<div ID='xa' a='b'>obsah xa divu</div> <!-- ID, not id :) -->
         <div id='xex' a='b'>obsah xex divu</div>
        """
    )

    div_xe = dom.find("div", {"id": "xa"})  # notice the small `id`
    div_xex = dom.find("div", {"id": "xex"})
    div_xerexes = dom.find("div", {"id": "xerexex"})

    assert div_xe
    assert div_xex
    assert not div_xerexes

    div_xe = first(div_xe)
    div_xex = first(div_xex)

    assert div_xe.toString() == '<div ID="xa" a="b">obsah xa divu</div>'
    assert div_xex.toString() == '<div id="xex" a="b">obsah xex divu</div>'

    assert div_xe.getTagName() == "div"
    assert div_xex.getTagName() == "div"
