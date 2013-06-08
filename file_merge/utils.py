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
        if data is None:
            data = {}
        elif isinstance(data, GeneratorType):
            # Unfortunately we need to be able to read a generator twice.  Once
            # to get the data into self with our super().__init__ call and a
            # second time to setup key_sort_order correctly
            data = list(data)

        super(SortableDict, self).__init__(data)
        if isinstance(data, dict):
            self.key_sort_order = list(data.keys())
        else:
            self.key_sort_order = []
            seen = set()
            for key, value in data:
                if key not in seen:
                    self.key_sort_order.append(key)
                    seen.add(key)

    def __deepcopy__(self, memo):
        return self.__class__([(key, copy.deepcopy(value, memo))
                               for key, value in self.iteritems()])

    def __setitem__(self, key, value):
        if key not in self:
            self.key_sort_order.append(key)
        super(SortableDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(SortableDict, self).__delitem__(key)
        self.key_sort_order.remove(key)

    def __iter__(self):
        return iter(self.key_sort_order)

    def __reversed__(self):
        reversed(self.key_sort_order)

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

    def popitem(self):
        """
        Removes and returns the first item.
        """
        try:
            key = self.key_sort_order.pop()
            value = super(SortableDict, self).pop(key)
        except IndexError:
            return super(SortableDict, self).popitem()
        else:
            return (key, value)

    def items(self):
        return zip(self.key_sort_order, self.values())

    def iteritems(self):
        for key in self.key_sort_order:
            yield key, self[key]

    def keys(self):
        return self.key_sort_order[:]

    def iterkeys(self):
        return iter(self.key_sort_order)

    def values(self):
        return map(self.__getitem__, self.key_sort_order)

    def itervalues(self):
        for key in self.key_sort_order:
            yield self[key]

    def update(self, dict_):
        for k, v in dict_.iteritems():
            self[k] = v

    def setdefault(self, key, default):
        if key not in self:
            self.key_sort_order.append(key)
        return super(SortableDict, self).setdefault(key, default)

    def value_for_index(self, index):
        """Returns the value of the item at the given zero-based index."""
        return self[self.key_sort_order[index]]

    def insert(self, index, key, value):
        """Inserts the key, value pair before the item with the given index."""
        if key in self.key_sort_order:
            n = self.key_sort_order.index(key)
            del self.key_sort_order[n]
            if n < index:
                index -= 1
        self.key_sort_order.insert(index, key)
        super(SortableDict, self).__setitem__(key, value)

    def copy(self):
        """
        Returns a copy of this object.
        """
        # This way of initializing the copy means it works for subclasses, too.
        obj = self.__class__(self)
        obj.key_sort_order = self.key_sort_order[:]
        return obj

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
        Sorts the dictonary
        """
        self.key_sort_order.sort(*args, **kwargs)


def verbose(text, level=INFO):
    if level >= VERBOSE_LEVEL:
        print(text)
