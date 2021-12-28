from dhtmlparser3.tokens import TagToken
from dhtmlparser3.tokens import TextToken
from dhtmlparser3.tokens import CommentToken
from dhtmlparser3.tokens import ParameterToken

from dhtmlparser3.tokenizer import Tokenizer


def test_entity_consumption():
    tokenizer = Tokenizer("&amp;")

    assert tokenizer.tokenize() == [TextToken("&")]


def test_text_consumption():
    tokenizer = Tokenizer("Some text.")

    assert tokenizer.tokenize() == [TextToken("Some text.")]


def test_text_and_entity_consumption():
    tokenizer = Tokenizer("&lt;Some text.&gt;")

    assert tokenizer.tokenize() == [
        TextToken("<Some text.>"),
    ]


def test_entity_mixup_consumption():
    tokenizer = Tokenizer("&entity Some text")

    assert tokenizer.tokenize() == [
        TextToken("&entity Some text"),
    ]


def test_long_entity():
    tokenizer = Tokenizer("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;")

    assert tokenizer.tokenize() == [
        TextToken("&" + ("a" * Tokenizer.MAX_ENTITY_LENGTH) + "a;"),
    ]


def test_possible_entity():
    tokenizer = Tokenizer("aaaa&a a;")

    assert tokenizer.tokenize() != [
        TextToken("aaaa"),
        TextToken("&a a;"),
    ]

    tokenizer = Tokenizer("aaaa&a a;")

    assert tokenizer.tokenize() == [TextToken("aaaa&a a;")]


def test_entity_at_the_end():
    tokenizer = Tokenizer("&a a")

    assert tokenizer.tokenize() == [
        TextToken("&a a"),
    ]


def test_comment():
    tokenizer = Tokenizer("aaa <!-- comment -->")

    assert tokenizer.tokenize() == [TextToken("aaa "), CommentToken(" comment ")]


def test_comment_without_end():
    tokenizer = Tokenizer("aaa <!-- comment ")

    assert tokenizer.tokenize() == [
        TextToken("aaa <!-- comment "),
    ]


def test_empty_tag():
    tokenizer = Tokenizer("<>")

    assert tokenizer.tokenize() == [TextToken("<>")]


def test_empty_tag_continuation():
    tokenizer = Tokenizer("<> ")

    assert tokenizer.tokenize() == [TextToken("<> ")]


def test_tag():
    tokenizer = Tokenizer("<tag>")

    assert tokenizer.tokenize() == [TagToken("tag")]


def test_tag_with_whitespaces_before_tag_name():
    tokenizer = Tokenizer("<  tag>")

    assert tokenizer.tokenize() == [TagToken("tag")]


def test_tag_with_whitespaces_after_tag_name():
    tokenizer = Tokenizer("<  tag  >")

    assert tokenizer.tokenize() == [TagToken("tag")]


def test_tag_with_nonpair_parameter():
    tokenizer = Tokenizer("<tag rectangle>")

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("rectangle", "")])
    ]


def test_tag_with_single_unquoted_parameter():
    tokenizer = Tokenizer("<tag key=value>")

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", "value")])
    ]


def test_tag_with_single_unquoted_parameter_spaces():
    tokenizer = Tokenizer("<  tag   key   =   value  >")

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", "value")])
    ]


def test_tag_with_single_quoted_parameter():
    tokenizer = Tokenizer("<tag key='value'>")

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", "value")])
    ]


def test_two_single_quoted_parameters():
    tokenizer = Tokenizer("<div ID='xa' a='b'>")

    assert tokenizer.tokenize() == [
        TagToken("div", parameters=[
            ParameterToken("ID", "xa"),
            ParameterToken("a", "b")
        ])
    ]


def test_tag_fail_recovery():
    tokenizer = Tokenizer("<tag key='value' <tag2>")

    assert tokenizer.tokenize() == [TextToken("<tag key='value' "), TagToken("tag2")]


def test_tag_with_double_quoted_parameter():
    tokenizer = Tokenizer('<tag key="value">')

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", "value")])
    ]


def test_tag_with_double_quoted_parameter_and_escape_seq():
    tokenizer = Tokenizer('<tag key="a \\" a">')

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", 'a " a')])
    ]


def test_tag_with_double_quoted_parameter_and_backslash():
    tokenizer = Tokenizer('<tag key="a \ a\\\\">')

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", "a \ a\\")])
    ]


def test_tag_with_double_quoted_parameter_and_multiple_escape_seq():
    tokenizer = Tokenizer('<tag key="a \\\\\\" a">')

    assert tokenizer.tokenize() == [
        TagToken("tag", parameters=[ParameterToken("key", 'a \\" a')])
    ]


