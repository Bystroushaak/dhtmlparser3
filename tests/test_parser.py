import pytest

import dhtmlparser3
from dhtmlparser3.tags.comment import Comment


def test_parse_simple_string():
    dom = dhtmlparser3.parse("""<html><tag PARAM="true"></html>""")

    assert dom.name == "html"
    assert dom.content
    assert len(dom.content) == 1

    assert dom.content[0].name == "tag"
    assert "PARAM" in dom.content[0].p
    assert dom.content[0].p["PARAM"] == "true"
    assert dom.content[0].p["param"] == "true"


def test_parse_simple_string_cip():
    dom = dhtmlparser3.parse(
        """<html><tag PARAM="true"></html>""",
        case_insensitive_parameters=False
    )

    assert dom.name == "html"
    assert dom.content
    assert len(dom.content) == 1

    assert dom.content[0].name == "tag"
    assert "PARAM" in dom.content[0].p
    assert dom.content[0].p["PARAM"] == "true"

    assert "param" not in dom.content[0].p

    with pytest.raises(KeyError):
         assert dom.content[0].p["param"]


def test_parse_single_quoted_params():
    dom = dhtmlparser3.parse("<div ID='xa' a='b'>")

    assert dom.name == "div"
    assert dom.p["ID"] == "xa"
    assert dom.p["a"] == "b"


def test_multiline_attribute():
    inp = """<sometag />
<ubertag attribute="long attribute
                    continues here">
    <valid>notice that quote is not properly started</valid>
</ubertag>
<something_parsable />
"""

    dom = dhtmlparser3.parse(inp)

    assert dom.c[0].name == "sometag"
    assert dom.c[0].is_non_pair

    assert dom.c[2].name == "ubertag"
    assert not dom.c[2].is_non_pair
    assert "attribute" in dom.c[2].p
    assert dom.c[2].p["ATTRIBUTE"] == """long attribute
                    continues here"""

    assert dom.c[2].c[1].name == "valid"
    assert not dom.c[2].c[1].is_non_pair
    assert dom.c[2].c[1].c[0] == "notice that quote is not properly started"

    assert dom.c[4].name == "something_parsable"
    assert dom.c[4].is_non_pair


def test_recovery_after_invalid_tag():
    inp = """<sometag />
<invalid tag=something">notice that quote is not properly started</invalid>
<something_parsable />
"""

    dom = dhtmlparser3.parse(inp)

    assert len(dom.content) == 6

    assert dom.content[0].name == "sometag"
    assert dom.content[0].is_non_pair

    assert dom.content[2].name == "invalid"
    assert dom.c[2].parameters == {"tag": "something"}
    assert dom.c[2].c[0] == "notice that quote is not properly started"
    assert not dom.content[2].is_non_pair

    assert dom.content[4].name == "something_parsable"
    assert dom.content[4].is_non_pair


def test_recovery_after_unclosed_tag():
    inp = """<code>Bla</code
<!-- -->

    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parse(inp)

    assert len(dom.c) == 6

    assert dom.name == ""
    assert dom.c[0].name == "code"
    assert dom.c[0].is_non_pair
    assert dom.c[1] == "Bla</code\n"
    assert dom.c[2] == Comment(" ")
    assert dom.c[4].name == "div"
    assert dom.c[4].p == {"class": "rating"}


def test_recovery_after_is_smaller_than_sign():
    inp = """<code>5 < 10.</code>
    <div class="rating">here is the rating</div>
    """

    dom = dhtmlparser3.parse(inp)

    assert dom.c[0].name == "code"
    assert dom.c[0].c[0] == "5 < 10."
    assert dom.c[2].name == "div"


def test_non_pair_structure():
    dom = dhtmlparser3.parse("""<div><br><img><hr></div>""")

    assert dom.name == "div"
    assert len(dom.c) == 3

    br = dom.c[0]
    assert br.name == "br"
    assert not br.content
    assert br.parent == dom

    img = dom.c[1]
    assert img.name == "img"
    assert not img.content
    assert img.parent == dom

    hr = dom.c[2]
    assert hr.name == "hr"
    assert not hr.content
    assert hr.parent == dom


def test_nonpair_closing():
    dom = dhtmlparser3.parse("""<div><br><img><hr>""")

    assert dom.name == ""
    assert len(dom.c) == 4

    div = dom.c[0]
    assert div.name == "div"
    assert not div.content

    br = dom.c[1]
    assert br.name == "br"
    assert not br.content
    assert br.parent == div.parent

    img = dom.c[2]
    assert img.name == "img"
    assert not img.content
    assert img.parent == div.parent

    hr = dom.c[3]
    assert hr.name == "hr"
    assert not hr.content
    assert hr.parent == div.parent


def test_correct_nonpair_behavior():
    dom = dhtmlparser3.parse("""<!DOCTYPE html>
<html>
<head>
  <meta name="generator" content="HTML Tidy for HTML5 for Linux version 5.6.0">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>Bystroushaak's blog</title>
  <link rel="stylesheet" type="text/css" href="style.css">
  <link rel="alternate" type="application/atom+xml" href="https://blog.rfox.eu/atom.xml">
  <link rel="shortcut icon" href="/favicon.ico">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@Bystroushaak">
  <script src="https://www.googletagmanager.com/gtag/js?id=UA-142545439-1"></script>
  <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
    
      gtag('config', 'UA-142545439-1');
  </script>
</head>
</html>""")

    assert dom.tags[1].name == "html"

    head = dom.tags[1].tags[0]
    assert head.name == "head"
    assert head.tags[0].name == "meta"
    assert head.tags[0].is_non_pair
    assert head.tags[1].name == "meta"
    assert head.tags[2].name == "title"
    assert head.tags[3].name == "link"
    assert head.tags[4].name == "link"
    assert head.tags[5].name == "link"
    assert head.tags[6].name == "meta"
    assert head.tags[7].name == "meta"
    assert head.tags[7].p["content"] == "@Bystroushaak"
    assert head.tags[8].name == "script"
    assert head.tags[8].p["src"] == "https://www.googletagmanager.com/gtag/js?id=UA-142545439-1"
    assert head.tags[9].name == "script"
