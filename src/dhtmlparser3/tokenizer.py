from typing import List

from dhtmlparser3.tokens import Tag
from dhtmlparser3.tokens import Text
from dhtmlparser3.tokens import Token
from dhtmlparser3.tokens import Entity
from dhtmlparser3.tokens import Comment
from dhtmlparser3.tokens import Parameter


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
