#!/usr/bin/env python3
import dhtmlparser3


s = """
<root>
    <object1>Content of first object</object1>
    <object2>Second objects content</object2>
</root>
"""

dom = dhtmlparser3.parse(s)

print(dom.prettify())
print("---")
print("Remove all `<object1>` tags:")
print()

# remove all <object1>
for e in dom.find("object1"):
    print(f"Removing {e.name}")
    dom.remove(e)

print()
print(dom.prettify())

"""
<root>
    <object1>Content of first object</object1>
    <object2>Second objects content</object2>
</root>

Remove all `<object1>`:

<root>
  <object2>Second objects content</object2>
</root>
"""