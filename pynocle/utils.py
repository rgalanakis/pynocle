#!/usr/bin/env python
"""
Utilities for pynocle project.
"""

import abc
import xml.etree.ElementTree as ElementTree
import fnmatch
import os
import traceback


class PynocleError(Exception):
    """Base class for custom exception hierarchy."""
    pass


class AggregateError(PynocleError):
    """Error that holds a group of other errors.
    Exceptions should be a collection of sys.exc_infos (asserts if empty/None).
    The AggregateError will use the traceback of the first exc_info.
    """
    def __init__(self, exc_infos):
        assert exc_infos
        self.exc_infos = exc_infos
        formatted = [''.join(traceback.format_exception(*ei))
                     for ei in exc_infos]
        self.formatted_exc_infos = '\n'.join(formatted)
        ei = self.exc_infos[0]
        PynocleError.__init__(self, AggregateError, self, ei[2])

    def __str__(self):
        return 'Errors:\n{0}\n{1}{0}'.format(
            '-' * 10, self.formatted_exc_infos)

    __repr__ = __str__


class MissingDependencyError(PynocleError):
    """If you hit this exception, it means you tried to use a feature
    in pynocle that required a dependency you weren't set up with!
    """
    pass


class IReportFormatter(object):
    """General abc for all report formatters."""
    __metaclass__ = abc.ABCMeta

    def outstream(self):
        """Returns a file-like object to write to.

        If subclasses provide a _outstream attribute,
        this method will return that, otherwise override this.
        """
        #noinspection PyUnresolvedReferences
        return self._outstream


    @abc.abstractmethod
    def format_report_header(self):
        """Writes the information that should be at the top
        of the report to self.outstream()."""

    def format_report_footer(self):
        """Writes the information that should be at the bottom of the report.
        Usually a no-op."""

    @abc.abstractmethod
    def format_data(self, data):
        """Writes data to self.outstream()"""


def write_report(filename, data, formatter_factory):
    """Opens a stream for the file at filename and writes the
    header/data/footer using the provided formatter.

    :param filename: Filename of the report.
    :param data: Data to write into the report.
    :param formatter_factory: Callable that takes the filestream at
      filename and returns an IReportFormatter.
    """
    with open(filename, 'w') as f:
        fmt = formatter_factory(f)
        fmt.format_report_header()
        fmt.format_data(data)
        fmt.format_report_footer()


def walk_recursive(root, pattern='*.py'):
    """Walks through all files and directories under `root` and yields
    the full path of any filenames that
    `fnmatch.fnmatch(<fullpath>, pattern)`.
    """
    for root, dirnames, filenames in os.walk(root):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def splitpath_root_file_ext(path):
    """Returns a tuple of path, pure filename, and extension."""
    head, tail = os.path.split(path)
    filename, ext = os.path.splitext(tail)
    return head, filename, ext


def flatten(node, getchildren):
    """Return a generator that walks node and children recursively
    (depth-first).

    :param node: Any node that has children.
    :param getchildren: A callable that takes node and
      returns a collection of children that will be walked recursively.
    """
    yield node
    for child in getchildren(node):
        for gc in flatten(child, getchildren):
            yield gc


def swap_keys_and_values(d):
    """Returns a new dictionary where keys are d.values()
    and values are d.keys().
    If there are duplicate values, raises a KeyError.
    """
    result = dict(zip(d.values(), d.keys()))
    if len(d) != len(result):
        raise KeyError('There were duplicate values in argument.  Values: %s' %
                       d.values())
    return result


def prettify_path(path, leading=None):
    """If path begins with `leading`,
    strip it and remove any new leading slashes.
    Also removes the extension and ensures all seps are os.sep.

    :param leading: If None, cwd.
    """
    leading = (leading or os.getcwd()).replace(os.altsep, os.sep)
    s = os.path.splitext(path.replace(os.altsep, os.sep))[0]
    if s.startswith(leading):
        s = s.replace(leading, '')
    return s.strip(os.sep)


def rst_to_html(rststr):
    from docutils.core import publish_string
    html = publish_string(rststr, writer_name='xml')
    el = ElementTree.fromstring(html)
    allparas = map(ElementTree.tostring, el)
    s = '\n'.join(allparas)
    s = s.replace('paragraph', 'p')
    s = s.replace('title', 'h1')
    s = s.replace('reference', 'a')
    s = s.replace('refuri', 'href')
    return s
