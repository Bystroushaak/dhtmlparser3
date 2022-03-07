import html
import copy
from typing import Dict
from typing import List
from typing import Union
from typing import Iterator

from dhtmlparser3.quoter import escape
from dhtmlparser3.specialdict import SpecialDict
from dhtmlparser3.tags.comment import Comment


class Tag:
    """
    Attributes:
        name (str): Name of the parsed tag.
        parameters (SpecialDict): Dictionary for the parameters.
        content (list): List of sub-elements.
        parent (Tag): Reference to parent element.
    """
    _DICT_INSTANCE = SpecialDict
    _DONT_ESCAPE = {"style", "script"}
    _DONT_FORMAT = {"pre", "style", "script"}

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
        """
        Shortcut for .parameters, used extensively in tests.
        """
        return self.parameters

    @property
    def c(self):
        """
        Shortcut for .content, used extensively in tests.
        """
        return self.content

    @property
    def tags(self) -> List["Tag"]:
        """
        Same as .c, but returns only tag instances. Useful for ignoring
        whitespace and comment clutter and iterating over the real dom structure.
        """
        return [x for x in self.content if isinstance(x, Tag)]

    def double_link(self):
        """
        Make the DOM hierarchy double-linked. Each content element now points
        to the parent element.
        """
        for item in self.content:
            if isinstance(item, Tag):
                item.parent = self
                item.double_link()

    def content_without_tags(self) -> str:
        """
        Return content but remove all tags.

        This is sometimes useful for processing messy websites.
        """
        output = ""
        for item in self.content:
            if isinstance(item, Tag):
                output += item.content_without_tags()
            elif isinstance(item, str):
                output += item

        return output

    def remove(self, offending_item: Union[str, "Tag", Comment]) -> bool:
        """
        Remove `offending_item` anywhere from the dom.

        Item is matched using `is` operator, so it better be something you've
        found using .find() or other relevant methods.

        Returns:
            bool: True if the item was found and removed.
        """
        for item in self.content:
            if item is offending_item:
                self.remove_item(offending_item)
                return True

            if isinstance(item, Tag) and item.remove(offending_item):
                return True

        return False

    def remove_item(self, item: Union[str, "Tag", Comment]):
        """
        Remove the item from the .content property.

        If the `item` is Tag instance, match it using tag name and parameters.
        """
        if isinstance(item, str):
            self.content.remove(item)
        elif isinstance(item, Comment):
            self.content = [
                x
                for x in self.content
                if not (isinstance(x, Comment) and x.content == item.content)
            ]
        elif isinstance(item, Tag):
            self.content = [
                x
                for x in self.content
                if not (
                    isinstance(x, Tag)
                    and x._is_almost_equal(item.name, item.parameters)
                )
            ]
        else:
            raise ValueError(f"Can't remove `{repr(item)}`")

    def to_string(self) -> str:
        """
        Get HTML representation of the tag and the content.
        """
        output = self.tag_to_str()

        escape_fn = html.escape
        if self.name in self._DONT_ESCAPE:
            escape_fn = lambda x: x

        for item in self.content:
            if isinstance(item, str):
                output += escape_fn(item)
            else:
                output += item.to_string()

        if self.name and not self.is_non_pair:
            return f"{output}</{self.name}>"

        return output

    def tag_to_str(self) -> str:
        """
        Convert just the tag with parameters to string, without content.
        """
        if not self.name:
            return ""

        if self.is_non_pair:
            return f"<{self.name}{self._parameters_to_str()} />"

        return f"<{self.name}{self._parameters_to_str()}>"

    def _parameters_to_str(self) -> str:
        if not self.parameters:
            return ""

        parameters = []
        for key, value in self.parameters.items():
            if value:
                parameters.append(f'{key}="{escape(str(value))}"')
            else:
                parameters.append(f"{key}")

        return " " + " ".join(parameters)

    def content_str(self) -> str:
        """
        Return everything in between the tags as string.
        """
        output = ""
        for item in self.content:
            if isinstance(item, str):
                output += item
            else:
                output += item.to_string()

        return output

    def replace_with(self, item: "Tag", keep_content: bool = False):
        """
        Replace this Tag with another `item`.

        Args:
            item (Tag, str): Item to replace this with.
            keep_content (bool): Keep the original content. Default `False`.
        """
        if isinstance(item, str):
            unused_root_element = self.parent.name == "" and len(self.parent.content) == 1
            if self.parent and not unused_root_element:
                self_index = self.parent.content.index(self)
                self.parent.content[self_index] = item
            else:
                self.name = ""
                self.parameters.clear()
                self.is_non_pair = True
                self.content = [item]
        elif isinstance(item, Tag):
            self.name = item.name
            self.parameters = item.parameters.copy()
            if not keep_content:
                self.content = item.content[:]
            self.is_non_pair = item.is_non_pair
            self._wfind_only_on_content = item._wfind_only_on_content
        else:
            raise TypeError(f"Can't replace `item` with `{item.__class__}`!")

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
        """
        Recursively call `find` for each element in `*args`. That means fuzzy
        matching, like "find all `<div>`s, which have this `<p>` element, which
        has this `<a>` in it.

        Example:
            dom.match("div", ["p", {"class": "great"}], "a")

        Args:
            *args (list): List of paths to match.

        Returns:
            list: List of matched elements.
        """
        item = self
        args = list(args)

        arg = args.pop(0)
        matched = self._call_find(arg)

        if not args:
            return matched

        next_matched = []
        while args:
            arg = args.pop(0)
            for item in matched:
                next_matched.extend(item._call_find(arg))

            matched = next_matched
            next_matched = []

        return matched

    def _call_find(self, arg):
        if isinstance(arg, dict):
            return self.find(**arg)
        elif isinstance(arg, list) or isinstance(arg, tuple):
            return self.find(*arg)
        else:
            return self.find(arg)

    def match_paths(self, *args):
        """
        Exactly match the path given by the arguments.

        Example:
            dom.match("body", ["div", {"class": "page-body"}], "p")

        This will match the path only if it really goes like this. If the `<p>`
        is for example wrapped in <div>, it won't be matched.

        Args:
            *args (list): List of paths to match.

        Returns:
            list: List of matched elements.
        """
        item = self
        args = list(args)
        while args:
            arg = args.pop(0)
            item = item._call_wfind(arg)

        return item.content

    def _call_wfind(self, arg):
        if isinstance(arg, dict):
            return self.wfind(**arg)
        elif isinstance(arg, list) or isinstance(arg, tuple):
            return self.wfind(*arg)
        else:
            return self.wfind(arg)

    def find(self, name, p=None, fn=None, case_sensitive=False) -> List["Tag"]:
        """
        Find (depth first) all tags with given parameters.

        Args:
            name (str): Name of the tag you are looking for. Use `""` for all.
            p (dict): Parameters to match.
            fn (lambda fn): Lambda expecting one argument.
             It will be tested for each element in the tree.
            case_sensitive (bool): Use case sensitive search. Default `False`.
        """
        return list(self.find_depth_first_iter(name, p, fn, case_sensitive))

    def findb(self, name, p=None, fn=None, case_sensitive=False) -> List["Tag"]:
        """
        Find (breadth first) all tags with given parameters.

        Args:
            name (str): Name of the tag you are looking for. Use `""` for all.
            p (dict): Parameters to match.
            fn (lambda fn): Lambda expecting one argument.
             It will be tested for each element in the tree.
            case_sensitive (bool): Use case sensitive search. Default `False`.
        """
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
        self, other_name: str, p: dict = None, fn=None, case_sensitive=False
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
            if not self.parameters or key not in self.parameters:
                return False

            if val != self.parameters[key]:
                return False

        return True

    def prettify(self, depth=0, dont_format=False) -> str:
        if self.name == "":
            return self._just_prettify_the_content()

        tag = self.tag_to_str()
        indent = depth * "  "

        if self.is_non_pair and not self.content:
            return f"{indent}{tag}\n"

        end_tag = "" if self.is_non_pair else f"</{self.name}>"

        if not dont_format and self.name in self._DONT_FORMAT:
            dont_format = True

        escape_fn = html.escape
        if self.name in self._DONT_ESCAPE:
            escape_fn = lambda x: x

        content = ""
        for item in self.content:
            if isinstance(item, str):
                if dont_format or item.strip():
                    content += escape_fn(item)
            else:
                content += item.prettify(depth + 1, dont_format=dont_format)

        if dont_format:
            return f"{tag}{content}{end_tag}\n"

        is_multiline = sum(1 for x in content.strip() if x == "\n") > 1
        if is_multiline:
            if content.endswith("\n"):
                return f"{indent}{tag}\n{content}{indent}{end_tag}\n"

            return f"{indent}{tag}\n{content}\n{indent}{end_tag}\n"

        if content.startswith("  ") and content.endswith("\n"):
            return f"{indent}{tag}\n{content}{indent}{end_tag}\n"

        return f"{indent}{tag}{content}{end_tag}\n"

    def _just_prettify_the_content(self):
        outputs = []

        escape_fn = html.escape
        if self.name in self._DONT_ESCAPE:
            escape_fn = lambda x: x

        for item in self.content:
            if isinstance(item, str):
                if item.strip():
                    outputs.append(escape_fn(item))
            else:
                outputs.append(item.prettify(0))

        return "\n".join(outputs)

    def __str__(self) -> str:
        return self.to_string()

    def __bytes__(self) -> bytes:
        return self.to_string().encode("utf-8")

    def __repr__(self) -> str:
        parameters = (
            f"{repr(self.name)}",
            f"parameters={repr(self.parameters)}",
            f"is_non_pair={self.is_non_pair}",
        )
        if self._wfind_only_on_content:
            parameters = (
                'name=""',
                f'content={repr(self.content)}'
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

    def __hash__(self):
        rolling_hash = hash(self.tag_to_str())

        for item in self.content:
            rolling_hash ^= hash(item)

        return rolling_hash

    def __bool__(self):
        return bool(self.content)

    def __len__(self):
        return len(self.tags)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.parameters[item]
        else:
            return self.tags[item]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.parameters[key] = str(value)
        elif isinstance(key, slice):  # used for inserting
            if key.start == -1:
                self.content.append(value)
            elif key.start == 0:
                self.content.insert(0, value)
            else:
                # use .tags as reference
                item = self.tags[key.start]
                index = self.content.index(item)
                self.content.insert(index, value)
        else:
            item = self.tags[key]
            index = self.content.index(item)
            self.content[index] = value

        if isinstance(value, Tag):
            value.parent = self

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.parameters
        else:
            return item in self.content

    def __delitem__(self, key):
        if isinstance(key, str):
            del self.parameters[key]
        else:
            self.remove_item(self.tags[key])

    def __iter__(self):
        return iter(self.tags)

    def __copy__(self):
        new_tag = Tag(self.name, self.parameters.copy(), self.content, self.is_non_pair)
        new_tag._wfind_only_on_content = self._wfind_only_on_content
        new_tag.parent = self.parent

        return new_tag

    def __deepcopy__(self, memodict={}):
        new_tag = Tag(self.name, self.parameters.copy(), is_non_pair=self.is_non_pair)
        new_tag._wfind_only_on_content = self._wfind_only_on_content
        new_tag.parent = self.parent

        new_tag.content = [
            copy.deepcopy(x, memodict)
            for x in self.content
        ]

        return new_tag
