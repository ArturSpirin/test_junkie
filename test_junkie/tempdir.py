import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

from test_junkie.debugger import LogJunkie


def _clear_read_only(func, path, _error):
    """rmtree's error handler: a read-only file (Windows) can't be removed, clear the bit and try once more"""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    func(path)


class TempDir(object):
    """
    One test attempt's temporary directory, given to a test, @beforeTest or @afterTest that names a temp_dir
    argument. Made the first time it's asked for, so a test that never asks makes nothing; removed after the attempt
    """

    def __init__(self):
        self.__path = None

    def path(self):
        """:return: pathlib.Path of a new, empty directory, the same one on every call"""
        if self.__path is None:
            self.__path = Path(tempfile.mkdtemp(prefix="tj_"))
        return self.__path

    def remove(self):
        """Removes the directory if it was made. A failure is a warning: it never changes the test's result"""
        if self.__path is None or not os.path.lexists(str(self.__path)):  # never made, or the test removed it
            return
        try:
            if sys.version_info >= (3, 12):  # onerror= is deprecated from 3.12
                shutil.rmtree(str(self.__path), onexc=_clear_read_only)
            else:
                shutil.rmtree(str(self.__path), onerror=_clear_read_only)
        except Exception as error:
            LogJunkie.warn("Could not remove temp_dir {}: {!r}".format(self.__path, error))
