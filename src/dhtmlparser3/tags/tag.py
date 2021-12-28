from typing import Union
from typing import Iterator

import dhtmlparser3
from dhtmlparser3.quoter import escape
from dhtmlparser3.specialdict import SpecialDict
from dhtmlparser3.tags.comment import Comment


class Tag:
    _DICT_INSTANCE = SpecialDict

    def __init__(self, name, parameters=None, content=None, is_non_pair=False):
        self.name = name

        if parameters is None:
            self.parameters = self._DICT_INSTANCE()
        elif isinstance(parameters, dict):
            self.parameters = self._DICT_INSTANCE(parameters)
        else:
            self.parameters = parameters

        self.content = content if content is not None else []

        self.is_non_pair = is_non_pair
        self.parent = None

    @property
    def p(self):
        return self.parameters

    @property
    def c(self):
        return self.content

    def double_link(self):
        for item in self.content:
            if isinstance(item, Tag):
                item.parent = self
                item.double_link()

    def remove_tags(self):
        output = ""
        for item in self.content:
            if isinstance(item, Tag):
                output += item.remove_tags()
            elif isinstance(item, str):
                output += item

        return output

    def to_string(self):
        output = self.tag_to_str()
        for item in self.content:
            if isinstance(item, str):
                output += item
            else:
                output += item.to_string()

        if self.name:
            return f"{output}</{self.name}>"

        return output

    def tag_to_str(self):
        if not self.name:
            return ""

        if self.is_non_pair:
            return f"<{self.name}{self._parameters_to_str()} />"

        return f"<{self.name}{self._parameters_to_str()}>"

    def content_str(self):
        output = ""
        for item in self.content:
            if isinstance(item, str):
                output += item
            else:
                output += item.to_string()

        return output

    def _parameters_to_str(self):
        if not self.parameters:
            return ""

        parameters = []
        for key, value in self.parameters.items():
            if value:
                parameters.append(f"{key}={escape(value)}")
            else:
                parameters.append(f"{key}")

        return " " + " ".join(parameters)

    def depth_first_iterator(
        self, tags_only=False
    ) -> Iterator[Union["Tag", str, Comment]]:
        yield self

        for item in self.content:
            if isinstance(item, Tag):
                yield from item.depth_first_iterator(tags_only)
            elif not tags_only:
                yield item

    def breadth_first_iterator(
        self, tags_only=False, _first_call=True
    ) -> Iterator[Union["Tag", str, Comment]]:
        if _first_call:
            yield self

        if tags_only:
            for item in self.content:
                if isinstance(item, Tag):
                    yield item
        else:
            yield from self.content

        for item in self.content:
            if isinstance(item, Tag):
                yield from item.breadth_first_iterator(tags_only, False)

    def __repr__(self):
        parameters = (
            f"{repr(self.name)}",
            f"parameters={repr(self.parameters)}",
            f"nonpair={self.is_non_pair}",
        )

        return f"{self.__class__.__name__}({', '.join(parameters)})"

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False

        if self.name != other.name:
            return False

        if self.parameters != other.parameters:
            return False

        if self.is_non_pair != other.is_non_pair:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)
