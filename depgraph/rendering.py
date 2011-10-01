#!/usr/bin/env python

import abc
import getopt
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
        fd, dotpath = 1, 'C:\\temp.dot'#tempfile.mkstemp('.dot')
        self.savedot(dotpath)
        return dotpath

    def get_attr_str(self, *args, **kwargs):
        """Return all args and kwargs enclosed in square brackets."""
        argstr = ','.join(str(a) for a in args)
        kws = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())
        return '[%s]' % ','.join(filter(None, [argstr, kws]))

    def get_output_format(self, outputfilename, overrideformat=None):
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
        format = self.get_output_format(outputfilename, overrideformat)
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


class DefaultRenderer(IRenderer):
    def __init__(self, dependencygroup, exe='dot'):
        self.depgroup = dependencygroup
        self.deps = dependencygroup.dependencies
        self.failedfiles = dependencygroup.failed
        self.exe = exe
        #Make a copy of our defaults and change any overridden ones.
        self.styler = DefaultStyler()

    def dotexe(self):
        return self.exe

    def _is_package(self, fullpath):
        return os.path.isdir(fullpath) or os.path.splitext(fullpath)[0].endswith('__init__')

    def savedot(self, filename):
        with open(filename, 'w') as f:
            f.write('digraph G {\n')
            #f.write('concentrate = true;\n')
            #f.write('ordering = out;\n')
            f.write('ranksep=%s;\n' % self.styler.ranksep())
            f.write('node %s;\n' % self.get_attr_str(**self.styler.nodestyle()))
            pkgs = {}
            modules = {}
            for startpt, endpt in self.deps:
                startname = self.styler.nodetext(startpt)
                endname = self.styler.nodetext(endpt)
                if self.styler.exclude(startpt) or self.styler.exclude(endpt):
                    continue
                edgeattrs = self.get_attr_str(weight=self.styler.weight(startname, endname))
                f.write('    "%s" -> "%s" %s;\n' % (startname, endname, edgeattrs))
                for fullname, purename in (startpt, startname), (endpt, endname):
                    if self._is_package(fullname):
                        d = pkgs
                    else:
                        d = modules
                    d[purename] = fullname

            failed = dict([(self.styler.nodetext(fname), fname) for fname in self.failedfiles])
            for dictitems, style_func in (
                (failed.items(), self.styler.failedstyle),
                (pkgs.items(), self.styler.packagestyle),
                (modules.items(), self.styler.modulestyle)
                ):
                for purename, fullname in dictitems:
                    style = style_func(self.depgroup, fullname)
                    stylestr = self.get_attr_str(**style)
                    f.write('    "%s" %s\n' % (purename, stylestr))
            f.write('}')


class DefaultStyler(object):
    """Graph styling for dot rendering."""

    def __init__(self, **kwargs):
        self.weight_normal = kwargs.get('weight_normal', 1)
        self.weight_heaviest = kwargs.get('weight_heaviest', 4)
        self.max_coupling = float(kwargs.get('max_coupling', 100))

    def _float_col_to_hex(self, fl):
        return hex(int(fl * 255))

    def _calc_color(self, depgroup, depnode):
        try:
            ca = depgroup.depnode_to_ca[depnode]
            ce = depgroup.depnode_to_ce[depnode]
        except KeyError:
            return None
        grn = utils.lerp(0, 1, ca / self.max_coupling)
        red = utils.lerp(0, 1, ce / self.max_coupling)
        return map(self._float_col_to_hex, (red, grn, 0))

    def nodetext(self, s):
        """Prettifies s for rendering on the node.
        Escape s and remove some junk (cwd, drive, ext) so that it can be used as a proper nodename.
        """
        #First look for __init__ and move it down to the dir if it is
        s2 = s
        s2 = os.path.splitext(s2)[0]
        if s2.endswith('__init__'):
            s2 = s2[:-9] #-9 is len of __init__ and preceding path sep
        s2 = utils.prettify_path(s2)
        if not s2: #We've removed the whole path, grab the cwd
            s2 = os.getcwd().split(os.sep)[-1]
        else:
            s2 = os.path.splitdrive(s2)[1]
            s2 = s2.replace('/', '.').replace('\\', '.')
        return s2

    def weight(self, a, b):
        """Return the weight of the dependency from a to b. Higher weights usually have shorter straighter edges.
        Should return a value between self.weight_normal and self.weight_heaviest.

        If module b starts with an underscore, assume a high weight.
        If module a starts with module b or vice versa, assume a 
        """
        if b.split('.')[-1].startswith('_'):
            # A module that starts with an underscore. You need a special reason to
            # import these (for example random imports _random), so draw them close
            # together
            return self.weight_heaviest
        if a.startswith(b) or b.startswith(a):
            return utils.lerp(self.weight_normal, self.weight_heaviest, .5)
        return self.weight_normal

    def ranksep(self):
        """Return a number value that will be used for ranksep."""
        return 1.0

    def exclude(self, path):
        """Return True if a node should be excluded (such as tests)."""
        return os.path.basename(path).startswith('test')

    def nodestyle(self):
        """Return a dictionary of keys and values that will be used for overall node styling."""
        return {'style':'filled', 'fontname': 'Arial', 'fontsize':10}

    def failedstyle(self, depgroup, depnode):
        """Return a dictionary of keys and values that will be used to style the nodes of failed parses."""
        return {'shape': 'polygon', 'sides': 8, 'fillcolor':'red', 'color': 'red', 'style': 'filled',
                'fontcolor':'white', 'peripheries': 2}

    def packagestyle(self, depgroup, depnode):
        col = self._calc_color(depgroup, depnode)
        return {'shape':'box', 'color':'black', 'fillcolor':'palegreen3', 'style':'filled'}

    def modulestyle(self, depgroup, depnode):
        col = self._calc_color(depgroup, depnode)
        return {'shape': 'ellipse', 'color':'black', 'fillcolor':'palegreen', 'style':'filled'}




class pydepgraphdot:

    def color(self,s,type):
        # Return the node color for this module name. This is a default policy - please override.
        #
        # Calculate a color systematically based on the hash of the module name. Modules in the
        # same package have the same color. Unpackaged modules are grey
        t = self.normalise_module_name_for_hash_coloring(s,type)
        return self.color_from_name(t)

    def normalise_module_name_for_hash_coloring(self,s,type):
        if type==imp.PKG_DIRECTORY:
            return s
        else:
            i = s.rfind('.')
            if i<0:
                return ''
            else:
                return s[:i]

    def color_from_name(self,name):
        n = md5.md5(name).digest()
        hf = float(ord(n[0])+ord(n[1])*0xff)/0xffff
        sf = float(ord(n[2]))/0xff
        vf = float(ord(n[3]))/0xff
        r,g,b = colorsys.hsv_to_rgb(hf, 0.3+0.6*sf, 0.8+0.2*vf)
        return '#%02x%02x%02x' % (r*256,g*256,b*256)