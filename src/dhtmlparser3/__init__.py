from dhtmlparser3 import specialdict

from dhtmlparser3.tags.tag import Tag
from dhtmlparser3.tags.comment import Comment

from dhtmlparser3.parser import Parser


class FileParser:
    def __init__(self, path: str, case_insensitive_parameters=True):
        self.path = path

        with open(path) as f:
            self.dom = parse(f.read())

    def write(self, path: str = None):
        if path is None:
            path = self.path

        with open(path, "w") as f:
            f.write(str(self.dom))


def parse(string: str, case_insensitive_parameters=True):
    parser = Parser(string, case_insensitive_parameters)
    return parser.parse_dom()


def parse_file(path: str, case_insensitive_parameters=True):
    return FileParser(path, case_insensitive_parameters)
