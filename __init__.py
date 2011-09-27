#!/usr/bin/env python
"""
pynocle is a module for reporting of code metrics and other inspection/reporting features.

It is meant to be used as a very simple API, usually as part of the the testing/build process.  Simply
create a new Monocle object with the directories and files you want to analyze
(along with coverage data if you have it), and call generate_all.
"""

__author__ = "Rob Galanakis"
__copyright__ = "Copyright 2011, Rob Galanakis"
__version__ = "0.1.21"
__email__ = "rob.galanakis@gmail.com"
__status__ = "Pre-Alpha"

import pynocle.utils as utils

try:
    import coverage
except ImportError as exc:
    coverage = utils.MissingDependencyError(repr(exc))
    pass
import os
import shutil

import _pynoclecover
import cyclcompl
import depgraph
import inheritance
import sloc

def _check_coverage():
    if type(coverage) == utils.MissingDependencyError:
        raise coverage

def run_with_coverage(func, **coveragekwargs):
    _check_coverage()
    return _pynoclecover.run_with_coverage(func, **coveragekwargs)

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
    if os.path.exists(outputdir):
        raise IOError, '%s was not deleted.' % outputdir
    try:
        os.makedirs(outputdir)
    except WindowsError:
        if not _ran:
            ensure_clean_output(outputdir, _ran=True)
        if not os.path.isdir(outputdir):
            raise

def generate_cover_html(cov, directory):
    """Outputs a coverage html report from cov into directory.

    cov: An instance of coverage.coverage.
    directory: The directory all the html files will be output to.  Directory must exist.
    """
    #isinstance causes scope problems so use exact type checking here.
    _check_coverage()
    cov.html_report(directory=directory)

def generate_cover_report(cov, filename):
    """Generates a coverage report for cov to filename."""
    #isinstance causes scope problems so use exact type checking here.
    _check_coverage()
    with open(filename, 'w') as f:
        cov.report(file=f)

def generate_cyclomatic_complexity(codefilenames, reportfilename, formatter_factory=None):
    """Generates a cyclomatic complexity report based on all the files in codefilenames, output to reportfilename.

    formatter_factory: Callable that takes the filestream of reportfilename and return the cyclcompl.CCFormatter
        to use to format the report.
    """
    ccdata, failures = cyclcompl.measure_cyclcompl(codefilenames)
    factory = formatter_factory or cyclcompl.CCTextFormatter
    utils.write_report(reportfilename, (ccdata, failures), factory)

def generate_sloc(codefilenames, reportfilename, formatter_factory=None):
    """Generates a Source Lines of Code report for files in codefilenames, output to reportfilename.

    formatter_factory: Callable that takes the filestream of reportfilename returns the sloc.ISlocFormatter to use
        to format the report.
    """
    slocgrp = sloc.SlocGroup(codefilenames)
    formatter_factory = formatter_factory or sloc.SlocTextFormatter
    utils.write_report(reportfilename, slocgrp, formatter_factory)

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
    utils.write_report(reportfilename, depgroup, formatter_factory)

def generate_couplingrank_report(codefilenames, reportfilename, formatter_factory=None):
    """Generates a PageRank report for all modules in codefilenames, saved to reportfilename.

    formatter_factory: Callable that returns an ICouplingFormatter instance.
    """
    factory = formatter_factory or depgraph.formatting.RankTextFormatter
    generate_coupling_report(codefilenames, reportfilename, formatter_factory=factory)

