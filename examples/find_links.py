#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DHTMLParserPy example how to find every link in document.
"""

import urllib
import dhtmlparser3

f = urllib.urlopen("http://google.com")
data = f.read()
f.close()

dom = dhtmlparser3.parseString(data)

for link in dom.find("a"):
	if "href" in link.params:
		print link.params["href"]