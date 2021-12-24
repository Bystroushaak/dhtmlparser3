from dhtmlparser3.tokens import Tag
from dhtmlparser3.tokens import Text
from dhtmlparser3.tokens import Entity
from dhtmlparser3.tokens import Comment
from dhtmlparser3.tokens import Parameter

from dhtmlparser3.tokenizer import Tokenizer


def test_entity_consumption():
    tokenizer = Tokenizer("&nbsp;")

    assert tokenizer.tokenize() == [Entity("&nbsp;")]


def test_text_consumption():
    tokenizer = Tokenizer("Some text.")

    assert tokenizer.tokenize() == [Text("Some text.")]


def test_text_and_entity_consumption():
    tokenizer = Tokenizer("&entity;Some text.&entity2;")

    assert tokenizer.tokenize() == [
        Entity("&entity;"),
        Text("Some text."),
        Entity("&entity2;"),
    ]


def test_entity_mixup_consumption():
    tokenizer = Tokenizer("&entity Some text")

    assert tokenizer.tokenize() == [
        Text("&entity Some text"),
    ]


def test_long_entity():
    tokenizer = Tokenizer("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;")

    assert tokenizer.tokenize() == [
        Text("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;"),
    ]


def test_possible_entity():
    tokenizer = Tokenizer("aaaa&a a;")

    assert tokenizer.tokenize() != [
        Text("aaaa"),
        Text("&a a;"),
    ]

    assert tokenizer.tokens == [Text("aaaa&a a;")]


def test_entity_at_the_end():
    tokenizer = Tokenizer("&a a")

    assert tokenizer.tokenize() == [
        Text("&a a"),
    ]


def test_comment():
    tokenizer = Tokenizer("aaa <!-- comment -->")

    assert tokenizer.tokenize() == [Text("aaa "), Comment(" comment ")]


def test_comment_without_end():
    tokenizer = Tokenizer("aaa <!-- comment ")

    assert tokenizer.tokenize() == [
        Text("aaa <!-- comment "),
    ]


def test_empty_tag():
    tokenizer = Tokenizer("<>")

    assert tokenizer.tokenize() == [Text("<>")]


def test_empty_tag_continuation():
    tokenizer = Tokenizer("<> ")

    assert tokenizer.tokenize() == [Text("<> ")]


def test_tag():
    tokenizer = Tokenizer("<tag>")

    assert tokenizer.tokenize() == [Tag("tag")]


def test_tag_with_whitespaces_before_tag_name():
    tokenizer = Tokenizer("<  tag>")

    assert tokenizer.tokenize() == [Tag("tag")]


def test_tag_with_whitespaces_after_tag_name():
    tokenizer = Tokenizer("<  tag  >")

    assert tokenizer.tokenize() == [Tag("tag")]


def test_tag_with_nonpair_parameter():
    tokenizer = Tokenizer("<tag rectangle>")

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("rectangle", "")])]


def test_tag_with_single_unquoted_parameter():
    tokenizer = Tokenizer("<tag key=value>")

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("key", "value")])]


def test_tag_with_single_unquoted_parameter_spaces():
    tokenizer = Tokenizer("<  tag   key   =   value  >")

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("key", "value")])]


def test_tag_with_single_quoted_parameter():
    tokenizer = Tokenizer("<tag key='value'>")

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("key", "value")])]


def test_tag_with_double_quoted_parameter():
    tokenizer = Tokenizer('<tag key="value">')

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("key", "value")])]


def test_tag_with_double_quoted_parameter_and_escape_seq():
    tokenizer = Tokenizer('<tag key="a \\" a">')

    assert tokenizer.tokenize() == [Tag("tag", parameters=[Parameter("key", 'a " a')])]


def test_tag_with_double_quoted_parameter_and_backslash():
    tokenizer = Tokenizer('<tag key="a \ a\\\\">')

    assert tokenizer.tokenize() == [
        Tag("tag", parameters=[Parameter("key", "a \ a\\")])
    ]


def test_tag_with_double_quoted_parameter_and_multiple_escape_seq():
    tokenizer = Tokenizer('<tag key="a \\\\\\" a">')

    assert tokenizer.tokenize() == [
        Tag("tag", parameters=[Parameter("key", 'a \\" a')])
    ]


def test_tag_with_multiple_parameters():
    tokenizer = Tokenizer(
        """<tag a=bbb asd = "bsd " @weird=parameters
                                   key='v a l' rect>"""
    )

    assert tokenizer.tokenize() == [
        Tag(
            "tag",
            parameters=[
                Parameter("a", "bbb"),
                Parameter("asd", "bsd "),
                Parameter("@weird", "parameters"),
                Parameter("key", "v a l"),
                Parameter("rect", ""),
            ],
        )
    ]


def test_nonpair_tag():
    tokenizer = Tokenizer("<tag />")

    assert tokenizer.tokenize() == [Tag("tag", nonpair=True)]


def test_nonpair_tag_parameters():
    tokenizer = Tokenizer("<tag param=val key='val' />")

    assert tokenizer.tokenize() == [
        Tag(
            "tag",
            parameters=[
                Parameter("param", "val"),
                Parameter("key", "val"),
            ],
            nonpair=True,
        )
    ]


def test_end_tag():
    tokenizer = Tokenizer("</tag>")

    assert tokenizer.tokenize() == [Tag("tag", endtag=True)]


def test_raw_split():
    tokenizer = Tokenizer("""<html><tag params="true"></html>""")

    assert tokenizer.tokenize() == [
        Tag("html"),
        Tag("tag", parameters=[Parameter("params", "true")]),
        Tag("html", endtag=True),
    ]


# + recovery
# + &entities; mixed with tags & text
# + fail recovery on <tag asd = ""   <tag2> ..


def test_raw_split_text():
    tokenizer = Tokenizer("""   <html>asd asd"as das</html>   """)

    assert tokenizer.tokenize() == [
        Text("   "),
        Tag("html"),
        Text('asd asd"as das'),
        Tag("html", endtag=True),
        Text("   "),
    ]


def test_raw_split_parameters():
    tokenizer = Tokenizer("""<html><tag params="<html_tag>"></html>""")

    assert tokenizer.tokenize() == [
        Tag("html"),
        Tag("tag", parameters=[Parameter("params", "<html_tag>")]),
        Tag("html", endtag=True),
    ]


def test_raw_split_parameters_quotes():
    tokenizer = Tokenizer("""<html><tag params="some \\"<quoted>\\" text"></html>""")

    assert tokenizer.tokenize() == [
        Tag("html"),
        Tag("tag", parameters=[Parameter("params", 'some "<quoted>" text')]),
        Tag("html", endtag=True),
    ]


def test_raw_split_comments():
    tokenizer = Tokenizer("""<html><!-- asd " asd" > asd --></html>""")

    assert tokenizer.tokenize() == [
        Tag("html"),
        Comment(' asd " asd" > asd '),
        Tag("html", endtag=True),
    ]
