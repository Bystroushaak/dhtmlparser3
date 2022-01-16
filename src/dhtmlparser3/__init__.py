from dhtmlparser3 import specialdict

from dhtmlparser3.tags.tag import Tag
from dhtmlparser3.tags.comment import Comment

from dhtmlparser3.parser import Parser


def parse(string: str, case_insensitive_parameters=True):
    parser = Parser(string, case_insensitive_parameters)
    return parser.parse_dom()
