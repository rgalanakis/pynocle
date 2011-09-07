#!/usr/bin/env python
"""Contains functionality for calculating the Cyclomatic Complexity of python code.  Originally from pygenie (I cannot
find a reliable home base for it), but significantly refactored for clarity and documentation.
"""

import compiler
from compiler.visitor import ASTVisitor

class Stats(object):
    """The base class for other types of statistics."""
    def __init__(self, name):
        self.name = name
        self.classes = []
        self.functions = []
        self.complexity = 1

    def __str__(self):
        return 'Stats: name=%r, classes=%r, functions=%r, complexity=%r' \
                % (self.name, self.classes, self.functions, self.complexity)

    __repr__ = __str__


class ClassStats(Stats):
    """Represents the statistics for a class."""
    def __str__(self):
        return 'Stats: name=%r, methods=%r, complexity=%r, inner_class=%r' \
                % (self.name, self.functions, self.complexity, self.classes)

    __repr__ = __str__


class DefStats(Stats):

    def __str__(self):
        return 'DefStats: name=%r, complexity=%r' \
                % (self.name, self.complexity)

    __repr__ = __str__


class FlatStats(object):
    """Create list of flat stats

       stats in init and flattenStats is of type class Stats
       flatStats is a list of lists with each list containing
       'C/M/F/X', Name, complexity
       summaryStats is a dictionary with keys X/C/M/F/T and value is
       a list of [count, complexity]
    """

    def __init__(self, stats=None):
        self.summaryStats = {'File':[0, 0],
                             'Clss':[0, 0],
                             'Meth':[0, 0],
                             'Func':[0, 0],
                             'Totl':[0, 0]}
        if stats:
            self.flatStats = self.flattenStats(stats)
            self.computeSummary()

    def flattenStats(self, stats):
        def flatten(stats, ns=None):
            if not ns:
                yield 'File', stats.name, stats.complexity
            for s in stats.classes:
                name = '.'.join(filter(None, [ns, s.name]))
                yield 'Clss', name, s.complexity
                for x in s.functions:
                    fname = '.'.join([name, x.name])
                    yield 'Meth', fname, x.complexity
            for s in stats.functions:
                name = '.'.join(filter(None, [ns, s.name]))
                yield 'Func', name, s.complexity

        return [t for t in flatten(stats)]

    def computeSummary(self):
        count = 0
        complexity = 0
        for row in self.flatStats:
            self.summaryStats[row[0]][0] = self.summaryStats[row[0]][0] + 1
            self.summaryStats['Totl'][0] = self.summaryStats['Totl'][0] + 1
            self.summaryStats[row[0]][1] = self.summaryStats[row[0]][1] + row[2]
            self.summaryStats['Totl'][1] = self.summaryStats['Totl'][1] + row[2]

    def __add__(self, other):
        """addition is only for summary stats"""
        result = FlatStats()
        for idx in 'File', 'Clss', 'Meth', 'Func', 'Totl':
            for i in range(2):
                result.summaryStats[idx][i] = self.summaryStats[idx][i] + other.summaryStats[idx][i]
        return result

    def __str__(self):
        lines = ['----------------------------------',
                 'Type         Count      Complexity',
                 '----------------------------------']
        for idx in 'File', 'Clss', 'Meth', 'Func', 'Totl':
            lines.append('%s     %8d         %8d' % (idx, self.summaryStats[idx][0], self.summaryStats[idx][1]))
        lines.append('----------------------------------\n')
        return '\n'.join(lines)


class CCVisitor(ASTVisitor):
    """Encapsulates the cyclomatic complexity counting."""

    def __init__(self, ast, stats=None, description=None):
        ASTVisitor.__init__(self)
        if isinstance(ast, basestring):
            ast = compiler.parse(ast)

        self.stats = stats or Stats(description or '<module>')
        for child in ast.getChildNodes():
            compiler.walk(child, self, walker=self)

    def dispatchChildren(self, node):
        for child in node.getChildNodes():
            self.dispatch(child)

    def visitFunction(self, node):
        if not hasattr(node, 'name'): # lambdas
            node.name = '<lambda>'
        stats = DefStats(node.name)
        stats = CCVisitor(node, stats).stats
        self.stats.functions.append(stats)

    visitLambda = visitFunction

    def visitClass(self, node):
        stats = ClassStats(node.name)
        stats = CCVisitor(node, stats).stats
        self.stats.classes.append(stats)

    def visitIf(self, node):
        self.stats.complexity += len(node.tests)
        self.dispatchChildren(node)

    def __processDecisionPoint(self, node):
        self.stats.complexity += 1
        self.dispatchChildren(node)

    visitFor = visitGenExprFor = visitGenExprIf \
            = visitListCompFor = visitListCompIf \
            = visitWhile = _visitWith = __processDecisionPoint

    def visitAnd(self, node):
        self.dispatchChildren(node)
        self.stats.complexity += 1

    def visitOr(self, node):
        self.dispatchChildren(node)
        self.stats.complexity += 1


def measure_complexity(ast, module_name=None, stats=None):
    try:
        return FlatStats(CCVisitor(ast, stats, module_name).stats)
    except Exception:
        return None 


class Table(object):

    def __init__(self, headings, rows):
        self.headings = headings
        self.rows = rows

        max_col_sizes = [len(x) for x in headings]
        for row in rows:
            for i, col in enumerate(row):
                max_col_sizes[i] = max(max_col_sizes[i], len(str(col)))
        self.max_col_sizes = max_col_sizes

    def __iter__(self):
        for row in self.rows:
            yield row

    def __nonzero__(self):
        return len(self.rows)

class PrettyPrinter(object):

    def __init__(self, out, complexity=False, threshold=7, summary=False):
        self.out = out
        self.complexity = complexity
        self.threshold = threshold
        self.summary = summary

    def pprint(self, filename, stats):
        if self.complexity or self.summary:
            self.out.write('File: %s\n' % filename)
            if self.complexity:
                self.pprint_complexity(stats.flatStats)
            if self.summary:
                self.pprint_summary(stats)
            self.out.write('\n')

    def pprint_complexity(self, stats):
        # filter out suites with low complexity numbers
        stats = (row for row in stats if row[-1] > self.threshold)

        stats = sorted(stats, lambda a, b: cmp(b[2], a[2]))

        table = Table(['Type', 'Name', 'Complexity'], stats)
        if table:
            self.pprint_table(table)
        else:
            self.out.write('This code looks all good!\n')

    def pprint_summary(self, stats):
        self.out.write('Summary\n')
        self.out.write(str(stats))

    def pprint_table(self, table):
        self.out.write('-' * (sum(table.max_col_sizes) + len(table.headings) - 1) + '\n')
        for n, col in enumerate(table.headings):
            self.out.write(str(col).ljust(table.max_col_sizes[n] + 1))
        self.out.write('\n')
        self.out.write('-' * (sum(table.max_col_sizes) + len(table.headings) - 1) + '\n')
        for row in table:
            for n, col in enumerate(row):
                self.out.write(str(col).ljust(table.max_col_sizes[n] + 1))
            self.out.write('\n')
        self.out.write('-' * (sum(table.max_col_sizes) + len(table.headings) - 1) + '\n')

