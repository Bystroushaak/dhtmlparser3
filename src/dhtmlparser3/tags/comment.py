class Comment:
    def __init__(self, content=None):
        self.content = content

    def to_string(self):
        if self.content == " ":
            return "<!-- -->"

        return f"<!--{self.content}-->"

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False

        return self.content == other.content

    def __ne__(self, other):
        return not self.__eq__(other)
