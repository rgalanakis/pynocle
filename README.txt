**pynocle, software metrics for python**
Rob Galanakis rob.galanakis@gmail.com
http://www.robg3d.com

========
Overview
========

Pynocle is a python module and API for the generation of software metrics.
It aims to be as dead simple to use as possible.  Simply create a
pynocle.Monocle object, and call generate_all to generate all supported
metrics!  In the future, there will be much more configuration available.

Currently supported metrics include:
    * cyclomatic complexity
    * lines of code (source, comment, blank, total)
    * test coverage
    * dependency graphing
    * coupling measurement
    * module ranking
    
In the future, additional metrics will be supported.  For more information
about what metrics mean what, see the Description of Metrics section below.

=====
Usage
=====

pynocle is meant to be used as a simple API from your own python code.
Simply import pynocle, create a Monocle instance, and
the generate_all method.  That's it!

To generate coverage, you can pass a parameterless function (like nose.run)
into pynocle.run_with_coverage.  Pass any coverage.coverage instance
into Monocle.coverdata in order to generate coverage reports.

The internal API's are more complex and flexible and we'll be working
on exposing that configuration as time goes by.

There is no commandline support, though commandline support for pynocle
and its individual modules may be added later.

============
Dependencies
============

 * Python 2.6 or higher
 * The docutils module.
 * For coverage support, requires the coverage module:
   http://pypi.python.org/pypi/coverage
 * For dependency graph generation support, requires GraphViz's
   free software: http://www.graphviz.org/
 * For page ranking algorithm, requires numpy.


============
Installation
============

Run setup.py to install pynocle and python dependencies.

Make sure you have GraphViz's 'dot' in your application path to use
dependency graph visualization features.  This will be configurable
in the future.


=======
Support
=======

Please email rob.galanakis@gmail.com if you have any questions,
bugs, or want to help!

Fork the Hg repository at http://code.google.com/p/pynocle/


=========================
License and Contributions
=========================

Pynocle is released under the MIT license.

Copyright 2011 Robert Galanakis, rob.galanakis@gmail.com.

I owe a huge thanks to Patrick Smacchia and the NDepend (www.ndepend.com)
team.  NDepend, is a fantastic code
analysis tool for .NET, and I owe a large number of the ideas and metrics
to them.

This project uses a few pieces of code originally developed in pygenie,
which measured cyclomatic complexity only. Most of the code has been
stripped out and only a few classes remain. There is no functional
homepage for the source so I can't link anywhere.

======================
Description of Metrics
======================

A generated metrics report will have more information about software metrics,
and links for additional info.

See the example output for more info, available here:

You can look at any good static analysis tool and wikipedia to get
overviews of various code metrics:

  * http://www.ndepend.com/Metrics.aspx
  * http://www.aivosto.com/project/help/pm-index.html




