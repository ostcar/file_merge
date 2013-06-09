import os
import hashlib
import stat

from .utils import SortableDict, verbose, INFO, DEVEL, WARNING, ERROR


class INodeFile(object):
    """
    An file object with referce to an inode and not to an path.

    More then one path to the file can be saved in a INodeFile-object.

    Attributes
    ----------
    inode: The inode of the files
    files: a list of all hardlinks to this file
    md5sum: the md5sum of the file
    sha1sum: the sha1sum of the file
    size: the size of the file
    """
    def __init__(self, firstfile):
        """
        firstfile: The absolut path to a file.
        """
        if not '\0' in firstfile:
            stat = os.lstat(firstfile)
            self.inode = stat.st_ino
            self.size = stat.st_size
            self.files = set()
            self.addfile(firstfile)
        else:
            # Load a INodeFile-object from a string.
            data = firstfile.split('\0')
            self.inode = int(data[0])
            self.size = int(data[1])
            if data[2]:
                self._prefix_md5sum = data[2]
            if data[3]:
                self._md5sum = data[3]
            if data[4]:
                self._sha1sum = data[4]
            self.files = set(data[5:])
        self.merged_into = None

    def __hash__(self):
        """
        The hash of this object is the inode from the file.

        This ensures, that there can only be one INodeFile in a INodeFileList
        """
        return self.inode

    def __eq__(self, other):
        """
        Compares two INodeFile objects.
        """
        if self.inode == other.inode:
            return True
        if self.size != other.size:
            return False
        if self.prefix_md5sum != other.prefix_md5sum:
            return False
        if self.md5sum != other.md5sum:
            return False
        if self.sha1sum != other.sha1sum:
            return False
        # They propably are the same
        return True

    def __len__(self):
        """
        Returns the number of paths from this INodeFile object.
        """
        return len(self.files)

    def __repr__(self):
        if self.merged_into is not None:
            return "merged into %s" % self.merged_into
        return "[%s]" % (", ".join(self.files))

    def __iter__(self):
        return iter(self.files)

    @property
    def file(self):
        """
        Return one file object.
        """
        return next(iter(self.files))  # Get one element from the set

    def addfile(self, path):
        """
        Add a new path if the inode matches.

        Returns True if the inode matches, else False.
        """
        if type(path) is INodeFile:
            if self == path:
                self.files.update(path.files)
                return True
            return False

        stat = os.lstat(path)
        if stat.st_ino == self.inode:
            try:
                path.encode('utf-8')
            except UnicodeEncodeError:
                new_name = path.encode(errors='replace')
                os.rename(path, new_name)
                path = new_name.decode('utf-8')
            self.files.add(path)
            return True
        return False

    def hash(self, algo, only_first_part=False):
        """
        Returns an hash of the file.
        """
        def fix_test_case(block):
            """
            Fix for the testing famework

            The open-method from fake_filesystem does return str instead of
            bytes object.
            """
            if type(block) is str:
                block = bytes(block, encoding='utf-8')
            return block

        with open(self.file, 'rb') as f:
            block = fix_test_case(f.read(1280))
            while block:
                algo.update(block)
                if only_first_part:
                    break
                block = fix_test_case(f.read(1280))
        return algo.hexdigest()

    @property
    def prefix_md5sum(self):
        """
        Returns the md5sum of the first part of the file.
        """
        try:
            return self._prefix_md5sum
        except AttributeError:
            self._prefix_md5sum = self.hash(hashlib.md5(), only_first_part=True)
            return self._prefix_md5sum

    @property
    def md5sum(self):
        """
        Returns the md5sum of the file.
        """
        try:
            return self._md5sum
        except AttributeError:
            self._md5sum = self.hash(hashlib.md5())
            return self._md5sum

    @property
    def sha1sum(self):
        """
        Returns the sha1sum of the file.
        """
        try:
            return self._sha1sum
        except AttributeError:
            self._sha1sum = self.hash(hashlib.sha1())
            return self._sha1sum

    def merge(self, other):
        """
        Merge other into self.

        'other' has to be an INodeFile.
        """
        # mv other to backup
        # create new hardlink to other
        # rm the backup
        for path in other.files:
            backup = path + '.file_merge-bu'
            try:
                os.rename(path, backup)
                os.link(self.file, path)
                os.remove(backup)
            except OSError:
                verbose('No rights for %s' % path, WARNING)
            else:
                self.addfile(path)
        other.merged_into = self

    def dump(self):
        """
        Creates a one-line string that represents this object.
        """
        files = "\0".join(self.files)
        md5sum_prefix = getattr(self, '_prefix_md5sum', '')
        md5sum = getattr(self, '_md5sum', '')
        sha1sum = getattr(self, '_sha1sum', '')
        return "%s\0%s\0%s\0%s\0%s\0%s" % (self.inode, self.size, md5sum_prefix,
                                           md5sum, sha1sum, files)


