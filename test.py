import unittest
import fake_filesystem
import file_merge.inode

# Create a fake file system and some fake objects
filesystem = fake_filesystem.FakeFilesystem()

os = fake_filesystem.FakeOsModule(filesystem)
open = fake_filesystem.FakeFileOpen(filesystem)


# fake_filesystem does not implement os.link yet
def link(source, link):
    inode = os.stat(source).st_ino
    filesystem.CreateFile(link, contents='', inode=inode)

os.link = link

# Override the namespace from the file_merge module
file_merge.inode.os = os
file_merge.inode.open = open

# Load the INodeFile name into the global namespace for easier use
INodeFile = file_merge.inode.INodeFile
INodeFileList = file_merge.inode.INodeFileList


class TestCase(unittest.TestCase):
    def add_file(self, path, content, inode=None):
        self._inodes = getattr(self, '_inodes', set())
        self._files = getattr(self, '_files', [])

        if inode is None:
            for i in range(10000):
                if i not in self._inodes:
                    inode = i
                    break

        filesystem.CreateFile(path, contents=content, inode=inode)
        self._inodes.add(inode)
        self._files.append(path)

    def tearDown(self):
        for file in self._files:
            filesystem.RemoveObject(file)


class TestINodeFile(TestCase):
    def setUp(self):
        self.myfile = '/myfile'
        self.add_file(self.myfile, 'foobar\n', 1)
        self.inode_file = INodeFile(self.myfile)

        self.second_file = '/second_file'
        self.add_file(self.second_file, 'second_file\n', 1)

    def test_init(self):
        self.assertEqual(self.inode_file.size, 7)
        self.assertIn('/myfile', self.inode_file.files)

    def test_hash(self):
        inode = os.lstat(self.myfile).st_ino
        self.assertEqual(hash(self.inode_file), inode)

    def test_len(self):
        self.assertEqual(len(self.inode_file), 1)
        self.inode_file.addfile(self.second_file)
        self.assertEqual(len(self.inode_file), 2)

    def test_iter(self):
        self.assertEqual(list(iter(self.inode_file)), [self.myfile])
        self.inode_file.addfile(self.second_file)
        self.assertEqual(set(iter(self.inode_file)), set([self.myfile, self.second_file]))

    def test_file(self):
        self.assertEqual(self.inode_file.file, self.myfile)

    def test_repr(self):
        self.assertEqual(repr(self.inode_file), '[/myfile]')

    def test_addfile(self):
        second = INodeFile(self.second_file)
        self.inode_file.addfile(second)
        self.assertIn(self.second_file, self.inode_file)

        self.add_file('/other', 'other')
        value = self.inode_file.addfile(INodeFile('/other'))
        self.assertFalse(value)
        self.assertNotIn('/other', self.inode_file)

        value = self.inode_file.addfile('/other')
        self.assertFalse(value)
        self.assertNotIn('/other', self.inode_file)


class TestINodeFileHash(TestCase):
    def setUp(self):
        content = 1280 * 'I am a big file\n'
        self.add_file('/big_file', content)
        self.big_file = INodeFile('/big_file')

        self.add_file('/smaler_file', content[:1280])
        self.smaler_file = INodeFile('/smaler_file')

    def test_prefix_md5sum(self):
        self.assertNotEqual(self.big_file, self.smaler_file)
        self.assertEqual(self.big_file.prefix_md5sum, '65dfc2296533ce7d59674f57c3432e49')
        self.assertEqual(self.big_file.prefix_md5sum, self.smaler_file.prefix_md5sum)
        self.assertIsNotNone(getattr(self.big_file, '_prefix_md5sum', None))

    def test_md5sum(self):
        self.assertEqual(self.big_file.md5sum, '1ff3f95f646c6dc500d341fd0ebab380')
        self.assertNotEqual(self.big_file.md5sum, self.smaler_file.md5sum)
        self.assertIsNotNone(getattr(self.big_file, '_md5sum', None))

    def test_sha1sum(self):
        self.assertEqual(self.big_file.sha1sum, 'a13a2fa71f9eef222ab05611a63a0a7219b6ec24')
        self.assertEqual(self.smaler_file.sha1sum, 'a9ecf1681e9dea399f2f32968fe941f669bb062b')
        self.assertIsNotNone(getattr(self.big_file, '_sha1sum', None))


class TestINodeFileDump(TestCase):
    def setUp(self):
        self.add_file('/testfile', 'foobar', 300)
        self.file = INodeFile('/testfile')
        self.dump = "\0".join(['300', '6', '', '', '', '/testfile'])

    def test_dump(self):
        self.assertEqual(self.file.dump(), self.dump)

    def test_load(self):
        load_file = INodeFile(self.dump)
        self.assertEqual(load_file.__dict__, self.file.__dict__)

    def test_with_hash(self):
        self.file.md5sum
        self.file.prefix_md5sum
        self.file.sha1sum
        dump = "\0".join(['300', '6', '3858f62230ac3c915f300c664312c63f',
                          '3858f62230ac3c915f300c664312c63f',
                          '8843d7f92416211de9ebb963ff4ce28125932878',
                          '/testfile'])
        file_dump = self.file.dump()
        self.assertEqual(file_dump, dump)
        load_file = INodeFile(file_dump)
        self.assertEqual(load_file.__dict__, self.file.__dict__)
        self.assertIsNotNone(getattr(load_file, '_prefix_md5sum', None))
        self.assertIsNotNone(getattr(load_file, 'md5sum', None))
        self.assertIsNotNone(getattr(load_file, 'sha1sum', None))


