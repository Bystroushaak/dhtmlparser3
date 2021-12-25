from typing import List

from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import Token
from dhtmlparser3.tokens import EntityToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import ParameterToken


class Tokenizer:
    tokens: List[Token]
    MAX_ENTITY_LENGTH = 20

    def __init__(self, string: str):
        self.string = string
        self.tokens = []

        self.pointer = 0
        self.buffer = ""
        self.char = string[0] if string else ""
        self.end = len(string) - 1

    def tokenize(self) -> List[Token]:
        if self.end == 0:
            return []

        while not self.is_at_end():
            self._scan_token()

        self._linearize_tokens()

        return self.tokens

    def _scan_token(self):
        if self.char == "<":
            pointer = self.pointer
            try:
                self._consume_tag()
            except IOError:
                self.tokens.append(TextToken(self.string[pointer:]))
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
            self.tokens.append(TextToken("<>"))
            return

        if self.char == "!" and self.peek_is("-") and self.peek_two_is("-"):
            self._consume_comment()
            return

        tag = TagToken(self._consume_tag_name(), endtag=endtag)
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
                    tag.parameters.append(ParameterToken(parameter_name))
                tag.nonpair = True
                continue

            elif self.char == ">":
                tag.parameters.append(ParameterToken(parameter_name))
                continue

            elif self.char == "=":
                self.advance()
                self._consume_whitespaces()
                parameter_value = self._consume_parameter_value()
                tag.parameters.append(ParameterToken(parameter_name, parameter_value))
                continue

    def _consume_whitespaces(self):
        if self.char != " " and self.char != "\t" and self.char != "\n":
            return

        while not self.is_at_end():
            if self.char != " " and self.char != "\t" and self.char != "\n":
                return

            self.advance()

    def _consume_tag_name(self):
        self.buffer = self.char
        while not self.is_at_end():
            if self.peek_is(">") or self.peek_is(" "):
                self.advance()  # move to the > or " "
                return self.return_reset_buffer()

            self.buffer += self.advance()

        raise IOError("End of string while parsing tag name!")

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

        raise IOError("End of string while paring parameter name!")

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

        raise IOError("End of string while parsing parameter value!")

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

        raise IOError("End of string while parsing parameter value!")

    def _consume_comment(self):
        self.advance()  # consume !
        self.advance()  # consume -

        self.buffer = ""
        while not self.is_at_end():
            char = self.advance()

            if char == "-" and self.peek_is("-") and self.peek_two_is(">"):
                self.tokens.append(CommentToken(self.buffer))
                self.advance()  # consume -
                self.advance()  # consume -
                self.advance()  # consume >
                return

            self.buffer += char

        self.tokens.append(TextToken(f"<!--{self.buffer}"))
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
                    self.tokens.append(EntityToken(self.buffer))
                    self.buffer = ""

                    if not self.is_at_end():
                        self.advance()

                return

        if self.buffer:
            self.tokens.append(TextToken(self.buffer))

    def _consume_text(self):
        self.buffer += self.char
        while not self.is_at_end():
            char = self.advance()

            if char == "<" or char == "&":
                self.tokens.append(TextToken(self.buffer))
                self.buffer = ""
                return

            self.buffer += char

        self.tokens.append(TextToken(self.buffer))
        self.buffer = ""

    def _linearize_tokens(self):
        if not self.tokens:
            return

        if isinstance(self.tokens[0], EntityToken):
            new_tokens = [TextToken(self.tokens.pop(0).to_text())]
        else:
            new_tokens = [self.tokens.pop(0)]

        while self.tokens:
            token = self.tokens.pop(0)

            if isinstance(token, EntityToken):
                self.tokens.insert(0, TextToken(token.to_text()))
                continue

            if isinstance(new_tokens[-1], TextToken) and isinstance(token, TextToken):
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
