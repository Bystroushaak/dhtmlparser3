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
