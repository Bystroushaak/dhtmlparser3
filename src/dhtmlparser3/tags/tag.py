from typing import Dict
from typing import List
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
    def p(self) -> Dict[str, str]:
        return self.parameters

    @property
    def c(self):
        return self.content

    @property
    def tags(self) -> List["Tag"]:
        return [x for x in self.content if isinstance(x, Tag)]

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

    def remove_item(self, stuff):
        if isinstance(stuff, str):
            self.content.remove(stuff)
        elif isinstance(stuff, Comment):
            self.content = [
                item
                for item in self.content
                if not (isinstance(item, Comment) and item.content == stuff.content)
            ]
        elif isinstance(stuff, Tag):
            self.content = [
                item
                for item in self.content
                if not (
                    isinstance(item, Tag)
                    and stuff._is_almost_equal(stuff.name, stuff.parameters)
                )
            ]
        else:
            raise ValueError(f"Can't remove `{repr(stuff)}`")

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

    def replace_with(self, item):
        if not isinstance(item, Tag):
            raise TypeError(f"Can't replace `item` with `{item.__class__}`!")

        self.name = item.name
        self.parameters = item.parameters.copy()
        self.content = item.content[:]
        self.is_non_pair = item.is_non_pair
        self._wfind_only_on_content = item._wfind_only_on_content

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

    def match(self, *args):
        item = self
        args = list(args)
        while args:
            arg = args.pop(0)
            if isinstance(arg, dict):
                item = item.wfind(**arg)
            elif isinstance(arg, list) or isinstance(arg, tuple):
                item = item.wfind(*arg)
            else:
                item = item.wfind(arg)

        return item.content

    def find(self, name, p=None, fn=None, case_sensitive=False) -> List["Tag"]:
        return list(self.find_depth_first_iter(name, p, fn, case_sensitive))

    def findb(self, name, p=None, fn=None, case_sensitive=False) -> List["Tag"]:
        return list(self.find_breadth_first_iter(name, p, fn, case_sensitive))

    def find_depth_first_iter(
        self, name, p=None, fn=None, case_sensitive=False
    ) -> Iterator["Tag"]:
        for item in self.depth_first_iterator(tags_only=True):
            if item._is_almost_equal(name, p, fn, case_sensitive):
                yield item

    def find_breadth_first_iter(
        self, name, p=None, fn=None, case_sensitive=False
    ) -> Iterator["Tag"]:
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

    def _is_almost_equal(
        self, other_name, p=None, fn=None, case_sensitive=False
    ) -> bool:
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

    def prettify(self, depth=0, dont_format=False):
        tag = self.tag_to_str()
        indent = depth * "  "

        if self.is_non_pair and not self.content:
            return f"{indent}{tag}\n"

        end_tag = "" if self.is_non_pair else f"</{self.name}>"

        if not dont_format and self.name in {"pre", "style", "script"}:
            dont_format = True

        content = ""
        for item in self.content:
            if isinstance(item, str):
                content += item
            else:
                content += item.prettify(depth + 1, dont_format=dont_format)

        if dont_format:
            return f"{tag}{content}{end_tag}\n"

        is_multiline = sum(1 for x in content.strip() if x == "\n") > 1
        if is_multiline:
            if content.endswith("\n"):
                return f"{indent}{tag}\n{content}{indent}{end_tag}\n"

            return f"{indent}{tag}\n{content}\n{indent}{end_tag}\n"

        return f"{indent}{tag}{content}{end_tag}\n"

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
