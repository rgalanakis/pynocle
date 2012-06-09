#!/usr/bin/env python
"""
pynocle is a module for reporting of code metrics and other
inspection/reporting features.

It is meant to be used as a very simple API,
usually as part of the the testing/build process.
Simply create a new Monocle object with the directories
and files you want to analyze (along with coverage data if you have it),
and call generate_all.
"""
import datetime
import os
import shutil
import sys

import cyclcompl
import depgraph
import sloc
import utils

#  * http://en.wikipedia.org/wiki/Dependency_graph
#  * http://en.wikipedia.org/wiki/Code_coverage


def ensure_clean_output(outputdir, _ran=0):
    """rmtree and makedirs outputdir to ensure a clean output directory.

    outputdir: The folder to create.
    _ran: For internal use only.
    """
    # There is a potential race condition where rmtree seems to succeed
    # and makedirs fails so the directory doesn't exist.
    # So for the time being, if makedirs fails, we re-invoke the function
    # 3 times.  I have observed this condition many times in the wild-
    # I don't want to believe it exists, but it does.
    try:
        shutil.rmtree(outputdir)
    except WindowsError:
        pass
    if os.path.exists(outputdir):
        raise IOError('%s was not deleted.' % outputdir)
    try:
        os.makedirs(outputdir)
    except WindowsError:
        if _ran < 3:
            ensure_clean_output(outputdir, _ran=_ran + 1)
        if not os.path.isdir(outputdir):
            raise


def _create_dependency_group(codefilenames):
    """Generates a new DependencyGroup from codefilenames."""
    depb = depgraph.DepBuilder(codefilenames)
    dependencygroup = depgraph.DependencyGroup(depb.dependencies, depb.failed)
    return dependencygroup


def generate_html_jump(htmlfilename, projectname, css_filename, jumpinfos):
    """Generates an html file at filename that contains links
    to all items in paths.

    :param htmlfilename: Filename of the resultant file.
    :param projectname: The name of the project metrics were generated for.
    :param css_filename: The path the css file for the reports.
    :param jumpinfos: Paths to all files the resultant file should
      display links to.
    """
    jumppaths = sorted(jumpinfos, key=lambda jump: jump[0])
    htmldir = os.path.dirname(os.path.abspath(htmlfilename))
    shutil.copy(css_filename, os.path.join(htmldir, 'pynocle.css'))

    def getJumpsHtml():
        rowtemplate = '<p><a href="{0}">{1}</a></p>'
        htmldirrepl = htmldir + os.sep
        def jumphtml(jumpinfo):
            reportpath, reportname = jumpinfo
            relpath = os.path.abspath(reportpath).replace(htmldirrepl, '')
            rowhtml = rowtemplate.format(relpath, reportname)
            return rowhtml
        return '\n'.join(map(jumphtml, jumpinfos))

    datestr = datetime.date.today().strftime('%b %d, %Y')
    jumpshtml = getJumpsHtml()

    def getLinksHtml():
        links = ['http://www.ndepend.com/Metrics.aspx',
                 'http://www.aivosto.com/project/help/pm-index.html']
        rowstrs = ['<li><a href="{0}">{0}</a></li>'.format(a) for a in links]
        html = """
<p>For an overview of metrics (and why things like pynocle
are important), check out the following pages:
  <ul>
    %s
  </ul>
</p>
""" % ('\n'.join(rowstrs))
        return html
    linkshtml = getLinksHtml()

    with open(htmlfilename, 'w') as f:
        fullhtml = """
    <html>
      <head>
        <title>%(projectname)s Project Metrics (by pynocle)</title>
        <link rel="stylesheet" type="text/css" href="pynocle.css" media="screen" />
      </head>
      <body>
        <h1>Metrics for %(projectname)s</h1>
        <p>The following reports have been generated for the project %(projectname)s by pynocle.<br />
        View reports for details, and information about what report is and suggested actions.</p>
    %(jumpshtml)s
    %(linkshtml)s
    <br />
    <div class="footer">
    <p>Metrics generated on %(datestr)s<br />
    <a href="http://code.google.com/p/pynocle/">Pynocle</a> copyright
    <a href="http://robg3d.com">Rob Galanakis</a> 2012</p>
    </div>
      </body>
    </html>
    """ % locals()
        f.write(fullhtml)


