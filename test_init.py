#!/usr/bin/env python

import nose

if __name__ == '__main__':
    import _pynoclecover
    try:
        result, cov = _pynoclecover.run_with_coverage(nose.run)
    except TypeError as exc:
        #Under debugger in pycharm, it uses the wrong coverage module!
        if exc.args[0] == "__init__() got an unexpected keyword argument 'data_file'":
            cov = None
        else:
            raise
    import pynocle
    m = pynocle.Monocle(outputdir='exampleoutput', coveragedata=cov)
    m.generate_all()