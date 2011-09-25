"""pynocle is a module for reporting of code metrics and other inspection/reporting features.

It is meant to be used as a very simple API, usually as part of the the testing/build process.  Simply set up
your testing function (like nose.run) and pass it into Monocle.makeawesome, along with the directories you want
to analyze.
"""

__author__ = "Rob Galanakis"
__copyright__ = "Copyright 2011, Rob Galanakis"
__credits__ = ["Rob Galanakis"]
__license__ = "LGPL"
__version__ = "0.0.1"
__maintainer__ = "Rob Galanakis"
__email__ = "rob.galanakis@gmail.com"
__status__ = "Pre-Alpha"

import utils

try:
    import coverage
except ImportError as exc:
    coverage = utils.MissingDependencyError(repr(exc))
    pass
import os
import shutil

import cyclcompl
import depgraph
import sloc

def ensure_clean_output(outputdir, _ran=False):
    """rmtree and makedirs outputdir to ensure a clean output directory.

    outputdir: The folder to create.
    _ran: For internal use only.
    """
    #There is a potential race condition where rmtree seems to succeed and makedirs fails so
    #the directory doesn't exist.  So for the time being, if makedirs fails, we re-invoke the function once.
    #TODO: Figure out race condition.
    try:
        shutil.rmtree(outputdir)
    except WindowsError:
        pass
    try:
        os.makedirs(outputdir)
    except WindowsError:
        if not _ran:
            ensure_clean_output(outputdir, _ran=True)
        pass

def run_with_coverage(func, filename):
    """Runs func (parameterless callable) with coverage on.  Saves coverage to filename.  Returns a tuple
    of the return value of func, and the coverage object created.
    """
    #isinstance causes scope problems so use exact type checking here.
    if type(coverage) == utils.MissingDependencyError:
        raise coverage
    cov = coverage.coverage(data_file=filename)
    cov.erase()
    cov.start()
    result = func()
    cov.stop()
    cov.save()
    return result, cov

def generate_cover_html(cov, directory):
    """Outputs a coverage html report from cov into directory.

    cov: An instance of coverage.coverage.
    directory: The directory all the html files will be output to.  Directory must exist.
    """
    cov.html_report(directory=directory)

def generate_cover_report(cov, filename):
    """Generates a coverage report for cov to filename."""
    with open(filename, 'w') as f:
        cov.report(file=f)

def generate_cyclomatic_complexity(codefilenames, reportfilename, formatter_factory=None):
    """Generates a cyclomatic complexity report based on all the files in codefilenames, output to reportfilename.

    formatter_factory: Callable that takes the filestream of reportfilename and return the cyclcompl.CCFormatter
        to use to format the report.
    """
    ccdata, failures = cyclcompl.measure_cyclcompl(codefilenames)
    formatter_factory = formatter_factory or (lambda f: cyclcompl.CCTextFormatter(out=f))
    with open(reportfilename, 'w') as f:
        cyclcompl.format_cyclcompl(formatter_factory(f), ccdata, failures=failures)

def generate_sloc(codefilenames, reportfilename, formatter_factory=None):
    """Generates a Source Lines of Code report for files in codefilenames, output to reportfilename.

    formatter_factory: Callable that takes the filestream of reportfilename returns the sloc.ISlocFormatter to use
        to format the report.
    """
    slocgrp = sloc.SlocGroup(codefilenames)
    formatter_factory = formatter_factory or sloc.SlocTextFormatter
    with open(reportfilename, 'w') as f:
        sloc.format_slocgroup(slocgrp, formatter_factory(f))

def generate_dependency_graph(codefilenames, reportfilename, renderer_factory=None):
    """Generates a dependency graph image to reportfilename for the files in codefilenames.

    renderer: A callable that returns an depgraph.IRenderer instance and takes a collection of depgraph.Dependency
        instances and a collection of filenames that failed to parse as its args.  Defaults to depgraph.DefaultRenderer
    """
    depb = depgraph.DepBuilder(codefilenames)
    renderer_factory = renderer_factory or depgraph.DefaultRenderer
    renderer = renderer_factory(depb.dependencies, depb.failed)
    renderer.render(reportfilename)

def generate_coupling_report(codefilenames, reportfilename, formatter_factory=None):
    """Generates a report for Afferent and Efferent Coupling between all modules in codefilenames, saved to
    reportfilename.
    """
    depb = depgraph.DepBuilder(codefilenames)
    depgroup = depgraph.DependencyGroup(depb.dependencies, depb.failed)
    formatter_factory = formatter_factory or depgraph.CouplingTextFormatter
    with open(reportfilename, 'w') as f:
        depgraph.format_coupling(depgroup, formatter_factory(f))


