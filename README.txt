                            pynocle, software metrics for python
                              Rob Galanakis rob.galanakis@gmail.com
                              www.robg3d.com

========
Overview
========

Pynocle is a python module and API for the generation of software metrics.  It aims to be as dead simple to use as
possible.  Simply create a pynocle.Monocle object, and call one of the makeawesome methods to generate all
supported metrics!  In the future, there will be much more configuration available.

Currently supported metrics include cyclomatic complexity, source lines of code, test coverage, and dependency graphs.
In the future, additional metrics will be supported.

For a rough understanding of code metrics, I'd encourage you to view the wikipedia pages:
http://en.wikipedia.org/wiki/Cyclomatic_complexity
http://en.wikipedia.org/wiki/Source_lines_of_code
http://en.wikipedia.org/wiki/Dependency_graph
http://en.wikipedia.org/wiki/Code_coverage

And NDepend, a fantastic code analysis tool for .NET, has a lot of good info: http://www.ndepend.com/Metrics.aspx


Usage
========

pynocle is meant to be used as a simple API from your own python code.  Simply import pynocle, create a Monocle
instance, and call one of the makeawesome methods (depending on if you want coverage or not).  That's it!

The internal API's are more complex and flexible and we'll be working on exposing that configuration as time goes by.

There is no commandline support, though commandline support for pynocle and its individual modules may be added later.


Dependencies
============

- Python 2.6 or higher
- For coverage support, requires the coverage module: http://pypi.python.org/pypi/coverage
- For dependency graph generation support, requires GraphViz's free software: http://www.graphviz.org/


Installation
============

There's currently no installation support, and there probably won't be until the API is greatly stabilized.
You can download the source from http://code.google.com/p/pynocle/, and just 'import pynocle' and you're ready to go!

Make sure you have GraphViz's 'dot' in your application path, and the coverage module installed, to use all features.


To Do
=====

- Add support for coupling metrics
  - http://codebetter.com/patricksmacchia/2008/02/15/code-metrics-on-coupling-dead-code-design-flaws-and-re-engineering/
  - Determine how to represent these conditions in the dependency graph.
  - Set up PageRank algorithm for weighing Ce.
  - Done
    - 9/25 Add Afferent Coupling (modules using it) and Efferent Coupling (modules it uses) support
    - 9/25 Create another report for coupling.
    
- Measure Number of Children (NOC) and Depth of Inheritance Tree (DIT)

Support
=======

Please email rob.galanakis@gmail.com if you have any questions, bugs, or want to help!


License and Contributions
=========================
Licensed under LGPL.  Copyright 2011 Robert Galanakis, rob.galanakis@gmail.com

This project uses a few pieces of code originally developed in pygenie, which measured cyclomatic complexity only.
Most of the code has been stripped out and only a few classes remain.  There is no functional homepage for the source
so I can't link anywhere.

