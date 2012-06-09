#!/usr/bin/env python
import nose
import os
try:
    import coverage
except ImportError:
    coverage = None

def get_coverage():
        try:
            cov = coverage.coverage()
            cov.start()
            nose.run()
            cov.stop()
        except TypeError as exc:
            #Under debugger in pycharm, it uses the wrong coverage module!
            if exc.args[0] == "__init__() got an unexpected keyword argument 'data_file'":
                cov = None
            else:
                raise
        except NameError as exc:
            if exc.args[0] == "global name 'cache_location' is not defined":
                cov = None
            else:
                raise
        return cov


def run_on_pynocle():
    cov = get_coverage() if coverage else None

    import pynocle
    dirname = os.path.dirname(__file__)
    outdir = os.path.join(dirname, 'exampleoutput')
    m = pynocle.Monocle(outdir, rootdir=dirname, coveragedata=cov)
    m.generate_all()



if __name__ == '__main__':
    run_on_pynocle()