def _generate_html_jump_str(htmlfilename, paths):
    """Generates the html contents for the jump page."""
    htmltemplate = '\n'.join(
        ['<html>',
        '  <head>',
        '    <title>Project Metrics, generated by pynocle.</title>',
        '  </head>',
        '  <body>',
        '%s',
        '  </body>',
        '</html>'])
    row = '      <a href="{0}">{0}</a>'
    absdir = os.path.dirname(os.path.abspath(htmlfilename)) + os.sep
    def hrefpath(p):
        absp = os.path.abspath(p)
        relp = absp.replace(absdir, '')
        return relp
    lines = [row.format(hrefpath(p)) for p in paths]
    return htmltemplate % '\n      <br />\n'.join(lines)

def generate_html_jump(filename, *paths):
    """Generates an html file at filename that contains links to all items in paths.

    filename: Filename of the resultant file.
    paths: Paths to all files the resultant file should display links to.
    """
    with open(filename, 'w') as f:
        f.write(_generate_html_jump_str(filename, sorted(paths)))

class Monocle(object):
    """Class that manages the filenames and default paths for the monocle methods.  Methods are the same as
    top-level module functions.
    """
    def __init__(self, outputdir='output', coveragedata_filename='.coverage', coverhtml_dir='report_covhtml',
                 coverreport_filename='report_coverage.txt', cyclcompl_filename='report_cyclcompl.txt',
                 sloc_filename='report_sloc.txt', depgraph_filename='depgraph.png',
                 coupling_filename='report_coupling.txt',
                 htmljump_filename='index.html', files_and_folders=(os.getcwd(),)):
        self.outputdir = outputdir
        join = lambda x: os.path.join(self.outputdir, x)
        self.coveragedata_filename = join(coveragedata_filename)
        self.coverhtml_dir = join(coverhtml_dir)
        self.coverreport_filename = join(coverreport_filename)
        self.cyclcompl_filename = join(cyclcompl_filename)
        self.sloc_filename = join(sloc_filename)
        self.depgraph_filename = join(depgraph_filename)
        self.coupling_filename = join(coupling_filename)
        self.htmljump_filename = join(htmljump_filename)
        self.filenames = utils.find_all(files_and_folders)
        self._filesforjump = []

    def ensure_clean_output(self):
        return ensure_clean_output(self.outputdir)

    def run_with_coverage(self, func):
        return run_with_coverage(func, self.coveragedata_filename)

    def generate_cover_html(self, cov):
        self._filesforjump.append(os.path.join(self.coverhtml_dir, 'index.html'))
        return generate_cover_html(cov, self.coverhtml_dir)

    def generate_cover_report(self, cov):
        self._filesforjump.append(self.coverreport_filename)
        return generate_cover_report(cov, self.coverreport_filename)

    def generate_cyclomatic_complexity(self, formatter_factory=None):
        self._filesforjump.append(self.cyclcompl_filename)
        return generate_cyclomatic_complexity(self.filenames, self.cyclcompl_filename,
                                              formatter_factory=formatter_factory)

    def generate_sloc(self, formatter_factory=None):
        self._filesforjump.append(self.sloc_filename)
        return generate_sloc(self.filenames, self.sloc_filename, formatter_factory=formatter_factory)

    def generate_dependency_graph(self, renderer_factory=None):
        self._filesforjump.append(self.depgraph_filename)
        return generate_dependency_graph(self.filenames, self.depgraph_filename, renderer_factory)

    def generate_coupling_report(self, formatter_factory=None):
        self._filesforjump.append(self.coupling_filename)
        return generate_coupling_report(self.filenames, self.coupling_filename, formatter_factory)
    
    def generate_html_jump(self):
        """Generates an html page that links to any generated reports."""
        return generate_html_jump(self.htmljump_filename, *self._filesforjump)

    def makeawesome(self, func):
        """Run ALL pynocle methods."""
        self.ensure_clean_output()
        result, cov = self.run_with_coverage(func)
        self.generate_cover_html(cov)
        self.generate_cover_report(cov)
        self.makeawesome_nocover()
        return result

    def makeawesome_nocover(self):
        self.generate_cyclomatic_complexity()
        self.generate_sloc()
        self.generate_dependency_graph()
        self.generate_coupling_report()
        self.generate_html_jump()