class TestINodeFileCompare(TestCase):
    def setUp(self):
        self.add_file('/file1', 'content1')
        self.add_file('/file2', 'content2', 300)
        self.add_file('/file', 'content', 300)
        self.add_file('/big1', 1999 * 'l' + 'i')
        self.add_file('/big2', 2000 * 'l')
        self.add_file('/big3', 2000 * 'l')
        self.files = [INodeFile(path) for path in ['/file1', '/file2', '/file',
                                                   '/big1', '/big2', '/big3']]

    def test_compare(self):
        self.assertEqual(self.files[1], self.files[2])
        self.assertIsNone(getattr(self.files[1], '_prefix_md5sum', None))

        self.assertNotEqual(self.files[0], self.files[2])
        self.assertIsNone(getattr(self.files[1], '_prefix_md5sum', None))

        self.assertNotEqual(self.files[0], self.files[1])
        self.assertIsNotNone(getattr(self.files[1], '_prefix_md5sum', None))

        self.assertNotEqual(self.files[3], self.files[4])
        self.assertIsNotNone(getattr(self.files[3], '_md5sum', None))

        self.files[5]._sha1sum = 'different'
        self.assertNotEqual(self.files[4], self.files[5])
        self.assertIsNotNone(getattr(self.files[4], '_sha1sum', None))

        del self.files[5]._sha1sum
        self.assertEqual(self.files[4], self.files[5])


class TestINodeFileMerge(TestCase):
    def setUp(self):
        self.add_file('/path1', 'content', 5)
        self.add_file('/path2', 'content', 6)
        self.f1 = INodeFile('/path1')
        self.f2 = INodeFile('/path2')

    def test_merge(self):
        self.assertNotEqual(self.f1.inode, self.f2.inode)
        self.f1.merge(self.f2)
        self.assertIn('/path2', self.f1)
        self.assertEqual(repr(self.f2), 'merged into %s' % self.f1)


class TestINodeFileList(TestCase):
    def setUp(self):
        self.add_file('/path1', 'content', 1)
        self.add_file('/path2', 'content2')
        self.add_file('/path/to/file', 'other content')
        self.add_file('/path/to/file2', 'other content2')
        self.ilist = INodeFileList('/')

    def test_init(self):

        self.assertEqual(len(self.ilist), 4)

    def test_getitem(self):
        self.assertEqual(self.ilist[1], INodeFile('/path1'))
        self.assertEqual(self.ilist[INodeFile('/path1')], INodeFile('/path1'))
        self.assertEqual(self.ilist['/path1'], INodeFile('/path1'))

    def test_delitem_by_inode(self):
        del self.ilist[1]
        self.assertNotIn('/path1', self.ilist)

    def test_delitem_by_path(self):
        del self.ilist['/path1']
        self.assertNotIn('/path1', self.ilist)

    def test_delitem_by_inode_file(self):
        del self.ilist[INodeFile('/path1')]
        self.assertNotIn('/path1', self.ilist)

    def test_delitem_by_inode_file_list(self):
        inode_file_list = INodeFileList('/path/to')
        del self.ilist[inode_file_list]
        self.assertNotIn('/path/to/file', self.ilist)

    def test_repr(self):
        self.assertEqual(repr(self.ilist), '4 INodeFiles')

    def test_sort_by_attribute(self):
        self.ilist.sort_by_attribute('size')
        self.assertEqual(repr(list(self.ilist)), '[[/path/to/file2], [/path/to/file], [/path2], [/path1]]')

        self.ilist.sort_by_attribute('md5sum')
        self.assertEqual(repr(list(self.ilist)), '[[/path/to/file], [/path1], [/path/to/file2], [/path2]]')

    def test_iter_list(self):
        self.add_file('/new_path1', '1234567')
        self.add_file('/new_path2', 'a234567')
        self.add_file('/new_path3', '123')
        self.add_file('/new_path4', 'abc')
        self.add_file('/new_path0', '')
        self.add_file('/new_path0b', '')
        self.ilist.add('/')

        # size
        lists = list(self.ilist.iter_list('size'))
        self.assertEqual(len(lists), 2)
        self.assertEqual(repr(lists[0].storage), '{1: [/path1], 4: [/new_path1], 5: [/new_path2]}')
        self.assertEqual(repr(lists[1].storage), '{6: [/new_path3], 7: [/new_path4]}')

        # prefix_md5sum
        self.add_file('/new/new_big', 1500 * 'l')
        self.add_file('/new/new_big2', 2000 * 'l')
        ilist = INodeFileList('/new')
        lists = list(ilist.iter_list('prefix_md5sum'))
        self.assertEqual(len(lists), 1)
        self.assertEqual(repr(lists[0].storage), '{10: [/new/new_big], 11: [/new/new_big2]}')

    def test_size(self):
        self.assertEqual(self.ilist.size(), 42)

    def test_dump_load(self):
        self.add_file('/dumpfile', '')  # create dumpfile so it will be removed on teadDown
        self.ilist.dump('/dumpfile')
        ilist = INodeFileList(load='/dumpfile')
        self.assertEqual(ilist.storage, self.ilist.storage)


if __name__ == '__main__':
    unittest.main()
