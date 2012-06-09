
def about_coupling():
    return """
Coupling
--------

Coupling measures how closely bound two modules are.  Afferent coupling (Ca)
measures how many modules reference a given module.  Efferent coupling
(Ce) measures how many modules a given module referenecs.  Afferent
coupling of 0 can indicate dead code, since nothing references it,
with various exceptions (test module, entry points, dynamic references,
configuration, etc.).  High efferent coupling means a module is
very dependent on other modules and has a high liklihood of change.

Instability measures the ratio Ce / (Ca + Ce), so a module that depends
on nothing is considered fully stable (it would not change if something
else changes), and a module that depends highly on others is considered
unstable (high liklihood of changing if another module changes).

For more info about coupling, see `the Wikipedia article on coupling
<http://en.wikipedia.org/wiki/Coupling_(computer_programming)>`_.
"""


def about_rank():
    return """
Coupling/Module Rank
--------------------

Coupling only tells a part of the story. Imagine you have a helper package,
and the package root (__init__) is used by every other module in your system.
However there may be several 'implementation' modules in this helper package,
which while having very low coupling (they are only referred to by
the __init__.py file), are indirectly very important for your application.

This situation is very much like the ranking of web pages.
We can use the Google PageRank algorithm to determine how important
all modules are.

The most highly ranked modules should have
the most thorough testing since the most amount of code is dependent
upon them.

For more info about coupling, see `the Wikipedia article on coupling
<http://en.wikipedia.org/wiki/Coupling_(computer_programming)>`_.

For more information about PageRank, see `the Wikipedia article on PageRank
<http://en.wikipedia.org/wiki/Page_rank>`_.
"""
