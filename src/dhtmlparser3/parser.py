import gc

from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokenizer import Tokenizer
from dhtmlparser3.specialdict import SpecialDict

from dhtmlparser3.tags.tag import Tag
from dhtmlparser3.tags.comment import Comment


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
            Tag._DICT_INSTANCE = SpecialDict
        else:
            Tag._DICT_INSTANCE = dict

        self.tokenizer = Tokenizer(string)

    def parse_dom(self) -> Tag:
        gc.disable()

        root_elem = Tag("")

        top_element = root_elem
        element_stack = [root_elem]
        for token in self.tokenizer.tokenize_iter():
            if isinstance(token, TextToken):
                top_element.content.append(token.content)
                continue

            elif isinstance(token, CommentToken):
                top_element.content.append(Comment(token.content))
                continue

            elif token.is_non_pair:
                top_element.content.append(token.to_tag())
                continue

            elif token.is_end_tag:
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
            new_top_element.parent = top_element
            element_stack.append(new_top_element)
            top_element = new_top_element

        if len(element_stack) > 1:
            self._reshape_non_pair_tags(element_stack, root_elem)

        gc.enable()

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
        new_element_stack = element_stack[:closed_element_index]
        element_stack.clear()
        element_stack.extend(new_element_stack)

        # create list of (element, parent) from the non_pairs
        shifted_non_pairs = non_pairs[:]
        shifted_non_pairs.pop()
        shifted_non_pairs.insert(0, element_stack[-1])
        for npt, parent in reversed(list(zip(non_pairs, shifted_non_pairs))):
            self._move_content_to_parent(npt, parent)
            npt.is_non_pair = True
            npt.parent = closed_element

        if element_stack:
            element_stack.pop()

            if element_stack:
                return element_stack[-1]

        return closed_element

    def _move_content_to_parent(self, non_pair_tag: Tag, parent: Tag):
        """
        Take `.content` from `non_pair_tag` and move them to `parent` tag.
        """
        if not non_pair_tag.content:
            return

        try:
            npt_index_in_parent = parent.content.index(non_pair_tag)
        except ValueError:
            npt_index_in_parent = 0

        for sub_tag in reversed(non_pair_tag.content):
            parent.content.insert(npt_index_in_parent + 1, sub_tag)

        non_pair_tag.content.clear()