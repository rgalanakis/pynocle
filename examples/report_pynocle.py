#!/usr/bin/env python

import os

if __name__ == '__main__':
    thisdir = os.path.dirname(__file__)
    outdir = os.path.join(thisdir, 'exampleoutput')
    pynocledir = os.path.join(thisdir, '..', 'pynocle')

    import report_project
    def runtests():
        report_project.nose_dir(pynocledir)
    report_project.run_project('Pynocle', pynocledir, outdir, runtests)

