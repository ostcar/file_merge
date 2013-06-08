import os
from .inode import INodeFile, INodeFileList


def p1(base_path):
    for path in sorted(os.listdir(base_path)):
        full_path = os.path.join(base_path, path)
        files_path = os.path.join(full_path, 'files')
        if os.path.exists(files_path):
            verbose("Skipping %s" % full_path, INFO)
            continue
        verbose("Now I do %s" % full_path, INFO)
        inode_file_list = INodeFileList(full_path)
        verbose("Start merging", INFO)
        merged_files = inode_file_list.merge()
        verbose("Merged %d files" % len(merged_files), INFO)
        inode_file_list.dump(files_path)


def p2(base_path):
    status_file = os.path.join(base_path, 'file_merge.status')
    data_file = os.path.join(base_path, 'file_merge.data')
    if os.path.exists(status_file):
        with open(status_file) as f:
            last_path = int(f.readline().strip())
        verbose("Load old data")
        file_list = INodeFileList(load=data_file)
    else:
        last_path = 0
        file_list = INodeFileList()

    for path in sorted(os.listdir(base_path)):
        try:
            int(path)
        except ValueError:
            continue
        if int(path) <= last_path:
            continue

        full_path = os.path.join(base_path, path)
        verbose("Now I do %s" % full_path, INFO)
        file_list.add(full_path)
        verbose("%d files now" % len(file_list))
        file_list.dump(data_file)
        with open(status_file, 'w') as f:
            f.write(path)


def p3(base_path):
    for path in sorted(os.listdir(base_path)):
        try:
            int(path)
        except ValueError:
            continue
        full_path = os.path.join(base_path, path)
        files_path = os.path.join(full_path, 'files')
        if os.path.exists(files_path):
            verbose("Skipping %s" % full_path, INFO)
            continue
        verbose("Now I do %s" % full_path, INFO)
        inode_file_list = INodeFileList(full_path)
        inode_file_list.dump(files_path)
        verbose("files: %d" % len(inode_file_list))


def p3b(base_path):
    file_list = INodeFileList()
    for path in sorted(os.listdir(base_path)):
        try:
            int(path)
        except ValueError:
            continue
        full_path = os.path.join(base_path, path)
        files_path = os.path.join(full_path, 'files')
        verbose("Loading %s" % files_path)
        file_list.load(files_path)

    #verbose("dumping file")
    #file_list.dump(os.path.join(base_path, path + '.all-data'))
    verbose("merging files")
    file_list.merge()
    verbose("%d Files merged", len(file_list))
