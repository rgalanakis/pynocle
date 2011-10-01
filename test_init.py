#!/usr/bin/env python

import nose
import os

if __name__ == '__main__':
    import _pynoclecover
    #Under debugger in pycharm, it uses the wrong coverage module!
    try:
        result, cov = _pynoclecover.run_with_coverage(nose.run)
    except TypeError as exc:
        if exc.args[0] == "__init__() got an unexpected keyword argument 'data_file'":
            cov = None
        else:
            raise
    except NameError as exc:
        if exc.args[0] == "global name 'cache_location' is not defined":
            cov = None
        else:
            raise
    import pynocle
    m = pynocle.Monocle(outputdir='exampleoutput', coveragedata=cov, rootdir=os.path.dirname(__file__))
    m.generate_all()