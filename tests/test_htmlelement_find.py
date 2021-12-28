#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import dhtmlparser3
from dhtmlparser3 import first


# Functions & objects =========================================================
def test_match():
    dom = dhtmlparser3.parseString(
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
    assert xe[0].params["id"] == "wanted xe"
    assert xe[1].params["id"] == "another wanted xe"
    assert xe[2].params["id"] == "last wanted xe"

def test_match_parameters():
    dom = dhtmlparser3.parseString(
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
        "root",
        {"tag_name": "div", "params": {"id": "1"}},
        ["div", {"id": "5"}],
        "xe"
    )

    assert len(xe) == 1
    assert first(xe).params["id"] == "wanted xe"


def test_match_parameters_relative_path():
    dom = dhtmlparser3.parseString(
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
        {"tag_name": "div", "params": {"id": "1"}},
        ["div", {"id": "5"}],
        "xe",
    )

    assert len(xe) == 1
    assert first(xe).params["id"] == "wanted xe"

    xe = dom.match(
        {"tag_name": "div", "params": {"id": "1"}},
        ["div", {"id": "5"}],
        "xe",
        absolute=True
    )

    assert not xe
