#!/usr/bin/env python
"""This script can be imported to help generate a pynocle report
for a project.

You will need coverage installed to use it,
and pynocle should be in your sys path so it can be imported.
"""

import os
import tempfile

os.environ['path'] += os.pathsep + r'C:\Program Files (x86)\Graphviz 2.28\bin'


def _get_coverage(projectname, docoverwork, regencover):
    import coverage
    covfile = os.path.join(tempfile.gettempdir(), projectname + '.coverage')
    cov = coverage.coverage(data_file=covfile)

    if not regencover and os.path.exists(covfile):
        cov.load()
        return cov

    cov.start()
    docoverwork()
    cov.stop()
    cov.save()
    return cov


def nose_dir(cwd):
    import nose
    old = os.getcwd()
    try:
        os.chdir(cwd)
        nose.run()
    finally:
        os.chdir(old)


def run_project(projectname, rootdir, outdir,
                docoverwork=None, regencover=True):
    """Generates a pynocle report for a project.

    :param projectname: The name of the project.
    :param rootdir: The root directory of the files to analyze.
    :param outdir: The folder to place report files.
    :param docoverwork: Parameterless callable invoked under coverage
      that the coverage report will be generated from.
      If None, do not generate coverage.
    :param regencover: By default, this script will cache a .coverage
      file for the project in the temp folder. If `regencover`,
      this cache will be regenerated.
    """
    cov = None
    if docoverwork:
        cov = _get_coverage(projectname, docoverwork, regencover)
    import pynocle
    m = pynocle.Monocle(
        projectname, outdir, rootdir=rootdir, coveragedata=cov)
    m.generate_all()
