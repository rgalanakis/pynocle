"""Utilities for pynocle project."""
import fnmatch
import os

class MissingDependencyError(Exception):
    """If you hit this exception, it means you tried to use a feature in pynocle that required a dependency you
    weren't set up with!
    """
    pass

class _FindAll:
    """Helper state class for counting lines of groups of files."""
    def __init__(self, files_and_folders, pattern):
        self.processed_files = []
        self.processed_files_set = set()
        self.pattern = pattern
        self.findall(files_and_folders)

    def not_yet_processed(self, filename):
        return filename not in self.processed_files_set

    def findfiles(self, filenames):
        """Updates processed_files with new python files in filenames."""
        if not filenames:
            return
        files = fnmatch.filter(filenames, self.pattern)
        unique = filter(self.not_yet_processed, files)
        self.processed_files.extend(unique)
        self.processed_files_set.intersection_update(unique)

    def findall(self, files_and_folders):
        """Counts the lines of code recursively in all files and folders."""
        self.findfiles(filter(os.path.isfile, files_and_folders))
        for d in filter(os.path.isdir, files_and_folders):
            paths = map(lambda x: os.path.join(d, x), os.listdir(d))
            self.findall(paths)

def find_all(files_and_folders, pattern='*.py'):
    fa = _FindAll(files_and_folders, pattern)
    return fa.processed_files

def splitpath_root_file_ext(path):
    head, tail = os.path.split(path)
    filename, ext = os.path.splitext(tail)
    return head, filename, ext

def flatten(node, getchildren):
    yield node
    for child in getchildren(node):
        for gc in flatten(child, getchildren):
            yield gc