class INodeFileList(object):
    """
    A list of INodeFile objects.
    """
    def __init__(self, directory=None, load=None):
        """
        Saves the INodeFile object in a SortableDict.

        Arguments
        ---------
        Either the argument directory or the argument load has to be set.

        'directory' has to be a path to a directory. Each file in this directory
        will be loaded.

        'load' has to be a path to a dumped INodeFileList-file. It will be
        loaded.
        """
        self.storage = SortableDict()
        if load is not None:
            self.load(load)
        elif directory is not None:
            self.add(directory)

    def __getitem__(self, item):
        """
        Retuns an INodeFile object.

        'item' has to be an inode or an INodeFile object.
        """
        if type(item) is int:
            return self.storage[item]
        elif type(item) is INodeFile:
            return self.storage[item.inode]
        else:
            raise AttributeError('item has to be intor INodeFile not %s'
                                 % type(item))

    def __delitem__(self, item):
        """
        Removes a INodeFile from the object.
        """
        if type(item) is int:
            item = self.storage[item]
        elif type(item) is INodeFileList:
            for inode_file in item:
                del self[inode_file]
            return

        if type(item) is INodeFile:
            del self.storage[item.inode]
        else:
            raise AttributeError('key has to be int, INodeFile or '
                                 'INodeFileList, not %s' % type(key))

    def __contains__(self, item):
        return item.inode in self.storage

    def __iter__(self):
        return self.storage.values()

    def __len__(self):
        """
        Retuns the number of INodeFile objects in this object.
        """
        return len(self.storage)

    def __repr__(self):
        return "%d INodeFiles" % len(self)

    def sort_by_attribute(self, sort_attribute):
        """
        Reorder the INodeFiles by the attribute.

        'sort_attribute' has to be the name of an attribute as string.
        """
        reverse = sort_attribute == 'size'
        self.storage.sort(
            key=lambda inode_file: getattr(self[inode_file], sort_attribute),
            reverse=reverse)

    def iter_list(self, sort_attribute, size_limit=0):
        """
        Generates INodeFileList objects from the INodeFile object from this
        object, where by any File in the new INodeFileLists, one attribute
        is the same.

        'sort_attribute' decide which attribute is used.
        """
        iter_list = INodeFileList()
        self.sort_by_attribute(sort_attribute)

        def yield_condition(iter_list):
            """
            Returns True if the list would has more then one item and the size
            of the items is larger then 'size_limit'.
            """
            if (len(iter_list) <= 1 or
                    iter_list.value_for_index(0).size <= size_limit):
                return False
            return True

        value = getattr(self.value_for_index(0), sort_attribute)
        for inode_file in self:
            if getattr(inode_file, sort_attribute) == value:
                iter_list.add(inode_file)
            else:
                if yield_condition(iter_list):
                    yield iter_list
                iter_list = INodeFileList()
                value = getattr(inode_file, sort_attribute)
                iter_list.add(inode_file)

        if yield_condition(iter_list):
            yield iter_list

    def value_for_index(self, index):
        """
        Returns one INodeFile from the list.

        'index' has to be an integer.
        """
        return self.storage.value_for_index(index)

    def add(self, item):
        """
        Add a INodeFile to the object.
        """
        if type(item) is str:
            try:
                mode = os.lstat(item).st_mode
            except FileNotFoundError:
                verbose("File not found: %s" % item, DEBUG)
                return
            if stat.S_ISDIR(mode):
                # TODO: Check relativ path
                root_len = len(item.split('/'))
                for root, dirs, files in os.walk(item):
                    for file in files:
                        self.add(INodeFile(os.path.join(root, file)))
            elif stat.S_ISREG(mode):
                self.add(INodeFile(item))
            else:
                verbose("Non regular file not supported: %s" % item, DEBUG)
                return
        elif type(item) == INodeFile:
            try:
                self.storage[item.inode].addfile(item)
            except KeyError:
                self.storage[item.inode] = item
        elif type(item) == INodeFileList:
            # It is not save to use self.update(item) because there could be
            # inode_files with the same inode in item and self
            for item_value in item:
                self.add(item_value)
        else:
            raise TypeError("%s is not supported." % type(item))

    def popitem(self, *args):
        """
        Removes and returns an INodeFile at a specific index (default last).
        """
        return self.storage.popitem(*args)[1]

    def merge(self, demo=False):
        """
        Merge any INodeFile with a propably identicly together.
        """
        def status(size_list):
            first_file = size_list.value_for_index(0)
            if not first_file.size % 100:
                verbose("%s, %s, %d" % (first_file.size, first_file.file, len(size_list)), INFO)

        merged_items = INodeFileList()
        # Look for identical Items and merge them
        for size_list in self.iter_list('size'):
            status(size_list)
            for prefix_md5sum_list in size_list.iter_list('prefix_md5sum'):
                for md5sum_list in prefix_md5sum_list.iter_list('md5sum'):
                    for sha1sum_list in md5sum_list.iter_list('sha1sum'):
                        # Any element in sha1sum_list should be identical.
                        base_item = sha1sum_list.popitem()
                        for item in sha1sum_list:
                            base_item.merge(item)
                        merged_items.add(sha1sum_list)
        del self[merged_items]
        return merged_items

    def dump(self, path):
        """
        Saves the object in a file.
        """
        with open(path, 'w') as save_file:
            for item in self:
                save_file.write('%s\n' % item.dump())

    def load(self, path):
        """
        Loads the object from a file.
        """
        with open(path) as f:
            for line in f.readlines():
                item = INodeFile(line.strip())
                self.storage[item.inode] = item

    def size(self, meter='b'):
        # TODO: interpretate meter. Maby there is a lib?
        count = 0
        for f in self:
            count += f.size
        return count
