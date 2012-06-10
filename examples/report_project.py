#!/usr/bin/env python

import os

os.environ['path'] += os.pathsep + r'C:\Program Files (x86)\Graphviz 2.28\bin'

thisdir = os.path.dirname(__file__)
outdir = os.path.join(thisdir, 'exampleoutput')
pynocledir = os.path.join(thisdir, '..', 'pynocle')

def _get_coverage():
    import coverage
    try:
        cov = coverage.coverage()
    except Exception as exc:
        msg = exc.args[0]
        #Under debugger in pycharm, it uses the wrong coverage module!
        if msg == "__init__() got an unexpected keyword argument 'data_file'":
            return None
        if msg == "global name 'cache_location' is not defined":
            return None
        raise
    cov.start()
    oldcwd = os.getcwd()
    try:
        os.chdir(pynocledir)
        import pynocle
    finally:
        os.chdir(oldcwd)
    cov.stop()
    return cov


def run_on_pynocle():
    cov = _get_coverage()

    import pynocle
    m = pynocle.Monocle('Pynocle', outdir, rootdir=pynocledir, coveragedata=cov)
    m.generate_all()


if __name__ == '__main__':
    run_on_pynocle()
