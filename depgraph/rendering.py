#!/usr/bin/env python

import abc
import os
import subprocess
import tempfile

import pynocle.utils as utils

class IRenderer(object):
    __metaclass__ = abc.ABCMeta

    def dotexe(self):
        """Returns the path to the dot (or other graphviz) exe to invoke."""
        return 'dot'

    @abc.abstractmethod
    def savedot(self, filename):
        """Saves a dot file to filename."""

    def savetempdot(self):
        """Saves a dot file to a temp file and returns the filename."""
        fd, dotpath = tempfile.mkstemp('.dot')
        self.savedot(dotpath)
        return dotpath

    def getformat(self, outputfilename, overrideformat=None):
        """Returns the format string based on the arguments (use overrideformat if provided, otherwise use
        outputfilename's extension).
        """
        result = overrideformat
        if not result:
            result = os.path.splitext(outputfilename)[1][1:] #Skip the period on the extension
        return result
    
    def render(self, outputfilename, dotpath=None, overrideformat=None, wait=True, moreargs=()):
        """Renders the dot file at dotpath to outputfilename.

        outputfilename: The name of the image file to be written.  The format will be inferred by the extension.
        dotpath: The path of the dotfile to use.  If not provided, call self.savedot with a temporary path.
        overrideformat: If provided, use this instead of inferring the format from outputfilename.
        moreargs: Additional args to invoke the exe with.
        """
        if not dotpath:
            dotpath = self.savetempdot()
        format = self.getformat(outputfilename, overrideformat)
        clargs = [self.dotexe(), '-T' + format, dotpath, '-o', outputfilename]
        clargs.extend(moreargs)
        try:
            p = subprocess.Popen(clargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except WindowsError as exc:
            if exc.errno == 2:
                raise utils.MissingDependencyError, 'Could not start %s: %s' % (self.dotexe(), repr(exc))
            raise
        if wait:
            p.communicate()

DEFAULT_STYLING = {
    'failed': r'shape=polygon,sides=8,style=filled,fontcolor=white,color=red,peripheries=2',
    'standard': r'shape=ellipse,color=black,fillcolor=palegreen,style=filled',
    'package': r'shape=box,color=black,fillcolor=palegreen3,style=filled',
}

class DefaultRenderer(IRenderer):
    def __init__(self, dependencies, failedfiles=(), exe='dot', styling=None):
        self.deps = dependencies
        self.failedfiles = failedfiles
        self.exe = exe
        #Make a copy of our defaults and change any overridden ones.
        self.styling = dict(DEFAULT_STYLING)
        self.styling.update(styling or {})

    def dotexe(self):
        return self.exe

    def nodename_and_style(self, s):
        """Escape s and remove some junk (drive, ext) so that it can be used as a proper nodename."""
        s2 = s.replace('\\', '/')
        s2 = os.path.splitdrive(s2)[1]
        s2 = os.path.splitext(s2)[0]
        s2 = s2.strip('/')
        if s2.endswith('/__init__'):
            s2 = s2[:-9]
            return s2, 'package'
        return s2, 'standard'

    def savedot(self, filename):
        with open(filename, 'w') as f:
            f.write('digraph G {\n')
            nodes_to_styles = {}
            for startpt, endpt in self.deps:
                #Make sure we escape our strings before we send them over... this shouldn't be necessary!
                startname, startstyle = self.nodename_and_style(startpt)
                endname, endstyle = self.nodename_and_style(endpt)
                f.write('    "%s" -> "%s";\n' % (startname, endname))
                nodes_to_styles[startname] = startstyle
                nodes_to_styles[endname] = endstyle

            for fname in self.failedfiles:
                nodes_to_styles[self.nodename_and_style(fname)[0]] = 'failed'
            for node, stylename in nodes_to_styles.items():
                f.write('    "%s" [%s];\n' % (node, self.styling[stylename]))
            f.write('}')


def clean_paths(depgraphdata):
    def san(p):
        p = os.path.splitdrive(p)[1]
        p = os.path.splitext(p)[0]
        return p.replace('\\', '/').replace('/', '.')
    for startpt, endpt in depgraphdata:
        yield san(startpt), san(endpt)