#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Imports =====================================================================
import gc

import specialdict
import htmlelement
from htmlelement import HTMLElement, _rotate_buff


# Functions ===================================================================
class StateEnum(object):
    _cnt = (x for x in range(100))

    content = next(_cnt)
    tag = next(_cnt)
    parameter = next(_cnt)
    comment = next(_cnt)


def _raw_split(itxt):
    """
    Parse HTML from text into array filled with tags end text.

    Source code is little bit unintutive, because it is state machine parser.

    For better understanding, look at http://bit.ly/1rXRcJj

    Example::

        >>> dhtmlparser._raw_split('<html><tag params="true"></html>')
        ['<html>', '<tag params="true">', '</html>']

    Args:
        itxt (str): Input HTML text, which will be parsed.

    Returns:
        list: List of strings (input splitted to tags and text).
    """
    echr = ""
    buff = ["", "", "", ""]
    content = ""
    array = []
    next_state = 0
    inside_tag = False
    escaped = False

    COMMENT_START = ["-", "!", "<"]
    COMMENT_END = ["-", "-"]

    gc.disable()

    for c in itxt:
        # content
        if next_state == StateEnum.content:
            if c == "<":
                if content:
                    array.append(content)

                content = c
                next_state = StateEnum.tag
                inside_tag = False

            else:
                content += c

        # html tag
        elif next_state == StateEnum.tag:
            if c == ">":
                array.append(content + c)
                content = ""
                next_state = StateEnum.content

            elif c == "'" or c == '"':
                echr = c
                content += c
                next_state = StateEnum.parameter

            elif c == "-" and buff[:3] == COMMENT_START:
                if content[:-3]:
                    array.append(content[:-3])

                content = content[-3:] + c
                next_state = StateEnum.comment

            else:
                if c == "<":   # jump back into tag instead of content
                    array.append(content)
                    inside_tag = True
                    content = ""

                content += c

        # quotes "" / ''
        elif next_state == StateEnum.parameter:
            if c == echr and not escaped:  # end of quotes
                next_state = StateEnum.tag

            # unescaped end of line - this is good for invalid HTML like
            # <a href=something">..., because it allows recovery
            if c == "\n" and not escaped:
                next_state = StateEnum.content
                inside_tag = False

            content += c
            escaped = not escaped if c == "\\" else False

        # html comments
        elif next_state == StateEnum.comment:
            if c == ">" and buff[:2] == COMMENT_END:
                next_state = StateEnum.tag if inside_tag else StateEnum.content
                inside_tag = False

                array.append(content + c)
                content = ""
            else:
                content += c

        # rotate buffer
        buff = _rotate_buff(buff)
        buff[0] = c

    gc.enable()

    if content:
        array.append(content)

    return array


def _indexOfEndTag(istack):
    """
    Go through `istack` and search endtag. Element at first index is considered
    as opening tag.

    Args:
        istack (list): List of :class:`.HTMLElement` objects.

    Returns:
        int: Index of end tag or 0 if not found.
    """
    if len(istack) <= 0:
        return 0

    if not istack[0].isOpeningTag():
        return 0

    cnt = 0
    opener = istack[0]
    for index, el in enumerate(istack[1:]):
        if el.isOpeningTag() and \
           el.getTagName().lower() == opener.getTagName().lower():
            cnt += 1

        elif el.isEndTagTo(opener):
            if cnt == 0:
                return index + 1

            cnt -= 1

    return 0


def _parseDOM(istack):
    """
    Recursively go through element array and create DOM.

    Args:
        istack (list): List of :class:`.HTMLElement` objects.

    Returns:
        list: DOM tree as list.
    """
    ostack = []
    end_tag_index = 0

    index = 0
    while index < len(istack):
        el = istack[index]

        # check if this is pair tag
        end_tag_index = _indexOfEndTag(istack[index:])

        if not el.isNonPairTag() and end_tag_index == 0 and not el.isEndTag():
            el.isNonPairTag(True)

        if end_tag_index == 0:
            if not el.isEndTag():
                ostack.append(el)
        else:
            el.childs = _parseDOM(istack[index + 1: end_tag_index + index])
            el.endtag = istack[end_tag_index + index]  # reference to endtag
            el.endtag.openertag = el

            ostack.append(el)
            ostack.append(el.endtag)

            index = end_tag_index + index

        index += 1

    return ostack


def parseString(txt, cip=True):
    """
    Parse string `txt` and return DOM tree consisting of single linked
    :class:`.HTMLElement`.

    Args:
        txt (str): HTML/XML string, which will be parsed to DOM.
        cip (bool, default True): Case Insensitive Parameters. Use special
            dictionary to store :attr:`.HTMLElement.params` as case insensitive.

    Returns:
        obj: Single conteiner HTML element with blank tag, which has whole DOM \
             in it's :attr:`.HTMLElement.childs` property. This element can be \
             queried using :meth:`.HTMLElement.find` functions.
    """
    # remove UTF BOM (prettify fails if not)
    if len(txt) > 3 and txt.startswith("\xef\xbb\xbf"):
        txt = txt[3:]

    if not cip:
        htmlelement.SpecialDict = dict
    elif type(htmlelement.SpecialDict) == dict:
        htmlelement.SpecialDict = specialdict.SpecialDict

    container = HTMLElement()
    container.childs = _parseDOM([
        HTMLElement(x) for x in _raw_split(txt)
    ])

    return container


def makeDoubleLinked(dom, parent=None):
    """
    Standard output from `dhtmlparser` is single-linked tree. This will make it
    double-linked.

    Args:
        dom (obj): :class:`.HTMLElement` instance.
        parent (obj, default None): Don't use this, it is used in recursive
               call.
    """
    dom.parent = parent

    for child in dom.childs:
        child.parent = dom
        makeDoubleLinked(child, dom)


def removeTags(dom):
    """
    Remove all tags from `dom` and obtain plaintext representation.

    Args:
        dom (str, obj, array): str, HTMLElement instance or array of elements.

    Returns:
        str: Plain string without tags.
    """
    # initialize stack with proper value (based on dom parameter)
    element_stack = None
    if type(dom) in [list, tuple]:
        element_stack = dom
    elif isinstance(dom, HTMLElement):
        element_stack = dom.childs if dom.isTag() else [dom]
    elif isinstance(dom, basestring):
        element_stack = parseString(dom).childs
    else:
        element_stack = dom

    # remove all tags
    output = ""
    while element_stack:
        el = element_stack.pop(0)

        if not (el.isTag() or el.isComment() or not el.getTagName()):
            output += str(el)

        if el.childs:
            element_stack = el.childs + element_stack

    return output
