from dhtmlparser3.specialdict import SpecialDict


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

    def __repr__(self):
        parameters = (
            f"{repr(self.name)}",
            f"parameters={repr(self.parameters)}",
            f"nonpair={self.is_non_pair}",
        )

        return f"{self.__class__.__name__}({', '.join(parameters)})"
