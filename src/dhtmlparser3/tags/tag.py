from typing import Union
from typing import Iterator

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

        self._wfind_only_on_content = False

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

        if self.name and not self.is_non_pair:
            return f"{output}</{self.name}>"

        return output

    def tag_to_str(self):
        if not self.name:
            return ""

        if self.is_non_pair:
            return f"<{self.name}{self._parameters_to_str()} />"

        return f"<{self.name}{self._parameters_to_str()}>"

    def _parameters_to_str(self):
        if not self.parameters:
            return ""

        parameters = []
        for key, value in self.parameters.items():
            if value:
                parameters.append(f'{key}="{escape(value)}"')
            else:
                parameters.append(f"{key}")

        return " " + " ".join(parameters)

    def content_str(self):
        output = ""
        for item in self.content:
            if isinstance(item, str):
                output += item
            else:
                output += item.to_string()

        return output

    def wfind(self, name, p=None, fn=None, case_sensitive=False):
        container = Tag(name="")
        container._wfind_only_on_content = True

        # in the first iteration, just do regular find
        if not self._wfind_only_on_content:
            container.content = self.find(name, p, fn, case_sensitive)
            return container

        # in the subsequent iterations, perform the matching on the sub-tags
        sub_tags = (item.content for item in self.content)
        for item in sum(sub_tags, []):  # flattern the list
            if isinstance(item, Tag):
                if item._is_almost_equal(name, p, fn, case_sensitive):
                    container.content.append(item)

        return container

    def find(self, name, p=None, fn=None, case_sensitive=False):
        return list(self.find_depth_first_iter(name, p, fn, case_sensitive))

    def findb(self, name, p=None, fn=None, case_sensitive=False):
        return list(self.find_breadth_first_iter(name, p, fn, case_sensitive))

    def find_depth_first_iter(self, name, p=None, fn=None, case_sensitive=False):
        for item in self.depth_first_iterator(tags_only=True):
            if item._is_almost_equal(name, p, fn, case_sensitive):
                yield item

    def find_breadth_first_iter(self, name, p=None, fn=None, case_sensitive=False):
        for item in self.breadth_first_iterator(tags_only=True):
            if item._is_almost_equal(name, p, fn, case_sensitive):
                yield item

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

    def _is_almost_equal(self, other_name, p=None, fn=None, case_sensitive=False):
        tag_name = self.name
        if not case_sensitive:
            tag_name = tag_name.lower()
            other_name = other_name.lower()

        if other_name and tag_name != other_name:
            return False

        if p is not None and not self._contains_parameters_subset(p):
            return False

        if fn is not None and not fn(self):
            return False

        return True

    def _contains_parameters_subset(self, parameter_subset):
        """
        Test whether this Tag contains at least all `parameter_subset`, key
        and values, or more.

        Args:
            params (dict/SpecialDict): Subset of parameters.

        Returns:
            bool: True if it is contained.
        """
        for key, val in parameter_subset.items():
            if key not in self.parameters:
                return False

            if val != self.parameters[key]:
                return False

        return True

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
