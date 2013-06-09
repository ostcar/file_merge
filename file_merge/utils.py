"""
Utils for the file_merge module
"""

ERROR = 1
WARNING = 2
INFO = 3
DEVEL = 5
VERBOSE_LEVEL = INFO


class SortableDict(dict):
    """
    A dictonary that keeps its key in order in which they're inserted.

    The order can be resorted.

    Originaly taken from django.
    """

    def __init__(self, data=None):
        if data is None or isinstance(data, dict):
            data = data or []
            super(SortableDict, self).__init__(data)
            self.key_sort_order = list(data) if data else []
        else:
            super(SortableDict, self).__init__()
            super_set = super(SortableDict, self).__setitem__
            self.key_sort_order = []
            for key, value in data:
                # Take the ordering from first key
                if key not in self:
                    self.key_sort_order.append(key)
                # But override with last value in data (dict() does this)
                super_set(key, value)

    def __setitem__(self, key, value):
        if key not in self:
            self.key_sort_order.append(key)
        super(SortableDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(SortableDict, self).__delitem__(key)
        self.key_sort_order.remove(key)

    def __iter__(self):
        return iter(self.key_sort_order)

    def pop(self, k, *args):
        """
        Removes and returns a value.
        """
        result = super(SortableDict, self).pop(k, *args)
        try:
            self.key_sort_order.remove(k)
        except ValueError:
            # Key wasn't in the dictionary in the first place. No problem.
            pass
        return result

    def popitem(self, *args):
        """
        Removes and returns an item at a specific index (default last).
        """
        try:
            key = self.key_sort_order.pop(*args)
            value = super(SortableDict, self).pop(key)
        except IndexError:
            return super(SortableDict, self).popitem()
        else:
            return (key, value)

    def items(self):
        for key in self.key_sort_order:
            yield key, self[key]

    def keys(self):
        for key in self.key_sort_order:
            yield key

    def values(self):
        for key in self.key_sort_order:
            yield self[key]

    def update(self, dict_):
        for key, value in dict_.items():
            self[key] = value

    def setdefault(self, key, default):
        if key not in self:
            self.key_sort_order.append(key)
        return super(SortableDict, self).setdefault(key, default)

    def value_for_index(self, index):
        """
        Returns the value of the item at the given zero-based index.
        """
        return self[self.key_sort_order[index]]

    def __repr__(self):
        """
        Replaces the normal dict.__repr__ with a version that returns the keys
        in their sorted order.
        """
        return '{%s}' % ', '.join(['%r: %r' % (k, v) for k, v in self.items()])

    def clear(self):
        super(SortableDict, self).clear()
        self.key_sort_order = []

    def sort(self, *args, **kwargs):
        """
        Sorts the dictonary.
        """
        self.key_sort_order.sort(*args, **kwargs)


def verbose(text, level=INFO):
    if level >= VERBOSE_LEVEL:
        print(text)
