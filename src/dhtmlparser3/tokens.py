class Token:
    def __ne__(self, other):
        return not self.__eq__(other)


class TextToken(Token):
    def __init__(self, content=""):
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, TextToken):
            return False

        if self.content != other.content:
            return False

        return True

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.content)})"


class TagToken(Token):
    def __init__(self, name="", parameters=None, nonpair=False, endtag=False):
        self.name = name
        self.parameters = [] if parameters is None else parameters
        self.nonpair = nonpair
        self.endtag = endtag

    def __eq__(self, other):
        if not isinstance(other, TagToken):
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

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({repr(self.name)}, "
            f"parameters={repr(self.parameters)}, "
            f"nonpair={self.nonpair})"
        )


class ParameterToken(Token):
    def __init__(self, key="", value=""):
        self.key = key
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, ParameterToken):
            return False

        if self.key != other.key:
            return False

        if self.value != other.value:
            return False

        return True

    def __repr__(self):
        return f"{self.__class__.__name__}(key={repr(self.key)}, value={repr(self.value)})"


class CommentToken(Token):
    def __init__(self, content=""):
        self.content = content

    def __eq__(self, other):
        if not isinstance(other, CommentToken):
            return False

        if self.content != other.content:
            return False

        return True

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.content)})"


class EntityToken(Token):
    NAMED_ENTITIES = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&nonbreakingspace;": u'\xa0',
        "&nbsp;": u'\xa0',
        "&quot;": '"',
        "&apos;": "'",
        "&cent;": "¢",
        "&pound;": "£",
        "&yen;": "¥",
        "&euro;": "€",
        "&copy;": "©",
        "&reg;": "®",
    }

    def __init__(self, content=""):
        self.content = content.lower()

    def to_text(self):
        representation = self.NAMED_ENTITIES.get(self.content)
        if representation:
            return representation

        if self.content.startswith("&#x"):
            return chr(int("0" + self.content[2:-1], 16))

        if self.content.startswith("&#"):
            return chr(int(self.content[2:-1]))

        return self.content

    def __eq__(self, other):
        if not isinstance(other, EntityToken):
            return False

        if self.content != other.content:
            return False

        return True

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.content)})"
