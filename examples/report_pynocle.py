#!/usr/bin/env python

import os

if __name__ == '__main__':
    thisdir = os.path.dirname(__file__)
    outdir = os.path.join(thisdir, 'exampleoutput')
    pynocledir = os.path.join(thisdir, '..', 'pynocle')

    import report_project
    runtests = report_project.run_nose(pynocledir)
    report_project.report_project('Pynocle', pynocledir, outdir, runtests)
