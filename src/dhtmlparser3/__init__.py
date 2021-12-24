import gc
from enum import IntEnum

from dhtmlparser3 import specialdict

from dhtmlparser3.htmlelement import HTMLElement
from dhtmlparser3.htmlelement import _rotate_buff

from dhtmlparser3.tokens import Text
from dhtmlparser3.tokens import Tag
from dhtmlparser3.tokens import Parameter
from dhtmlparser3.tokens import Comment
from dhtmlparser3.tokens import Entity


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


class Tokenizer:
    MAX_ENTITY_LENGTH = 20

    def __init__(self, string):
        self.string = string
        self.tokens = []

        self.pointer = 0
        self.buffer = ""
        self.char = string[0] if string else ""
        self.end = len(string) - 1

    def tokenize(self):
        if self.end == 0:
            return

        while not self.is_at_end():
            self._scan_token()

        self._linearize_tokens()

        return self.tokens

    def _scan_token(self):
        if self.char == "<":
            self._consume_tag()
        elif self.char == "&":
            self._consume_entity()
        else:
            self._consume_text()

    def _consume_tag(self):
        self.advance()  # consume <

        self._consume_whitespaces()

        endtag = False
        if self.char == "/":
            endtag = True
            self.advance()

        if self.char == ">":
            self.advance()  # consume >
            self.tokens.append(Text("<>"))
            return

        if self.char == "!" and self.peek_is("-") and self.peek_two_is("-"):
            self._consume_comment()
            return

        tag = Tag(self._consume_token_name(), endtag=endtag)
        while not self.is_at_end():
            self._consume_whitespaces()

            if self.char == ">":
                self.advance()  # consume >
                self.tokens.append(tag)
                return

            parameter_name = self._consume_parameter_name()
            self._consume_whitespaces()

            if self.char == "/":
                self.advance()
                if parameter_name:
                    tag.parameters.append(Parameter(parameter_name))
                tag.nonpair = True
                continue

            elif self.char == ">":
                tag.parameters.append(Parameter(parameter_name))
                continue

            elif self.char == "=":
                self.advance()
                self._consume_whitespaces()
                parameter_value = self._consume_parameter_value()
                tag.parameters.append(Parameter(parameter_name, parameter_value))
                continue

    def _consume_whitespaces(self):
        if self.char != " " and self.char != "\t" and self.char != "\n":
            return

        while not self.is_at_end():
            if self.char != " " and self.char != "\t" and self.char != "\n":
                return

            self.advance()

    def _consume_token_name(self):
        self.buffer = self.char
        while not self.is_at_end():
            if self.peek_is(">") or self.peek_is(" "):
                self.advance()  # move to the > or " "
                return self.return_reset_buffer()

            self.buffer += self.advance()

        self.tokens.append(Text(f"<{self.buffer}"))

    def _consume_parameter_name(self):
        if self.char == "/":
            return

        self.buffer = self.char
        while not self.is_at_end():
            peek = self.peek()
            if peek in " <=/>\t\n":
                self.advance()
                return self.return_reset_buffer()

            self.buffer += self.advance()

        self.tokens.append(Text(f"{self.buffer}"))

    def _consume_parameter_value(self):
        if self.char == '"' or self.char == "'":
            return self._consume_quoted_parameter_value()

        self.buffer = self.char
        while not self.is_at_end():
            peek = self.peek()
            if peek in " </>\t\n":
                self.advance()
                return self.return_reset_buffer()

            self.buffer += self.advance()

        self.tokens.append(Text(f"{self.buffer}"))

    def _consume_quoted_parameter_value(self):
        quote_type = self.char
        self.advance()

        if self.peek() == quote_type:
            self.advance()
            return ""

        is_quoted = False
        while not self.is_at_end():
            if self.char == quote_type and not is_quoted:
                self.advance()
                return self.return_reset_buffer()

            if self.char == "\\":
                is_quoted = not is_quoted

                if is_quoted and (self.peek_is(quote_type) or self.peek_is("\\")):
                    self.advance()
                    continue
            else:
                is_quoted = False

            self.buffer += self.char
            self.advance()

        self.tokens.append(Text(f"{self.buffer}"))

    def _consume_comment(self):
        self.advance()  # consume !
        self.advance()  # consume -

        self.buffer = ""
        while not self.is_at_end():
            char = self.advance()

            if char == "-" and self.peek_is("-") and self.peek_two_is(">"):
                self.tokens.append(Comment(self.buffer))
                self.advance()  # consume -
                self.advance()  # consume -
                self.advance()  # consume >
                return

            self.buffer += char

        self.tokens.append(Text(f"<!--{self.buffer}"))
        self.buffer = ""

    def _consume_entity(self):
        length = 0
        self.buffer = self.char
        while not self.is_at_end():
            char = self.advance()
            length += 1

            if char == " ":
                return

            if length > self.MAX_ENTITY_LENGTH:
                return

            self.buffer += char

            if char == ";":
                if self.buffer != "&;":
                    self.tokens.append(Entity(self.buffer))
                    self.buffer = ""

                    if not self.is_at_end():
                        self.advance()

                return

        if self.buffer:
            self.tokens.append(Text(self.buffer))

    def _consume_text(self):
        self.buffer += self.char
        while not self.is_at_end():
            char = self.advance()

            if char == "<" or char == "&":
                self.tokens.append(Text(self.buffer))
                self.buffer = ""
                return

            self.buffer += char

        self.tokens.append(Text(self.buffer))
        self.buffer = ""

    def _linearize_tokens(self):
        if not self.tokens:
            return

        new_tokens = [self.tokens.pop(0)]
        while self.tokens:
            token = self.tokens.pop(0)
            if isinstance(new_tokens[-1], Text) and isinstance(token, Text):
                new_tokens[-1].content += token.content
                continue

            new_tokens.append(token)

        self.tokens = new_tokens

    def return_reset_buffer(self):
        buffer = self.buffer
        self.buffer = ""
        return buffer

    def advance(self):
        self.pointer += 1

        if self.pointer > self.end:
            return ""

        self.char = self.string[self.pointer]

        return self.char

    def is_at_end(self):
        return self.pointer > self.end

    def peek_is(self, char):
        next_char = self.peek()

        return char == next_char

    def peek(self):
        if self.pointer < self.end:
            return self.string[self.pointer + 1]

        return ""

    def peek_two_is(self, char):
        next_char = self.peek_two()

        return char == next_char

    def peek_two(self):
        if (self.pointer + 1) < self.end:
            return self.string[self.pointer + 2]

        return ""


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
