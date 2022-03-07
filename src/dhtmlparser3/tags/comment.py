class Comment:
    def __init__(self, content=None):
        self.content = content

    def to_string(self):
        if not self.content.strip():
            return "<!-- -->"

        return f"<!--{self.content}-->"

    def prettify(self, depth, dont_format=False):
        if dont_format:
            return self.to_string()

        return f"{depth * '  '}{self.to_string()}"

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False

        return self.content == other.content

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return Comment(self.content)

    def __deepcopy__(self, memodict={}):
        return Comment(self.content)
