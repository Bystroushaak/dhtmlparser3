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


class Element:
    def __init__(self, name=""):
        self.name = name
        self.parameters = []

    def __eq__(self, other):
        if not isinstance(other, Element):
            return False

        if self.name != other.name:
            return False

        if self.parameters != other.parameters:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Element({repr(self.name)}, parameters={self.parameters})"


class Parameter:
    def __init__(self, key="", value=""):
        self.key = key
        self.value = value


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