def generate_inheritance_report(codefilenames, reportfilename, formatter_factory=None):
    classgroup = inheritance.ClassGraph(inheritance.InheritanceBuilder(codefilenames).classinfos())
    with open(reportfilename, 'w') as f:
        f.write('Functionality not yet supported!\n\n')
        f.write(repr(classgroup))

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

    outputdir: Directory relative to cwd to write files.
    files_and_folders: All files and files recursively under directories in this collection will be reported on.
    coveragedata: A coverage.coverage instance.  You can get this from running coverage, or loading a coverage data
        file.

    Other arguments are filenames relative to outputdir that reports will be written to,
    and factory methods that are used to output those reports.
    """
    def __init__(self, outputdir='output',
                 files_and_folders=(os.getcwd(),),
                 coveragedata=None,
                 coverhtml_dir='report_covhtml',
                 coverreport_filename='report_coverage.txt',
                 cyclcompl_filename='report_cyclcompl.txt',
                 cyclcompl_fmtfactory=None,
                 sloc_filename='report_sloc.txt',
                 sloc_fmtfactory=None,
                 depgraph_filename='depgraph.png',
                 depgraph_renderfactory=None,
                 coupling_filename='report_coupling.txt',
                 coupling_fmtfactory=None,
                 couplingrank_filename='report_couplingrank.txt',
                 couplingrank_fmtfactory=None,
                 inheritance_filename='report_inheritance.txt',
                 inheritance_fmtfactory=None,
                 htmljump_filename='index.html',
                 ):
        self.outputdir = outputdir
        self.filenames = utils.find_all(files_and_folders)
        self.coveragedata = coveragedata

        join = lambda x: os.path.join(self.outputdir, x)
        self.coverhtml_dir = join(coverhtml_dir)
        self.coverreport_filename = join(coverreport_filename)
        self.cyclcompl_filename = join(cyclcompl_filename)
        self.sloc_filename = join(sloc_filename)
        self.depgraph_filename = join(depgraph_filename)
        self.coupling_filename = join(coupling_filename)
        self.couplingrank_filename = join(couplingrank_filename)
        self.inheritance_filename = join(inheritance_filename)
        self.htmljump_filename = join(htmljump_filename)

        self.cyclcompl_fmtfactory = cyclcompl_fmtfactory
        self.sloc_fmtfactory = sloc_fmtfactory
        self.depgraph_renderfactory = depgraph_renderfactory
        self.coupling_fmtfactory = coupling_fmtfactory
        self.couplingrank_fmtfactory = couplingrank_fmtfactory
        self.inheritance_fmtfactory = inheritance_fmtfactory

        self._filesforjump = []

    def ensure_clean_output(self):
        ensure_clean_output(self.outputdir)

    def generate_cover_html(self):
        generate_cover_html(self.coveragedata, self.coverhtml_dir)
        self._filesforjump.append(os.path.join(self.coverhtml_dir, 'index.html'))

    def generate_cover_report(self):
        generate_cover_report(self.coveragedata, self.coverreport_filename)
        self._filesforjump.append(self.coverreport_filename)

    def generate_cyclomatic_complexity(self):
        generate_cyclomatic_complexity(self.filenames, self.cyclcompl_filename, self.cyclcompl_fmtfactory)
        self._filesforjump.append(self.cyclcompl_filename)

    def generate_sloc(self):
        generate_sloc(self.filenames, self.sloc_filename, self.sloc_fmtfactory)
        self._filesforjump.append(self.sloc_filename)

    def generate_dependency_graph(self):
        generate_dependency_graph(self.filenames, self.depgraph_filename, self.depgraph_renderfactory)
        self._filesforjump.append(self.depgraph_filename)

    def generate_coupling_report(self):
        generate_coupling_report(self.filenames, self.coupling_filename, self.coupling_fmtfactory)
        self._filesforjump.append(self.coupling_filename)

    def generate_couplingrank_report(self):
        generate_couplingrank_report(self.filenames, self.couplingrank_filename, self.couplingrank_fmtfactory)
        self._filesforjump.append(self.couplingrank_filename)

    def generate_inheritance_report(self):
        generate_inheritance_report(self.filenames, self.inheritance_filename, self.inheritance_fmtfactory)
        self._filesforjump.append(self.inheritance_filename)
    
    def generate_html_jump(self):
        """Generates an html page that links to any generated reports."""
        return generate_html_jump(self.htmljump_filename, *self._filesforjump)

    def generate_all(self, cleanoutput=True):
        """Run all report generation functions.

        If coveragedata is not set, skip the coverage functions.
        Raises an AggregateError after all functions run if any function raises.
        cleanoutput: If True, run ensure_clean_output to clear the output directory.
        """
        if cleanoutput:
            self.ensure_clean_output()
        funcs = [self.generate_inheritance_report,
                     self.generate_cyclomatic_complexity,
                     self.generate_sloc,
                     self.generate_coupling_report,
                     self.generate_couplingrank_report,
                     self.generate_dependency_graph,
                     self.generate_html_jump]
        if self.coveragedata:
            funcs.insert(0, self.generate_cover_html)
            funcs.insert(0, self.generate_cover_report)
        excs = []
        for func in funcs:
            try:
                func()
            except Exception as exc:
                import traceback
                excs.append((exc, traceback.format_exc()))
        if excs:
            raise utils.AggregateError, excs
