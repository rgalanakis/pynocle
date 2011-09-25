import compiler
import compiler.ast
import fnmatch
import os
import sys

import utils

PYTHON_EXE_DIR_FILTER = os.path.dirname(sys.executable) + '*'

class DepBuilder:
    """Builds dependencies between modules, starting from all modules in filenames.  Dependencies are available
    as a list of 2-item tuples as DepBuilder.dependencies.  Modules that could not be parsed are available as
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
            filename = filename[:-3] + 'py'
        if not os.path.exists(filename):
            return []
        with open(filename) as f:
            try:
                astnode = compiler.parse(f.read())
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
                self.dependencies.append((purename, puremodulefilename))
            if modulefilename:
                self.process_file(modulefilename)

    def get_module_filename(self, modulename, importing_module_filename):
        """Return the filename of the module at modulename that is being imported by importing_module_filename.  If
        the module does not have a __file__ attr, return None.
        """
        try:
            module = __import__(modulename)
        except ImportError:
            #We need to support relative imports.
            possiblepath = modulename.replace('.', os.sep) + '.py'
            possiblepath = os.path.join(os.path.dirname(importing_module_filename), possiblepath)
            if os.path.exists(possiblepath):
                return possiblepath
            raise
        if hasattr(module, '__file__'): #some modules don't have a __file__ attribute, like sys
            return os.path.abspath(module.__file__)
        return

