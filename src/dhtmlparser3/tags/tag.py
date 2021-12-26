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

    @property
    def p(self):
        return self.parameters

    @property
    def c(self):
        return self.content
