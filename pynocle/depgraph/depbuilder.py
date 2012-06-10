#!/usr/bin/env python

import compiler
import compiler.ast
import fnmatch
import itertools
import os
import sys

import pynocle._modulefinder as modulefinder
import pynocle.utils as utils


_python_stdlib_filter = os.path.dirname(sys.executable) + '*'
_pycharm_filter = '*JetBrains\PyCharm *'
EXCLUDE_PATHS = _python_stdlib_filter, _pycharm_filter

EXCLUDE_MODULES = ('sys', 'time','imp')


class Dependency(object):
    """Data object that represents a single dependency with a
    startpoint and endpoint."""
    def __init__(self, startpt, endpt):
        self.startpt = startpt
        self.endpt = endpt

    def __iter__(self):
        yield self.startpt
        yield self.endpt

    def __eq__(self, other):
        if isinstance(other, Dependency):
            return other.startpt == self.startpt and other.endpt == self.endpt
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return True
        return not result

    def __str__(self):
        return 'Dependency(%s -> %s)' % (self.startpt, self.endpt)
    __repr__ = __str__


class DependencyGroup(object):
    def __init__(self, dependencies, failed=()):
        self.failed = failed
        self.dependencies = dependencies
        self.allstartpts, self.allendpts = zip(*dependencies)
        self.depnode_to_ca = self._calc_coupling(self.allendpts)
        self.depnode_to_ce = self._calc_coupling(self.allstartpts)
        #allstartpts and allendpts will be of equal size, but not equal contents- we want to make sure our coupling
        #dicts have the same keys so we have all metrics for all modules!
        for d in self.depnode_to_ca, self.depnode_to_ce:
            for key in self.allstartpts + self.allendpts:
                d.setdefault(key, 0)

    def _calc_coupling(self, depnodes):
        """Return a dict where keys are all unique items in depnodes and values are the number of times
        those items occur.
        """
        #This method can be optimized if it ever becomes a bottleneck
        result = {}
        depnodecopy = list(depnodes)
        unique = set(depnodes)
        for item in unique:
            count = 0
            for i in range(len(depnodecopy) - 1, 0, -1): #we're modifying depnodecopy inside loop
                if depnodecopy[i] == item: #Increment and remove the item so we don't have to reiterate it
                    depnodecopy.pop(i)
                    count += 1
            result[item] = count
        return result


class DepBuilder:
    """Builds dependencies between modules,
    starting from all modules in filenames.
    Dependencies are available as a list of `Dependency`
    instances as `self.dependencies`.
    Modules that could not be parsed are available as `self.failed`.

    :param exclude_paths: Collection of fnmatch patterns.
      Any path that matches any pattern will not be considered for dependencies.
    :param exclude_modules: Any modules that match one of the strings
      in this collection will not be considered for dependencies.
      This is necessary because some modules do not have filenames.
    """
    def __init__(self,
                 filenames,
                 exclude_paths=EXCLUDE_PATHS,
                 exclude_modules=EXCLUDE_MODULES):
        self._processed = set()
        self.dependencies = []
        self.failed = []
        self.exclude_paths = exclude_paths
        self.exclude_modules = set(exclude_modules)
        self.modulefinder_cache = modulefinder.ModuleFinderCache()
        for fn in filenames:
            self._process_file(fn)

    def _is_excluded(self, path):
        """Check whether the given path is an excluded module.
        Excluded modules will be cached in self.excluded_modules so
        they don't have to be re-checked.
        If path evaluates to False, it is excluded.
        """
        if not path:
            return True
        if path in self.exclude_modules:
            return True
        for epath in self.exclude_paths:
            if fnmatch.fnmatch(path, epath):
                self.exclude_modules.add(path)
                return True
        p2 = set(path)
        if not '.' in p2 and not os.sep in p2 and not os.altsep in p2:
            self.exclude_modules.add(path)
            return True
        return False

    def _extless(self, filename):
        """Return an extensionless path for filename."""
        return os.path.splitext(filename)[0]

    def _extract_modulename(self, node):
        """If node is a From/Import node, return the module's name,
        otherwise return None."""
        if isinstance(node, compiler.ast.Import):
            return node.names[0][0]
        if isinstance(node, compiler.ast.From):
            return node.modname
        return None

    def _get_all_imported_modulenames(self, filename):
        """Compiles an AST for filename and returns the module names
        for all modules imported by.

        If no file for filename exists, or it is an unparseable file (pyd, pyc),
        return an empty list.

        If the file cannot be parsed,
        append to self.failed and return an empty list.
        """
        #We can only read py files right now
        if filename.endswith('.pyd'):
            return []
        if filename.endswith('.pyc') or filename.endswith('.pyo'):
            filename = filename[:-1]
        elif not os.path.splitext(filename)[1]: #Has no ext whatsoever
            filename += '.py'
        if not os.path.exists(filename):
            return []
        try:
            astnode = compiler.parseFile(filename)
        except SyntaxError:
            self.failed.append(self._extless(filename))
            return []
        allnodes = utils.flatten(astnode, lambda node: node.getChildNodes())
        names = itertools.imap(self._extract_modulename, allnodes)
        names = itertools.ifilter(None, names)
        return names

    def _process_file(self, filename):
        """Process the file at filename.
        Adds it to processed,
        and finds dependencies for all import nodes."""
        filename = os.path.abspath(filename)
        extless_filename = self._extless(filename)
        if (extless_filename in self._processed or
            self._is_excluded(extless_filename)):
            return
        self._processed.add(extless_filename)
        importednames = self._get_all_imported_modulenames(filename)
        for impmodname in importednames:
            imported_modulefilename = self.modulefinder_cache.get_module_filename(impmodname, filename)
            #We can get back 'sys' as a filename so check if it's excluded before we get the abspath
            if imported_modulefilename and not self._is_excluded(imported_modulefilename):
                imported_modulefilename = os.path.abspath(imported_modulefilename)
                extless_imported_modulefilename = self._extless(imported_modulefilename)
                if not self._is_excluded(extless_imported_modulefilename):
                    self.dependencies.append(Dependency(extless_filename, extless_imported_modulefilename))
                self._process_file(imported_modulefilename)
