#!/usr/bin/env python3
"""
dhtmlparser3 DOM creation example.
"""
from dhtmlparser3 import Tag
from dhtmlparser3 import Comment


e = Tag("root", content=[
    Tag("item", {"param1":"1", "param2":"2"}, [
        Tag("crap", content=[
            "hello parser!"
        ]),
        Tag("another_crap", {"with" : "params"}, is_non_pair=True),
        Comment(" comment ")
    ]),
    Tag("item", {"blank" : "body"}, is_non_pair=True)
])

# print(e.to_string())
print(e.prettify())

"""
Writes:

<root>
  <item param2="2" param1="1">
    <crap>hello parser!</crap>
    <another_crap with="params" />
    <!-- comment -->
  </item>
  <item blank="body" />
</root>
"""
