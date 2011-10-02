#!/usr/bin/env python

import nose
import os
import sys

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
    #os.chdir('..')
    dirname = os.path.dirname(__file__)
    m = pynocle.Monocle(outputdir=os.path.join(dirname, 'exampleoutput'), coveragedata=cov, rootdir=dirname)
    #root = os.path.join(dirname, '..', 'pipeline')
    #sys.path.append(root)
    #m = pynocle.Monocle(outputdir=r'C:\testmetrics', rootdir=root)
    m.generate_all()