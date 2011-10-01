"""Functions for finding modules so pynocle doesn't have to go through python's import machinery.  Ideally it does
not have to run any code in order to analyze.
"""
import imp
import os
import sys

class _ModuleFinder(object):
    def __init__(self, modulename, importing_module_filename, stripext):
        self.modulename = modulename
        self.stripext = stripext
        self.imp_mod_dir = os.path.dirname(os.path.abspath(importing_module_filename))
        self.splitmodulename = modulename.split('.')

    def __repr__(self):
        return 'ModuleFinder(modulename: %s, imp_mod_dir: %s, stripext: %s)' % (
            self.modulename, self.imp_mod_dir, self.stripext)

    __str__ = __repr__
    
    def maybestrip(self, path):
        """Strips ext if self.stripext."""
        if self.stripext:
            return os.path.splitext(path)[0]
        return path

    def find_in_sysmodules(self):
        """Looks for a module in sys.modules that has a matching modulename and a __file__ attr."""
        if self.modulename in sys.modules:
            filename = getattr(sys.modules[self.modulename], '__file__', None)
            if filename:
                return filename
        return None

    def find_from_builtins(self):
        """If modulename has only one component, find a module for it and return its path if its path is equal to its
        name, such as is the case for sys, time, etc.
        """
        if len(self.splitmodulename) != 1:
            return
        try:
            path = imp.find_module(self.splitmodulename[0])[1]
            if path == self.splitmodulename[0]:
                return path
        except ImportError:
            pass
        return None

    def find_package(self, path):
        """Returns the filename for the __init__ file if path is the directory of a package, None if path is not a
        directory or there is no init file."""
        if not os.path.isdir(path):
            return None
        for suffix in map(lambda suf: suf[0], imp.get_suffixes()):
            fullpath = os.path.join(path, '__init__' + suffix)
            if os.path.isfile(fullpath):
                return fullpath
        return None

    def _get_module_filename(self):
        """See module-level get_module_filename."""

        #First look for the module and return the filename if set
        result = self.find_in_sysmodules()
        if result:
            return result

        #Second, if this is package-less, look for it as a builtin/pathless
        result = self.find_from_builtins()
        if result:
            return result

        #Now go through each component and look for an __init__
        lastpath = self.imp_mod_dir
        for i in range(len(self.splitmodulename)):
            try:
                paths = [lastpath] if lastpath else None
                lastpath = imp.find_module(self.splitmodulename[i], paths)[1]
                #If this is our last component, and it is a package, use it
                if i == len(self.splitmodulename) - 1:
                    package = self.find_package(lastpath)
                    if package:
                        return package
            except ImportError:
                pass

        #If we ended up with a path to a file, use it.
        if os.path.isfile(lastpath):
            return lastpath

        #Trying to import a package from a file in the package will if imp_mod_dir is set to the package dir
        #So we can jump up a dir and check if it fails, since lastpath is going to be as deep as possible.
        upadir = os.path.abspath(os.path.join(lastpath, '..'))
        try:
            path = imp.find_module(self.splitmodulename[-1], [upadir])[1]
            pkg = self.find_package(path)
            if pkg:
                return pkg
        except ImportError:
            pass
        raise NotImplementedError

    def get_module_filename(self):
        """Provides a wrapper for _get_module_filename that will call maybestrip to possibly strip the ext."""
        result = self.maybestrip(self._get_module_filename())
        if len(result) == 1:
            raise SystemError('Not a valid return value, there is a bug somewhere!')
        return result


def get_module_filename(modulename, importing_module_filename=None, stripext=True):
    """Return the filename of the module at modulename.  Tries to emulate the python import logic, without running
    any files.

    importing_module_filename: If provided, should be the filename (__file__) of the module that is trying to import
        the module of modulename.
    stripext: If true, strip the extension from the returned filename.  If False, the filename may or may not have an
        extension.
    """
    return _ModuleFinder(modulename, importing_module_filename, stripext).get_module_filename()

