import pytest

import dhtmlparser3
from dhtmlparser3.tokenizer import Tokenizer

from dhtmlparser3.tags.tag import Tag

from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import ParameterToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import EntityToken


def test_constructor_with_content():
    e = Tag(
        "name",
        {"key": "value"},
        [
            "hello",
            Tag("hi", is_non_pair=True)
        ]
    )

    assert not e.is_non_pair

    assert e.content
    assert e.parameters

    assert e.to_string() == '<name key="value">hello<hi /></name>'
    assert e.content_str() == "hello<hi />"
    assert e.name == "name"

    assert "key" in e.parameters
    assert e.parameters["key"] == "value"

    assert dict(e.parameters) == {"key": "value"}

    assert len(e.content) == 2

    assert e.content[0] == "hello"
    assert e.content[1].name == "hi"


def test_constructor_with_content_only():
    e = Tag(
        name="",
        content=[
            "hello",
            Tag("hi"),
        ]
    )

    assert e.content
    assert not e.parameters
    assert not e.is_non_pair

    assert e.to_string() == "hello<hi></hi>"
    assert e.content_str() == "hello<hi></hi>"
    assert not e.tag_to_str()
    assert not e.name

    assert len(e.content) == 2

    assert e.content[0] == "hello"
    assert e.content[1].name == "hi"


def test_parameters():
    dom = dhtmlparser3.parse("<xe id=1 />")
    xe = dom.find("xe")[0]

    assert xe.parameters["id"] == "1"
    xe.parameters = {}

    assert xe.to_string() == "<xe />"


def test_contains_parameters_subset():
    dom = dhtmlparser3.parse("<div id=x class=xex></div>")
    div = dom.find("div")[0]

    assert div._contains_parameters_subset({"id": "x"})
    assert div._contains_parameters_subset({"class": "xex"})
    assert div._contains_parameters_subset({"id": "x", "class": "xex"})
    assert not div._contains_parameters_subset(
        {"asd": "bsd", "id": "x", "class": "xex"}
    )


def test_to_string():
    dom = dhtmlparser3.parse("""<html><tag PARAM="true" rectangular /></html>""")

    assert dom.c[0].name == "tag"
    assert dom.c[0].p["param"] == "true"
    assert dom.c[0].p["rectangular"] == ""

    assert dom.c[0].to_string() == '<tag PARAM="true" rectangular />'


def test_content_str():
    dom = dhtmlparser3.parse("""
<div id=first>
    First div.
    <div id=first.subdiv>
        Subdiv in first div.
    </div>
</div>
<div id=second>
    Second.
    <br />
    <!-- comment -->
</div>
    """)

    div = dom.find("div", {"id": "first.subdiv"})[0]
    assert div.content_str().strip() == "Subdiv in first div."

    second_div = dom.find("div", {"id": "second"})[0]
    match = '\n    Second.\n    <br />\n    <!-- comment -->\n'
    assert second_div.content_str() == match


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

    assert items == [Tag("div"), Tag("x"), Tag("y"), Tag("z", is_non_pair=True)]


