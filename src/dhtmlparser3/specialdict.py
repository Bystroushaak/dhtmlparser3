from collections import OrderedDict


def _lower_if_str(item):
    """
    Try to convert item to lowercase, if it is string.

    Args:
        item (obj): Str, unicode or any other object.

    Returns:
        obj: ``item.lower()`` if `item` is ``str`` or ``unicode``, else just \
             `item` itself.
    """
    if isinstance(item, str):
        return item.lower()

    return item


class SpecialDict(OrderedDict):
    """
    This dictionary stores items case sensitive, but compare them case
    INsensitive.
    """
    def __init__(self, *args, **kwargs):
        # lower_key -> key mapping
        self._case_mapping = OrderedDict()
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        lower_key = _lower_if_str(key)

        # remove the old key with (possibly) different case
        if lower_key in self._case_mapping:
            original_key = self._case_mapping[lower_key]
            super().__delitem__(original_key)

        self._case_mapping[lower_key] = key

        super().__setitem__(key, value)

    def __getitem__(self, key):
        lower_key = _lower_if_str(key)

        if lower_key not in self._case_mapping:
            raise KeyError(repr(key))

        return super().__getitem__(self._case_mapping[lower_key])

    def __delitem__(self, key):
        lower_key = _lower_if_str(key)
        key = self._case_mapping[lower_key]

        del self._case_mapping[lower_key]

        return super().__delitem__(key)

    def clear(self):
        self._case_mapping.clear()
        return super().clear()

    def get(self, k, d=None):
        lower_key = _lower_if_str(k)
        if lower_key not in self._case_mapping:
            return d

        return super().get(self._case_mapping[lower_key], d)

    def __contains__(self, key):
        lower_key = _lower_if_str(key)
        right_key = self._case_mapping.get(lower_key, None)

        return right_key and right_key in set(self.keys())

    def has_key(self, key):
        return key in self

    def __eq__(self, obj):
        if self is obj:
            return True

        if not hasattr(obj, "__getitem__"):
            return False

        keys = None
        if hasattr(obj, "keys"):
            keys = obj.keys()
        elif hasattr(obj, "iterkeys"):
            keys = list(obj.keys())
        else:
            keys = list(obj)

        if len(self.keys()) != len(keys):
            return False

        for key in keys:
            if not self.__contains__(key):
                return False

            if obj[key] != self.__getitem__(key):
                return False

        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    # python 2 / 3 compatibility
    def _is_py2(self):
        return hasattr(super(), "iteritems")

    def iteritems(self, *args, **kwargs):
        if self._is_py2():
            return super().iteritems(*args, **kwargs)

        return self.items()

    def iterkeys(self, *args, **kwargs):
        if self._is_py2():
            return super().iterkeys(*args, **kwargs)

        return self.keys()

    def itervalues(self, *args, **kwargs):
        if self._is_py2():
            return super().itervalues(*args, **kwargs)

        return self.values()

    def keys(self, *args, **kwargs):
        if not self._is_py2():
            return list(super().keys(*args, **kwargs))

        return super().keys(*args, **kwargs)

    def items(self, *args, **kwargs):
        if not self._is_py2():
            return list(super().items(*args, **kwargs))

        return super().items(*args, **kwargs)

    def values(self, *args, **kwargs):
        if not self._is_py2():
            return list(super().values(*args, **kwargs))

        return super().values(*args, **kwargs)

    def copy(self):
        new_dict = super().copy()
        new_dict._case_mapping = self._case_mapping.copy()
