#!/usr/bin/env python

import abc
import colorsys
import hashlib
import os
import subprocess
import tempfile

import pynocle.utils as utils


def lerp(minval, maxval, term):
    return (maxval - minval) * term + minval


def saturate(num, floats=True):
    if hasattr(num, '__iter__'):
        return [saturate(x) for x in num]
    if num < 0:
        return num
    maxval = 1 if floats else 255
    if num > maxval:
        return maxval
    return num


def nth_percentile(values, n=0.95):
    """Get's the value in values that is closest to the nth percentile.
    For example, nth_percentile([4, 2, 1, 5], .75)
    would return 4.
    """
    sorted_vals = sorted(values)
    ind = int(len(sorted_vals) * n)
    return sorted_vals[ind]


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

    def get_attr_str(self, *args, **kwargs):
        """Return all args and kwargs enclosed in square brackets."""
        argstr = ','.join(str(a) for a in args)
        kws = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())
        return '[%s]' % ','.join(filter(None, [argstr, kws]))

    def get_output_format(self, outputfilename, overrideformat=None):
        """Returns the file format/type/extension string based on the arguments
        (use overrideformat if provided,
        otherwise use outputfilename's extension).
        """
        result = overrideformat
        if not result:
            #Skip the period on the extension
            result = os.path.splitext(outputfilename)[1][1:]
        return result
    
    def render(self, outputfilename,
               dotpath=None, overrideformat=None, wait=True, moreargs=()):
        """Renders the dot file at dotpath to outputfilename.

        outputfilename: The name of the image file to be written.
        The format will be inferred by the extension.

        :param dotpath: The path of the dotfile to use.
          If not provided, call self.savedot with a temporary path.
        :param overrideformat: If provided, use this instead of inferring
          the format from outputfilename.
        :param moreargs: Additional args to invoke the exe with.
        """
        if not dotpath:
            dotpath = self.savetempdot()
        format = self.get_output_format(outputfilename, overrideformat)
        clargs = [self.dotexe(), '-T' + format, dotpath, '-o', outputfilename]
        clargs.extend(moreargs)
        try:
            p = subprocess.Popen(
                clargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except WindowsError as exc:
            if exc.errno == 2:
                raise utils.MissingDependencyError('Could not start %s: %s' % (
                    self.dotexe(), repr(exc)))
            raise
        if wait:
            p.communicate()


class DefaultRenderer(IRenderer):
    def __init__(self, dependencygroup,
                 exe='dot', leading_path=None, styler=None):
        self.depgroup = dependencygroup
        self.deps = dependencygroup.dependencies
        self.failedfiles = dependencygroup.failed
        self.exe = exe
        #Make a copy of our defaults and change any overridden ones.
        self.styler = styler or DefaultStyler(leading_path=leading_path)

    def dotexe(self):
        return self.exe

    def _is_package(self, fullpath):
        return (os.path.isdir(fullpath) or
                os.path.splitext(fullpath)[0].endswith('__init__'))

    def _write_edges(self, out):
        """Writes all edges for all dependencies,
        and returns two dictionaries where the keys are the nodenames
        and the values are the full paths.
        First dictionary is for packages, second is for modules.
        """
        pkgs = {}
        modules = {}
        for startpath, endpath in self.deps:
            startname = self.styler.nodetext(startpath)
            endname = self.styler.nodetext(endpath)
            if self.styler.exclude(startpath) or self.styler.exclude(endpath):
                continue
            edgeattrs = self.get_attr_str(
                weight=self.styler.weight(startname, endname))
            out.write('    "%s" -> "%s" %s;\n' % (
                startname, endname, edgeattrs))
            for fullname, purename in [(startpath, startname),
                                       (endpath, endname)]:
                if self._is_package(fullname):
                    pkgs[purename] = fullname
                else:
                    modules[purename] = fullname
        return pkgs, modules

    def _write_clusters(self, clusters, out):
        # subgraph cluster_Computers
        # {label="Computers"; labelloc="b"; Computers_icon};
        for clustername, clusternodes in clusters.items():
            out.write('    subgraph cluster_%s {\n' % clustername)
            out.write('        label="%s";\n' % clustername)
            for kvp in self.styler.clusterstyle(clustername).items():
                out.write('        %s=%s;\n' % kvp)

            out.write('        "%s";\n' % clustername)
            for node in clusternodes:
                out.write('        "%s";\n' % node)
            out.write('    }\n')

    def savedot(self, filename):
        with open(filename, 'w') as f:
            f.write('digraph G {\n')
            for kvp in self.styler.graphsettings().items():
                f.write('    %s=%s;\n' % kvp)
            
            pkgs, modules = self._write_edges(f)
            failed = dict((self.styler.nodetext(fname), fname)
                          for fname in self.failedfiles)

            for dictitems, style_func in (
                (failed.items(), self.styler.failedstyle),
                (pkgs.items(), self.styler.packagestyle),
                (modules.items(), self.styler.modulestyle)
                ):
                for purename, fullname in dictitems:
                    style = style_func(self.depgroup, fullname)
                    stylestr = self.get_attr_str(**style)
                    f.write('    "%s" %s\n' % (purename, stylestr))

            allkeys = failed.keys() + pkgs.keys() + modules.keys()
            clusters = self.styler.create_clusters(allkeys)
            if clusters:
                self._write_clusters(clusters, f)
            f.write('}')


def name_to_color(name):
    """Converts name into an rgb color based on its md5 hash.
    Copied from http://www.tarind.com/depgraph2dot.py.
    Don't try to understand this code...
    """
    n = hashlib.md5(name).digest()
    hf = float(ord(n[0])+ord(n[1])*0xff)/0xffff
    sf = float(ord(n[2]))/0xff
    vf = float(ord(n[3]))/0xff
    r,g,b = colorsys.hsv_to_rgb(hf, 0.3+0.6*sf, 0.8+0.2*vf)
    return '#%02x%02x%02x' % (r*256,g*256,b*256)


class DefaultStyler(object):
    """Graph styling for dot rendering.

    All dot colors can be found here:
      http://www.graphviz.org/doc/info/colors.html#brewer
    """

    def __init__(self, **kwargs):
        self.weight_normal = kwargs.get('weight_normal', 1)
        self.weight_heaviest = kwargs.get('weight_heaviest', 4)
        self.leading_path = kwargs.get('leading_path') or os.getcwd()

    def create_clusters(self, nodenames):
        """Return a dictionary of {package name, (modules)),
        where package name will be the cluster name
        (and is also normally the package name),
        and modules are the names of all nodes included in the package
        (including the __init__ files, usually).

        Will also nest clusters for packages nested within other packages.

        Return None to disable clustering.
        """
        result = {}
        for name in nodenames:
            dotind = name.find('.')
            if dotind > -1:
                cluster = name[:dotind]
                items = result.setdefault(cluster, [])
                items.append(name)
#            while dotind > -1:
#                cluster = name[:dotind]
#                result.setdefault(cluster, [])
#                result[cluster].append(name)
#                dotind = name.find('.', dotind + 1)
        return result

    def _calc_outline_col(self, ca, maxca):
        """Should go from black to bright red as `ca` approaches `maxca`."""
        redchan = 0x00
        if maxca: # If maxca is 0 we'd get an error, just use black if so.
            redchan = lerp(0x00, 0xff, float(ca) / maxca)
        return '#%02x0000' % redchan

    def _calc_fill_col(self, ce, maxce):
        """Should go from green to red as `ce` approaches `maxce`."""
        redchan, greenchan = 0x00, 0xff
        # If maxce is 0, we'd get an error, so just use green.
        if maxce:
            ratio = float(ce) / maxce
            redchan = lerp(0x00, 0xff, ratio)
            greenchan = lerp(0xff, 0x00, ratio)
        return '#%02x%02x00' % (redchan, greenchan)

    def _calc_node_colors(self, depgroup, depnode):
        """Returns a tuple of (outline color, fill color).
        Outline color will go from black at zero Ca to red at 1 Ca.
        Fill color will go from a green at 0 Ce to reddish at 1 Ce.
        """
        try:
            ca = depgroup.depnode_to_ca[depnode]
            ce = depgroup.depnode_to_ce[depnode]
        except KeyError:
            return None
        outlcol = self._calc_outline_col(
            ca, nth_percentile(depgroup.depnode_to_ca.values()))
        fillcol = self._calc_fill_col(
            ce, nth_percentile(depgroup.depnode_to_ce.values()))
        return '"%s"' % outlcol, '"%s"' % fillcol

    def nodetext(self, s):
        """Prettifies s for rendering on the node.
        Escape s and remove some junk (cwd, drive, ext)
        so that it can be used as a proper nodename.
        """
        #First look for __init__ and move it down to the dir if it is
        s2 = s
        s2 = os.path.splitext(s2)[0]
        if s2.endswith('__init__'):
            s2 = s2[:-9] #-9 is len of __init__ and preceding path sep
        s2 = utils.prettify_path(s2, self.leading_path)
        if not s2:
            # We've removed the whole path,
            # grab the last dir from the leadingpath that removed it
            s2 = self.leading_path.replace(os.altsep, os.sep).split(os.sep)[-1]
        else:
            s2 = os.path.splitdrive(s2)[1]
            s2 = s2.replace(os.sep, '.').replace(os.altsep, '.')
        return s2.strip('.')

    def weight(self, a, b):
        """Return the weight of the dependency from a to b.
        Higher weights usually have shorter straighter edges.
        Should return a value between self.weight_normal and
        self.weight_heaviest.

        If module b starts with an underscore, assume a high weight.
        If module a starts with module b or vice versa, assume a 
        """
        if b.split('.')[-1].startswith('_'):
            # A module that starts with an underscore.
            # You need a special reason to import these
            # (for example random imports _random),
            # so draw them close together
            return self.weight_heaviest
        if a.startswith(b) or b.startswith(a):
            return lerp(self.weight_normal, self.weight_heaviest, .5)
        return self.weight_normal

    def graphsettings(self):
        """Returns a dictionary of top-level graph settings
        (ranksep, 'node', concentrate, etc.')."""
        return {'ranksep':'1.0', 'concentrate':'true', 'compound':'true',
                'node':'[style=filled,fontname=Arial,fontsize=10]'}

    def exclude(self, path):
        """Return True if a node should be excluded (such as tests)."""
        return os.path.basename(path).startswith('test')

    def failedstyle(self, depgroup, depnode):
        """Return a dictionary of keys and values that will be used
        to style the nodes of failed parses."""
        return {'shape': 'polygon',
                'sides': 8,
                'fillcolor':'red',
                'color': 'red',
                'fontcolor':'white',
                'peripheries': 2}

    def packagestyle(self, depgroup, depnode):
        outline, fill = self._calc_node_colors(depgroup, depnode)
        return {'shape':'box', 'color':outline, 'fillcolor':fill}

    def modulestyle(self, depgroup, depnode):
        outline, fill = self._calc_node_colors(depgroup, depnode)
        return {'shape': 'ellipse', 'color':outline, 'fillcolor':fill}

    def clusterstyle(self, clustername):
        col = '"%s"' % name_to_color(clustername)
        return {'color':'black', 'fillcolor':col, 'style':'filled'}