def test_find():
    dom = dhtmlparser3.parse(
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

    div_xe = div_xe[0]
    div_xex = div_xex[0]

    assert div_xe.to_string() == '<div ID="xa" a="b">obsah xa divu</div>'
    assert div_xex.to_string() == '<div id="xex" a="b">obsah xex divu</div>'

    assert div_xe.name == "div"
    assert div_xex.name == "div"


def test_find_fn():
    dom = dhtmlparser3.parse(
        """
        <div id=first>
            First div.
            <div id=first.subdiv>
                Subdiv in first div.
            </div>
        </div>
        <div id=second>
            Second.
        </div>
        """
    )

    div_tags = dom.find("div", fn=lambda x: x.p.get("id") == "first")

    assert div_tags
    assert len(div_tags) == 1

    assert div_tags[0].p.get("id") == "first"
    assert div_tags[0].content_str().strip().startswith("First div.")


def test_find_parameters():
    dom = dhtmlparser3.parse(
        """
        <div id=first>
            First div.
            <div id=first.subdiv>
                Subdiv in first div.
            </div>
        </div>
        <div id=second>
            Second.
        </div>
        """
    )

    div_tags = dom.find("", {"id": "first"})

    assert div_tags
    assert len(div_tags) == 1

    assert div_tags[0].p.get("id") == "first"
    assert div_tags[0].content_str().strip().startswith("First div.")


def test_findb():
    dom = dhtmlparser3.parse(
        """
        <div id=first>
            First div.
            <div id=first.subdiv>
                Subdiv in first div.
            </div>
        </div>
        <div id=second>
            Second.
        </div>
        """
    )

    assert dom.find("div")[1].content_str().strip() == "Subdiv in first div."
    assert dom.findb("div")[1].content_str().strip() == "Second."


def test_wfind():
    dom = dhtmlparser3.parse(
        """
        <div id=first>
            First div.
            <div id=first.subdiv>
                Subdiv in first div.
            </div>
        </div>
        <div id=second>
            Second.
        </div>
        """
    )

    div = dom.wfind("div").wfind("div")

    assert div.content
    assert div.content[0].p["id"] == "first.subdiv"


def test_wfind_complicated():
    dom = dhtmlparser3.parse(
        """
        <root>
            <some>
                <something>
                    <xe id="wanted xe" />
                </something>
                <something>
                    asd
                </something>
                <xe id="another xe" />
            </some>
            <some>
                else
                <xe id="yet another xe" />
            </some>
        </root>
        """
    )

    xe = dom.wfind("root").wfind("some").wfind("something").find("xe")

    assert len(xe) == 1
    assert xe[0].parameters["id"] == "wanted xe"

    unicorn = dom.wfind("root").wfind("pink").wfind("unicorn")

    assert not unicorn.content


def test_wfind_multiple_matches():
    dom = dhtmlparser3.parse(
        """
        <root>
            <some>
                <something>
                    <xe id="wanted xe" />
                </something>
                <something>
                    <xe id="another wanted xe" />
                </something>
                <xe id="another xe" />
            </some>
            <some>
                <something>
                    <xe id="last wanted xe" />
                </something>
            </some>
        </root>
        """
    )

    xe = dom.wfind("root").wfind("some").wfind("something").wfind("xe")

    assert len(xe.content) == 3
    assert xe.content[0].parameters["id"] == "wanted xe"
    assert xe.content[1].parameters["id"] == "another wanted xe"
    assert xe.content[2].parameters["id"] == "last wanted xe"


def test_match():
    dom = dhtmlparser3.parse(
        """
        <root>
            <some>
                <something>
                    <xe id="wanted xe" />
                </something>
                <something>
                    <xe id="another wanted xe" />
                </something>
                <xe id="another xe" />
            </some>
            <some>
                <something>
                    <xe id="last wanted xe" />
                </something>
            </some>
        </root>
        """
    )

    xe = dom.match("root", "some", "something", "xe")
    assert len(xe) == 3
    assert xe[0].parameters["id"] == "wanted xe"
    assert xe[1].parameters["id"] == "another wanted xe"
    assert xe[2].parameters["id"] == "last wanted xe"


def test_match_parameters():
    dom = dhtmlparser3.parse(
        """
        <root>
            <div id="1">
                <div id="5">
                    <xe id="wanted xe" />
                </div>
                <div id="10">
                    <xe id="another wanted xe" />
                </div>
                <xe id="another xe" />
            </div>
            <div id="2">
                <div id="20">
                    <xe id="last wanted xe" />
                </div>
            </div>
        </root>
        """
    )

    xe = dom.match(
        "root", {"name": "div", "p": {"id": "1"}}, ["div", {"id": "5"}], "xe"
    )

    assert len(xe) == 1
    assert xe[0].parameters["id"] == "wanted xe"


def test_match_parameters_relative_path():
    dom = dhtmlparser3.parse(
        """
        <root>
            <div id="1">
                <div id="5">
                    <xe id="wanted xe" />
                </div>
                <div id="10">
                    <xe id="another wanted xe" />
                </div>
                <xe id="another xe" />
            </div>
            <div id="2">
                <div id="20">
                    <xe id="last wanted xe" />
                </div>
            </div>
        </root>
        """
    )

    xe = dom.match(
        {"name": "div", "p": {"id": "1"}},
        ["div", {"id": "5"}],
        "xe",
    )

    assert len(xe) == 1
    assert xe[0].parameters["id"] == "wanted xe"


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


def test_replace_with():
    dom = dhtmlparser3.parse("<div><nonpair /></div>")
    nonpair = dom.find("nonpair")[0]

    assert nonpair

    nonpair.replace_with(
        Tag("another", is_non_pair=True)
    )

    assert dom.find("another")
    assert dom.to_string() == "<div><another /></div>"
