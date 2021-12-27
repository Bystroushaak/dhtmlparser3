import dhtmlparser3


def test_equality_of_output_with_comment():
    inp = """<head>
    <!-- <link rel="stylesheet" type="text/css" href="style.css"> -->
</head>
"""
    dom = dhtmlparser3.parse(inp)

    assert dom.to_string() == inp