def test_tag_with_multiple_parameters():
    tokenizer = Tokenizer(
        """<tag a=bbb asd = "bsd " @weird=parameters
                                   key='v a l' rect>"""
    )

    assert tokenizer.tokenize() == [
        TagToken(
            "tag",
            parameters=[
                ParameterToken("a", "bbb"),
                ParameterToken("asd", "bsd "),
                ParameterToken("@weird", "parameters"),
                ParameterToken("key", "v a l"),
                ParameterToken("rect", ""),
            ],
        )
    ]


def test_nonpair_tag():
    tokenizer = Tokenizer("<tag />")

    assert tokenizer.tokenize() == [TagToken("tag", is_non_pair=True)]


def test_nonpair_tag_parameters():
    tokenizer = Tokenizer("<tag param=val key='val' />")

    assert tokenizer.tokenize() == [
        TagToken(
            "tag",
            parameters=[
                ParameterToken("param", "val"),
                ParameterToken("key", "val"),
            ],
            is_non_pair=True,
        )
    ]


def test_end_tag():
    tokenizer = Tokenizer("</tag>")

    assert tokenizer.tokenize() == [TagToken("tag", is_end_tag=True)]


def test_split():
    tokenizer = Tokenizer("""<html><tag params="true"></html>""")

    assert tokenizer.tokenize() == [
        TagToken("html"),
        TagToken("tag", parameters=[ParameterToken("params", "true")]),
        TagToken("html", is_end_tag=True),
    ]


def test_mixing_of_entities():
    tokenizer = Tokenizer("""<html>aaa&amp;aaa<tag params="true">&lt;</html>""")

    assert tokenizer.tokenize() == [
        TagToken("html"),
        TextToken("aaa&aaa"),
        TagToken("tag", parameters=[ParameterToken("params", "true")]),
        TextToken("<"),
        TagToken("html", is_end_tag=True),
    ]


def test_split_text():
    tokenizer = Tokenizer("""   <html>asd asd"as das</html>   """)

    assert tokenizer.tokenize() == [
        TextToken("   "),
        TagToken("html"),
        TextToken('asd asd"as das'),
        TagToken("html", is_end_tag=True),
        TextToken("   "),
    ]


def test_parameters():
    tokenizer = Tokenizer("""<html><tag params="<html_tag>"></html>""")

    assert tokenizer.tokenize() == [
        TagToken("html"),
        TagToken("tag", parameters=[ParameterToken("params", "<html_tag>")]),
        TagToken("html", is_end_tag=True),
    ]


def test_parameters_quotes():
    tokenizer = Tokenizer("""<html><tag params="some \\"<quoted>\\" text"></html>""")

    assert tokenizer.tokenize() == [
        TagToken("html"),
        TagToken("tag", parameters=[ParameterToken("params", 'some "<quoted>" text')]),
        TagToken("html", is_end_tag=True),
    ]


def test_nested_comments():
    tokenizer = Tokenizer("""<html><!-- asd " asd" > asd --></html>""")

    assert tokenizer.tokenize() == [
        TagToken("html"),
        CommentToken(' asd " asd" > asd '),
        TagToken("html", is_end_tag=True),
    ]


def test_multiline_attribute():
    tokenizer = Tokenizer(
        """<ubertag attribute="long attribute
                               continues here">"""
    )

    tokens = tokenizer.tokenize()

    assert len(tokens) == 1
    assert tokens[0].name == "ubertag"
    assert tokens[0].parameters[0].key == "attribute"
    assert (
        tokens[0].parameters[0].value
        == """long attribute
                               continues here"""
    )


def test_recovery_from_invalid_quote():
    tokenizer = Tokenizer("""<invalid tag=something">notice""")

    assert tokenizer.tokenize() == [
        TagToken("invalid", parameters=[ParameterToken("tag", "something")]),
        TextToken("notice"),
    ]


def test_recovery_from_unclosed_tag():
    tokenizer = Tokenizer("""<code>Bla</code <tag>""")

    assert tokenizer.tokenize() == [
        TagToken("code"),
        TextToken("Bla</code "),
        TagToken("tag"),
    ]


def test_recovery_from_another_unclosed_tag():
    tokenizer = Tokenizer("""<code>Bla</code\n<!-- -->""")

    assert tokenizer.tokenize() == [
        TagToken("code"),
        TextToken("Bla</code\n"),
        CommentToken(" "),
    ]
