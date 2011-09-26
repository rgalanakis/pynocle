#!/usr/bin/env python

import compiler
import compiler.ast
import fnmatch
import os
import sys

import pynocle.utils as utils

PYTHON_EXE_DIR_FILTER = os.path.dirname(sys.executable) + '*'

class Dependency(object):
    """Data object that represents a single dependency with a startpoint and endpoint."""
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
    """Builds dependencies between modules, starting from all modules in filenames.  Dependencies are available
    as a list of Dependency instances as DepBuilder.dependencies.  Modules that could not be parsed are available as
    DepBuilder.failed.

    exclude_paths: Collection of fnmatch patterns.  Any path that matches any pattern will not be considered for
        dependencies.
    exclude_modules: Any modules that match one of the strings in this collection will not be considered for
        dependencies.  This is necessary because some modules do not have filenames.
    """
    def __init__(self, filenames, exclude_paths=(PYTHON_EXE_DIR_FILTER,), exclude_modules=('sys',)):
        exclude_paths += (r'C:\Program Files (x86)\JetBrains\PyCharm *',)
        self._processed = set()
        self.dependencies = []
        self.failed = []
        self.exclude_paths = exclude_paths
        self.exclude_modules = set(exclude_modules)
        for fn in filenames:
            self.process_file(fn)

    def is_excluded(self, path):
        for epath in self.exclude_paths:
            if fnmatch.fnmatch(path, epath):
                return True
        return path in self.exclude_modules

    def _extless(self, filename):
        return os.path.splitext(filename)[0]

    def get_all_importnodes(self, filename):
        #We can only read py files right now
        if filename.endswith('.pyd'):
            return []
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        if not os.path.exists(filename):
            return []
        try:
            astnode = compiler.parseFile(filename)
        except SyntaxError:
            self.failed.append(self._extless(filename))
            return []
        importnodes = filter(lambda node: isinstance(node, compiler.ast.Import),
                             utils.flatten(astnode, lambda node: node.getChildNodes()))
        return importnodes

    def process_file(self, filename):
        purename = self._extless(filename)
        if purename in self._processed or self.is_excluded(purename):
            return
        self._processed.add(purename)
        impnodes = self.get_all_importnodes(filename)
        for node in impnodes:
            modulename = node.names[0][0]
            modulefilename = self.get_module_filename(modulename, filename)
            if modulefilename:
                puremodulefilename = self._extless(modulefilename)
            else:
                puremodulefilename = modulename
            if not self.is_excluded(puremodulefilename):
                self.dependencies.append(Dependency(purename, puremodulefilename))
            if modulefilename:
                self.process_file(modulefilename)

    def get_module_filename(self, modulename, importing_module_filename):
        """Return the filename of the module at modulename that is being imported by importing_module_filename.  If
        the module does not have a __file__ attr, return None.
        """
        try:
            module = __import__(modulename)
            module = sys.modules[modulename]
        except ImportError:
            #We need to support relative imports.
            impdir = os.path.dirname(importing_module_filename)
            modulenameslashes = modulename.replace('.', os.sep)
            possiblepath = os.path.join(impdir, modulenameslashes + '.py')
            if os.path.exists(possiblepath):
                return possiblepath
            possiblepath = os.path.join(impdir, modulenameslashes, '__init__.py')
            if os.path.exists(possiblepath):
                return possiblepath
            #raise #Do we want to raise here?  Need more testing on other codebases since it doesn't raise on pynocle's
            return None
        if hasattr(module, '__file__'): #some modules don't have a __file__ attribute, like sys
            return os.path.abspath(module.__file__)
        return

