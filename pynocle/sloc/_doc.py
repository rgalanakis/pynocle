#!/usr/bin/env python

def about():
    return """
SLOC (Source Lines of Code)
---------------------------

Useful to see the general size and distribution of code across the codebase.
The number of bugs in a codebase can be said in general to be proportional
to its lines of code, but this code metric is most useful in understanding
the codebase, rather than finding quality issues.

Measures physical source lines of code (SLOC), lines of comments,
and blank lines, in number and percentage of file.

Also measures total line count and as percentage of total codebase lines.

For more info, see `the Wikipedia article on SLOC
<http://en.wikipedia.org/wiki/Source_lines_of_code>`_.
"""
