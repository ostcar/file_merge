import unittest
import fake_filesystem
import file_merge.inode

# Create a fake file system and some fake objects
filesystem = fake_filesystem.FakeFilesystem()
os = fake_filesystem.FakeOsModule(filesystem)
open = fake_filesystem.FakeFileOpen(filesystem)

# Override the namespace from the file_merge module
file_merge.inode.os = os
file_merge.inode.open = open


# Load the INodeFile name into the global namespace for easier use
INodeFile = file_merge.inode.INodeFile


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

    def test_md5sum(self):
        self.assertEqual(self.big_file.md5sum, '1ff3f95f646c6dc500d341fd0ebab380')
        self.assertNotEqual(self.big_file.md5sum, self.smaler_file.md5sum)

    def test_sha1sum(self):
        self.assertEqual(self.big_file.sha1sum, 'a13a2fa71f9eef222ab05611a63a0a7219b6ec24')
        self.assertEqual(self.smaler_file.sha1sum, 'a9ecf1681e9dea399f2f32968fe941f669bb062b')


if __name__ == '__main__':
    unittest.main()
