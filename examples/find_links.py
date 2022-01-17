#!/usr/bin/env python3
"""
DHTMLParserPy example how to find every link in document.
"""
import urllib.request

import dhtmlparser3


with urllib.request.urlopen("http://blog.rfox.eu") as resp:
    data = resp.read().decode("utf-8")

dom = dhtmlparser3.parse(data)
for link in dom.find("a"):
    if "href" in link.p:
        print(link.p["href"])

print(dom)