#!/usr/bin/env python
"""
Small module that contains the 'run_with_coverage' method so that pynocle test coverage doesn't import it before
it starts coverage.
"""
import coverage

def run_with_coverage(func, **coveragekwargs):
    cov = coverage.coverage(**coveragekwargs)
    cov.start()
    result = func()
    cov.stop()
    cov.save()
    return result, cov