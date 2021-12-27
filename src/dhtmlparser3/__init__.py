import gc
from enum import IntEnum
from typing import Iterator

from dhtmlparser3 import specialdict

from dhtmlparser3.htmlelement import HTMLElement
from dhtmlparser3.htmlelement import _rotate_buff

from dhtmlparser3.tags.tag import Tag

from dhtmlparser3.tokens import Token
from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import EntityToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import ParameterToken
from dhtmlparser3.tokenizer import Tokenizer


class Parser:
    NONPAIR_TAGS = {
        "br",
        "hr",
        "img",
        "input",
        # "link",
        "meta",
        "spacer",
        "frame",
        "base",
    }

    def __init__(self, string: str, case_insensitive_parameters=True):
        # remove UTF BOM (prettify fails if not)
        if len(string) > 3 and string[:3] == "\xef\xbb\xbf":
            string = string[3:]

        if case_insensitive_parameters:
            Tag._DICT_INSTANCE = specialdict.SpecialDict
        else:
            Tag._DICT_INSTANCE = dict

        self.tokenizer = Tokenizer(string)

    def parse_dom(self):
        root_elem = Tag("")

        top_element = root_elem
        element_stack = [root_elem]
        # for token in self.tokenizer.tokenize_iter():
        tokens = self.tokenizer.tokenize()
        for token in tokens:
            if isinstance(token, TextToken) or isinstance(token, CommentToken):
                top_element.content.append(token)
                continue

            if token.is_non_pair:
                top_element.content.append(token.to_tag())
                continue

            if token.is_end_tag:
                closed_element = [
                    x for x in reversed(element_stack) if x.name == token.name
                ]

                # random closing tag which doesn't match anything
                if not closed_element:
                    continue

                closed_element = closed_element[0]

                # correctly closed element on top of the stack
                if closed_element is top_element:
                    element_stack.pop()
                    top_element = element_stack[-1]
                    continue

                top_element = self._reshape_non_pair_tags(element_stack, closed_element)
                continue

            new_top_element = token.to_tag()
            top_element.content.append(new_top_element)
            element_stack.append(new_top_element)
            top_element = new_top_element

        if len(root_elem.content) == 1:
            return root_elem.content[0]

        return root_elem

    def _reshape_non_pair_tags(self, element_stack, closed_element):
        """
        Used for non_pair tags, which are parsed like this:

        "<div><br><img><hr></div>" gets parsed to:

        <div>
            <br>
                <img>
                    <hr>

        What this does is that it changes the structure into:

        <div>
            <br>
            <img>
            <hr>
        """
        # find which one was closed and treat all others as nonpair
        closed_element_index = element_stack.index(closed_element) + 1
        non_pairs = element_stack[closed_element_index:]
        element_stack = element_stack[:closed_element_index]

        # create list of (element, parent) from the non_pairs
        shifted_non_pairs = non_pairs[:]
        shifted_non_pairs.pop()
        shifted_non_pairs.insert(0, element_stack[-1])
        for npt, parent in reversed(list(zip(non_pairs, shifted_non_pairs))):
            self._move_content_to_parent(npt, parent)

        element_stack.pop()
        return element_stack[-1]

    def _move_content_to_parent(self, non_pair_tag: Tag, parent: Tag):
        """
        Take `.content` from `non_pair_tag` and move them to `parent` tag.
        """
        if not non_pair_tag.content:
            return

        npt_index_in_parent = parent.content.index(non_pair_tag)
        for sub_tag in reversed(non_pair_tag.content):
            parent.content.insert(npt_index_in_parent + 1, sub_tag)

        non_pair_tag.content.clear()


def parse(string: str, case_insensitive_parameters=True):
    parser = Parser(string, case_insensitive_parameters)
    return parser.parse_dom()


class StateEnum(IntEnum):
    content = 0
    tag = 1
    parameter = 2
    comment = 3


def first(inp_data):
    """
    Return first element from `inp_data`, or raise StopIteration.

    Note:
        This function was created because it works for generators, lists,
        iterators, tuples and so on same way, which indexing doesn't.

        Also, it has smaller cost than list(generator)[0], because it doesn't
        convert whole `inp_data` to list.

    Args:
        inp_data (iterable): Any iterable object.

    Raises:
        StopIteration: When the `inp_data` is blank.
    """
    return next(x for x in inp_data)


def _raw_split(itxt):
    """
    Parse HTML from text into array filled with tags end text.

    Source code is little bit unintutive, because it is state machine parser.

    For better understanding, look at http://bit.ly/1rXRcJj

    Example::

        >>> dhtmlparser3._raw_split('<html><tag params="true"></html>')
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
    next_state = StateEnum.content
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
                if c == "<":  # jump back into tag instead of content
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
            if c == "\n" and not escaped and buff[0] == ">":
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
        if el.isOpeningTag() and el.getTagName().lower() == opener.getTagName().lower():
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

    def neither_nonpair_or_end_or_comment(el):
        return not (el.isNonPairTag() or el.isEndTag() or el.isComment())

    index = 0
    while index < len(istack):
        el = istack[index]

        # check if this is pair tag
        end_tag_index = _indexOfEndTag(istack[index:])

        if end_tag_index == 0 and neither_nonpair_or_end_or_comment(el):
            el.isNonPairTag(True)

        if end_tag_index == 0:
            if not el.isEndTag():
                ostack.append(el)
        else:
            el.childs = _parseDOM(istack[index + 1 : end_tag_index + index])
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
            dictionary to store :attr:`.HTMLElement.params` as case
            insensitive.

    Returns:
        obj: Single conteiner HTML element with blank tag, which has whole DOM\
             in it's :attr:`.HTMLElement.childs` property. This element can be\
             queried using :meth:`.HTMLElement.find` functions.
    """
    if isinstance(txt, HTMLElement):
        return txt

    # remove UTF BOM (prettify fails if not)
    if len(txt) > 3 and txt[:3] == u"\xef\xbb\xbf":
        txt = txt[3:]

    if not cip:
        htmlelement.html_parser.SpecialDict = dict
    elif isinstance(htmlelement.html_parser.SpecialDict, dict):
        htmlelement.html_parser.SpecialDict = specialdict.SpecialDict

    container = HTMLElement()
    container.childs = _parseDOM([HTMLElement(x) for x in _raw_split(txt)])

    return container


def makeDoubleLinked(dom, parent=None):
    """
    Standard output from `dhtmlparser3` is single-linked tree. This will make it
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
    # python 2 / 3 shill
    try:
        string_type = basestring
    except NameError:
        string_type = str

    # initialize stack with proper value (based on dom parameter)
    element_stack = None
    if type(dom) in [list, tuple]:
        element_stack = dom
    elif isinstance(dom, HTMLElement):
        element_stack = dom.childs if dom.isTag() else [dom]
    elif isinstance(dom, string_type):
        element_stack = parseString(dom).childs
    else:
        element_stack = dom

    # remove all tags
    output = ""
    while element_stack:
        el = element_stack.pop(0)

        if not (el.isTag() or el.isComment() or not el.getTagName()):
            output += el.__str__()

        if el.childs:
            element_stack = el.childs + element_stack

    return output