class Monocle(object):
    """Entry point for all metrics generation.

    :param outputdir: Directory to write reports.
    :param rootdir: The root directory of the python files to search.
      If None, use the cwd.
    :param coveragedata: A coverage.coverage instance.
      You can get this from running coverage,
      or loading a coverage data file.
    :param css_filename: The path to the css file. Uses default.css if None.
    """
    def __init__(self,
                 projectname,
                 outputdir,
                 rootdir=None,
                 coveragedata=None,
                 css_filename=None):
        self.rootdir = os.path.abspath(rootdir or os.getcwd())
        self.filenames = list(utils.walk_recursive(self.rootdir))

        self.projectname = projectname
        self.outputdir = outputdir
        self.coveragedata = coveragedata

        join = lambda x: os.path.join(self.outputdir, x)
        self.coverhtml_dir = join('report_covhtml')
        self.cyclcompl_filename = join('report_cyclcompl.html')
        self.sloc_filename = join('report_sloc.html')
        self.depgraph_filename = join('depgraph.png')
        self.coupling_filename = join('report_coupling.html')
        self.couplingrank_filename = join('report_couplingrank.html')
        self.htmljump_filename = join('index.html')

        if css_filename is None:
            css_filename = os.path.join(
                os.path.dirname(__file__), 'default.css')
        self.css_filename = css_filename

        self._filesforjump = {}

    def ensure_clean_output(self):
        ensure_clean_output(self.outputdir)

    def generate_cover_html(self):
        """Outputs a coverage html report from cov into directory."""
        self.coveragedata.html_report(directory=self.coverhtml_dir)
        p = os.path.join(self.coverhtml_dir, 'index.html')
        self._filesforjump[p] = p, 'Report: Coverage'

    def generate_cyclomatic_complexity(self):
        """Generates a cyclomatic complexity report for all files in self.files,
        output to self.cyclcompl_filename.
        """
        ccdata, failures = cyclcompl.measure_cyclcompl(self.filenames)
        def makeFormatter(f):
            return cyclcompl.CCGoogleChartFormatter(
                f, leading_path=self.rootdir)
        p = self.cyclcompl_filename
        utils.write_report(p, (ccdata, failures), makeFormatter)
        self._filesforjump[p] = p, 'Report: Cyclomatic Complexity'

    def generate_sloc(self):
        """Generates a Source Lines of Code report for all files in self.files,
        output to self.sloc_filename.
        """
        slocgrp = sloc.SlocGroup(self.filenames)
        def makeSlocFmt(f):
            return sloc.SlocGoogleChartFormatter(f, self.rootdir)
        p = self.sloc_filename
        utils.write_report(p, slocgrp, makeSlocFmt)
        self._filesforjump[p] = p, 'Report: SLOC'

    def generate_dependency_graph(self, depgrp):
        """Generates a dependency graph image to self.depgraph_filename
        for the files in self.files.
        """
        renderer = depgraph.DefaultRenderer(depgrp, leading_path=self.rootdir)
        p = self.depgraph_filename
        renderer.render(p)
        self._filesforjump[p] = p, 'Report: Dependency Graph'

    def generate_coupling_report(self, depgrp):
        """Generates a report for Afferent and Efferent Coupling between
        all modules in self.filenames,
        saved to self.coupling_filename
        """
        def factory(f):
            return depgraph.CouplingGoogleChartFormatter(f, self.rootdir)
        p = self.coupling_filename
        utils.write_report(p, depgrp, factory)
        self._filesforjump[p] = p, 'Report: Coupling'

    def generate_couplingrank_report(self, depgrp):
        """Generates a PageRank report for all code in self.filenames to
        self.couplingrank_filename.
        """
        def factory(f):
            return depgraph.RankGoogleChartFormatter(f, self.rootdir)
        p = self.couplingrank_filename
        utils.write_report(p, depgrp, factory)
        self._filesforjump[p] = p, 'Report: Coupling PageRank'

    def generate_html_jump(self):
        """Generates an html page that links to any generated reports."""
        return generate_html_jump(
            self.htmljump_filename,
            self.projectname,
            self.css_filename,
            self._filesforjump.values())

    def generate_all(self, cleanoutput=True):
        """Run all report generation functions.

        If coveragedata is not set, skip the coverage functions.

        :param cleanoutput: If True, run ensure_clean_output to clear
          the output directory.
        """
        if cleanoutput:
            self.ensure_clean_output()
        exc_infos = []
        def trydo(func):
            try:
                return func()
            except Exception:
                exc_infos.append(sys.exc_info())

        trydo(self.generate_sloc)
        trydo(self.generate_cyclomatic_complexity)

        if self.coveragedata:
            trydo(self.generate_cover_html)

        depgrp = _create_dependency_group(self.filenames)
        trydo(lambda: self.generate_coupling_report(depgrp))
        trydo(lambda: self.generate_couplingrank_report(depgrp))
        trydo(lambda: self.generate_dependency_graph(depgrp))
        trydo(self.generate_html_jump)
        #self.generate_funcinfo_report,
        #self.generate_inheritance_report,
        if exc_infos:
            raise utils.AggregateError(exc_infos)
