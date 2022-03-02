"""
This module provides ability to quote and unquote strings using backslash
notation.
"""

def escape(inp):
    """
    Escape `quote` in string `inp`.

    Example usage::

        >>> escape('hello "')
        'hello &quot;'

    Args:
        inp (str): String in which `quote` will be escaped.

    Returns:
        str: Escaped string.
    """
    output = ""

    for c in inp:
        if c == '"':
            output += '&quot;'
            continue

        output += c

    return output
