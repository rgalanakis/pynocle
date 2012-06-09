#!/usr/bin/env python
"""Functions for finding modules so pynocle doesn't have to go
through python's import machinery.
Ideally it does not have to run any code in order to analyze.
"""
import imp
import os
import sys

_oabs = os.path.abspath
_ojoin = os.path.join


class _ModuleFinder(object):
    def __init__(self, modulename, importing_module_filename):
        self.modulename = modulename
        self.imp_mod_dir = os.path.dirname(_oabs(importing_module_filename))
        self.splitmodulename = modulename.split('.')

    def __repr__(self):
        return 'ModuleFinder(modulename: %s, imp_mod_dir: %s)' % (
            self.modulename, self.imp_mod_dir)

    __str__ = __repr__
    
    def find_in_sysmodules(self):
        """If self.module is in sys.modules, return the value of its
        __file__ attr if it has it.
        Otherwise, return None.
        """
        if self.modulename in sys.modules:
            filename = getattr(sys.modules[self.modulename], '__file__', None)
            if filename:
                return filename
        return None

    def find_from_builtins(self):
        """If modulename has only one component,
        find a module for it and return its path if its path is equal to its
        name, such as is the case for sys, time, etc.

        If modulename has more than one component, or module cannot be found,
        return None.
        """
        if len(self.splitmodulename) != 1:
            return None
        try:
            path = imp.find_module(self.splitmodulename[0])[1]
            return path
        except ImportError:
            return None

    def find_package(self, path):
        """Returns the filename for the __init__ file if path is
        the directory of a package,
        None if path is not a directory or there is no init file.
        """
        if not os.path.isdir(path):
            return None
        for suffix in map(lambda suf: suf[0], imp.get_suffixes()):
            fullpath = os.path.join(path, '__init__' + suffix)
            if os.path.isfile(fullpath):
                return fullpath
        return None

    def get_module_filename(self):
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
        for attempt in None, self.imp_mod_dir:
            lastpath = attempt#self.imp_mod_dir
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
            if lastpath and os.path.isfile(lastpath):
                return lastpath

        #Trying to import a package from a file in the package will if imp_mod_dir is set to the package dir
        #So we can jump up a dir and check if it fails, since lastpath is going to be as deep as possible.
        #noinspection PyUnboundLocalVariable
        upadir = os.path.abspath(os.path.join(lastpath, '..'))
        try:
            path = imp.find_module(self.splitmodulename[-1], [upadir])[1]
            pkg = self.find_package(path)
            if pkg:
                return pkg
        except ImportError:
            pass

        #At this point, we may have a module we can't do anything with.  It could be a stdlib module or something that
        #isn't available to us, so just return nothing for now...
        return None
        #raise NotImplementedError


def get_module_filename(modulename, importing_module_filename=None, stripext=True):
    """Return the filename of the module at modulename.  Tries to emulate the python import logic, without running
    any files.

    importing_module_filename: If provided, should be the filename (__file__) of the module that is trying to import
        the module of modulename.
    stripext: If true, strip the extension from the returned filename.  If False, the filename may or may not have an
        extension.
    """
    result = _ModuleFinder(modulename, importing_module_filename).get_module_filename()
    if result and stripext:
        result = os.path.splitext(result)[0]
    return result


class ModuleFinderCache(object):
    """Provides caching behavior for the get_module_filename function.  Useful for a single run of a metric generation.
    We do not want to cache the values at a module/static level because the paths involved in the lookup can change.

    modulename_to_importing_filename_to_result is a dict of dicts:
    { modulename: {importing_module_filename: result} }
    """
    def __init__(self):
        self.modulename_to_importing_filename_to_result = {}

    def cached(self, modulename, importing_module_filename):
        """Returns a tuple of (was in cache, value if it was in cache) for modulename/importing_module_filename.
        If not cached, creates the collections in the cache.

        Note that extensionless values should never be stored in the cache!
        """
        importing_to_result = self.modulename_to_importing_filename_to_result.setdefault(modulename, {})
        if importing_module_filename in importing_to_result:
            return True, importing_to_result[importing_module_filename]
        return False, None

    def get_module_filename(self, modulename, importing_module_filename=None, stripext=True):
        importing_module_filename = os.path.splitext(importing_module_filename)[0]
        incache, result = self.cached(modulename, importing_module_filename)
        if not incache:
            result = get_module_filename(modulename, importing_module_filename, stripext=False)
            self.modulename_to_importing_filename_to_result[modulename][importing_module_filename] = result
        if result and stripext:
            result = os.path.splitext(result)[0]
        return result