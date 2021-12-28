#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import dhtmlparser3
from dhtmlparser3 import first


# Variables ===================================================================
TEXT = "<div><nonpair /></div>"
dom = dhtmlparser3.parseString(TEXT)


# Functions & objects =========================================================
def _test_removeChild():
    dom.removeChild(
        dom.find("another")
    )

    assert dom.getContent() == "<div></div>"

    dom.removeChild(dom.find("div"), end_tag_too=False)

    assert dom.getContent() == ""
    assert len(dom.childs) == 1  # endtag wasn't removed

    dom2 = dhtmlparser3.parseString("<div></div>")
    dom2.removeChild(dom2.find("div"))

    assert dom2.getContent() == ""
    assert not dom2.childs


