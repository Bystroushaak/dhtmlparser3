class Text:
    def __init__(self, content=""):
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, Text):
            return False

        if self.content != other.content:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Text({repr(self.content)})"


class Tag:
    def __init__(self, name="", parameters=None, nonpair=False, endtag=False):
        self.name = name
        self.parameters = [] if parameters is None else parameters
        self.nonpair = nonpair
        self.endtag = endtag

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False

        if self.name != other.name:
            return False

        if self.nonpair != other.nonpair:
            return False

        if self.endtag != other.endtag:
            return False

        if len(self.parameters) != len(other.parameters):
            return False

        for my_param, other_param in zip(self.parameters, other.parameters):
            if my_param != other_param:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return (
            f"Element({repr(self.name)}, parameters={repr(self.parameters)}, "
            f"nonpair={self.nonpair})"
        )


class Parameter:
    def __init__(self, key="", value=""):
        self.key = key
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return False

        if self.key != other.key:
            return False

        if self.value != other.value:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Parameter(key={repr(self.key)}, value={repr(self.value)})"


class Comment:
    def __init__(self, content=""):
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False

        if self.content != other.content:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Comment({repr(self.content)})"


class Entity:
    def __init__(self, content=""):
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False

        if self.content != other.content:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Entity({repr(self.content)})"