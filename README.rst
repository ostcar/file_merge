==========
file_merge
==========

Script to find identical files in a filesystem and merge them together using
hard links.

The implementing idea is from fslint_

.. _fslint: http://www.pixelbeat.org/fslint/

This script has the advantage, that it detects files with the same inode
(hardlinks) and does not merge this files together.


At the moment there is no real interface to use the functinality. You have
to open a python-shell and Load a path via :code:`INodeFileList(PATH)`

.. code:: python

    files = INodeFileList('/path/to/directory')
    files.merge



TODOs
=====
There is still a lot do to before this script is usable.

* Interface to call use the functioality
* More tests
* Documentation
