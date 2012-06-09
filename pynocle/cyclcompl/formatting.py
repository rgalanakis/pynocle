#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils

#Anything under 7 is considered fine.
DEFAULT_THRESHOLD = 6

class _CCFormatter(utils.IReportFormatter):
    """Base class for formatting Cyclomatic Complexity reports.

    out: The stream to write the report out to.
    threshold: Items with CC values less than threshold will not be included in the report.
    leading_path: Strip off this leading path from result filenames.
    """
    def __init__(self, out=sys.stdout, threshold=None, leading_path=None):
        if threshold is None:
            threshold = DEFAULT_THRESHOLD
        elif threshold < 1:
            raise ValueError, 'threshold must be greater than 0, got ' + str(threshold)
        self.threshold = threshold
        self._outstream = out
        self.leading_path = leading_path

    def above_threshold(self, flatstat):
        """Returns true of the CC of flatstat is equal to or above self.threshold."""
        return flatstat[2] >= self.threshold #ind 2 is cc amount

    def prettify(self, s):
        """Calls utils.prettify on s with self.leadingpath."""
        return utils.prettify_path(s, self.leading_path)

    def infostr(self, linebreak='', newline='<br />'):
        """Returns the informational string about CC."""
        return ('Cyclomatic Complexity is a measure of decisions that can be made in a procedure.{1}'
            'Values <= 10 are fine, between 11 and 20 should be refactored, and values above 20 are usually{0}'
            'considered unacceptable and should be refactored.').format(linebreak, newline)

    def showingstr(self):
        return 'Showing items with a CC greater than or equal to %s.' % self.threshold

class CCTextFormatter(_CCFormatter):
    def format_report_header(self):
        self.outstream().write(self.infostr('\n', '\n'))
        self.outstream().write('\n\n')
        self.outstream().write('%s\n\n' % self.showingstr())

    def format_failures(self, failures):
        if not failures:
            return
        self._outstream.write('WARNING: The following files failed to parse:\n')
        for f in failures:
            self._outstream.write('\t%s\n' % f)
        self._outstream.write('\n')

    def format_data(self, files_stats_failures):
        """Formats the output of measure_cyclcompl ([filename, stats], [failures])."""
        self.format_failures(map(self.prettify, files_stats_failures[1]))
        allrows = []
        for filename, stat in files_stats_failures[0]:
            filename = self.prettify(filename)
            rows = self.format_file_and_stats(filename, stat)
            for r in rows:
                r.insert(0, filename)
            allrows.extend(rows)
        sortby_cc_desc = lambda row: -(int(row[3]))
        tbl = tableprint.Table(['Filename', 'Type', 'Name', 'CC'], sorted(allrows, key=sortby_cc_desc))
        self.outstream().write('All results, sorted by CC:\n')
        tbl.write(self.outstream())

    def _get_table_for_stats(self, stats):
        rows = []
        for type, name, cc in filter(self.above_threshold, stats.flatStats):
            rows.append([type, name, str(cc)])
        tbl = tableprint.Table(['Type', 'Name', 'CC'], rows)
        return tbl

    def format_file_and_stats(self, filename, stats):
        tbl = self._get_table_for_stats(stats)
        if tbl.rows:
            self._outstream.write(filename)
            self._outstream.write('\n')
            tbl.write(self.outstream())
        return tbl.rows


class CCGoogleChartFormatter(_CCFormatter):
    def __init__(self, *args, **kwargs):
        super(CCGoogleChartFormatter, self).__init__(*args, **kwargs)
        self.chart = tableprint.GoogleChartTable(
            [('Filename', 'string'), ('Type', 'string'), ('Name', 'string'), ('CC', 'number')])

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        firstp = '<p>%s</p>\n<p>%s</p>' % (self.infostr(), self.showingstr())
        self.outstream().write(self.chart.last_part(abovetable=firstp))

    def format_data(self, files_stats_failures):
        """Formats the output of measure_cyclcompl ([filename, stats], [failures])."""
        rows = []
        for filename, stats in files_stats_failures[0]:
            filename = utils.prettify_path(filename, self.leading_path)
            for type, name, cc in filter(self.above_threshold, stats.flatStats):
                rows.append([filename, type, name, cc])
        self.outstream().write(self.chart.second_part(rows))

formatter_registry = utils.ExtensionFormatterRegistry({'.txt': CCTextFormatter, '.html': CCGoogleChartFormatter})
