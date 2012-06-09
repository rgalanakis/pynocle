#!/usr/bin/env python

def about():
    return """
Cyclomatic Complexity
---------------------

Cyclomatic Complexity measures the number of decisions of piece of code can make
(flow control such as if/then, try/catch, for, while, break, continue,
etc.).  Values between 1-9 are considered ideal.  Values between 10-20 are
considered acceptable depending on the use (they can indicate poor design,
or inherently tricky areas).  Values higher than 20 should be considered
unacceptable and must be refactored.
Generally, high CC indicates code is difficult to understand,
far away from polymorphism, and has a high
liklihood of introducing bugs during bugfixing or maintenance.

Values <= 10 are fine, between 11 and 20 should be refactored,
and values above 20 are usually considered unacceptable
and should be refactored.

For more info, see `the Wikipedia article on cyclomatic complexity
<http://en.wikipedia.org/wiki/Cyclomatic_complexity>`_.
"""
