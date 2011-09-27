**pynocle, software metrics for python**
Rob Galanakis rob.galanakis@gmail.com
http://www.robg3d.com

========
Overview
========

Pynocle is a python module and API for the generation of software metrics.  It aims to be as dead simple to use as
possible.  Simply create a pynocle.Monocle object, and call generate_all to generate all
supported metrics!  In the future, there will be much more configuration available.

Currently supported metrics include:
    * cyclomatic complexity
    * lines of code (source, comment, blank, total)
    * test coverage
    * dependency graphing
    * coupling measurement
    * module ranking
    
In the future, additional metrics will be supported.  For more information about what metrics mean what, see
the Description of Metrics section below.

=====
Usage
=====

pynocle is meant to be used as a simple API from your own python code.  Simply import pynocle, create a Monocle
instance, and the generate_all method.  That's it!

To generate coverage, you can pass a parameterless function (like nose.run) into pynocle.run_with_coverage.  Pass any
coverage.coverage instance into Monocle.coverdata in order to generate coverage reports.

The internal API's are more complex and flexible and we'll be working on exposing that configuration as time goes by.

There is no commandline support, though commandline support for pynocle and its individual modules may be added later.

============
Dependencies
============

 * Python 2.6 or higher
 * For coverage support, requires the coverage module: http://pypi.python.org/pypi/coverage
 * For dependency graph generation support, requires GraphViz's free software: http://www.graphviz.org/
 * For page ranking algorithm, requires numpy.

============
Installation
============

Run setup.py to install pynocle and python dependencies.

Make sure you have GraphViz's 'dot' in your application path to use dependency graph visualization features.

=====
To Do
=====

- Add support for coupling metrics
  - http://codebetter.com/patricksmacchia/2008/02/15/code-metrics-on-coupling-dead-code-design-flaws-and-re-engineering/
  - Determine how to represent these conditions in the dependency graph.
  - Done
    - 9/25 Set up PageRank algorithm for weighing Ce.
    - 9/25 Add Afferent Coupling (modules using it) and Efferent Coupling (modules it uses) support
    - 9/25 Create another report for coupling.

- Additional metrics to support (http://www.ndepend.com/Metrics.aspx)
  - Number of subclasses
  - Depth of baseclasses
  - Number of baseclasses
  - Function parameter count
  - Function variables

- Start using some markup and ideally sortable tables, rather than crappy plain text!


=======
Support
=======

Please email rob.galanakis@gmail.com if you have any questions, bugs, or want to help!

Fork the Hg repository at http://code.google.com/p/pynocle/


=========================
License and Contributions
=========================

See LICENSE.txt for more info.

Copyright 2011 Robert Galanakis, rob.galanakis@gmail.com.

I owe a huge thanks to Patrick Smacchia and the NDepend (www.ndepend.com) team.  NDepend, is a fantastic code
analysis tool for .NET, and I owe a large number of the ideas and metrics to them.

This project uses a few pieces of code originally developed in pygenie, which measured cyclomatic complexity only.
Most of the code has been stripped out and only a few classes remain.  There is no functional homepage for the source
so I can't link anywhere.

======================
Description of Metrics
======================

You can look at any good static analysis tool and wikipedia to get overviews of various code metrics:
  * http://www.ndepend.com/Metrics.aspx
  * http://www.aivosto.com/project/help/pm-index.html
  * http://en.wikipedia.org/wiki/Cyclomatic_complexity
  * http://en.wikipedia.org/wiki/Source_lines_of_code
  * http://en.wikipedia.org/wiki/Dependency_graph
  * http://en.wikipedia.org/wiki/Code_coverage

SLOC (Source Lines of Code)
--------------------------_
Useful to see the general size and distribution of code across the codebase.  The number of bugs in a codebase can
be said in general to be proportional to its lines of code, but this code metric is most useful in understanding
the codebase, rather than finding quality issues.

Cyclomatic Complexity
---------------------
CC measures the number of decisions of piece of code can make (flow control such as if/then, try/catch, for, while,
break, continue, etc.).  Values between 1-9 are considered ideal.  Values between 10-20 are considered acceptable
depending on the use (they can indicate poor design, or inherently tricky areas).  Values higher than 20 should
be considered unacceptable and must be refactored.  Generally high CC indicates code is difficult to understand,
far away from polymorphism, and has a high liklihood of introducing bugs during bugfixing or maintenance.

Coupling
--------
Coupling measures how closely bound two modules are.  Afferent coupling (Ca) measures how many modules reference
a given module.  Efferent coupling (Ce) measures how many modules a given module referenecs.  Afferent
coupling of 0 can indicate dead code, since nothing references it, with various exceptions (test module, entry
points, dynamic references, configuration, etc.).  High efferent coupling means a module is very dependent on other
modules and has a high liklihood of change.

Instability measures the ratio Ce / (Ca + Ce), so a module that depends on nothing is considered fully stable, and a
module that depends on others entirely is considered entirely unstable.

Coupling/Module Rank
--------------------
Coupling only tells a part of the story.  Imagine you have a few helper classes used by a core library that every
other module references.  The Ca of those helpers would be low, but they would be very important.  So we can use
the Google PageRank algorithm to determine a weight of important of all modules.  The most highly ranked modules
should have the most thorough testing since the most amount of code is dependent upon them.
 

