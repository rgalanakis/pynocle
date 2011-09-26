#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils

#Anything under 7 is considered fine.
DEFAULT_THRESHOLD = 5


class CCTextFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, threshold=None, writeempty=False):
        if threshold is None:
            threshold = DEFAULT_THRESHOLD
        elif threshold < 1:
            raise ValueError, 'threshold must be greater than 0, got ' + str(threshold)
        self.writeempty = writeempty
        self.threshold = threshold
        self._outstream = out

    def format_report_header(self):
        self._outstream.write('Cyclomatic Complexity is a measure of decisions that can be made in a procedure.\n'
            'Values <= 10 are fine, between 11 and 20 should be refactored, and values above 20 are usually\n'
            'considered unacceptable and should be refactored.\n\n')
        self._outstream.write('Showing items with a CC greater than or equal to %s\n\n' % self.threshold)

    def format_failures(self, failures):
        if not failures:
            return
        self._outstream.write('WARNING: The following files failed to parse:\n')
        for f in failures:
            self._outstream.write('\t%s\n' % f)
        self._outstream.write('\n')

    def format_data(self, files_stats_failures):
        """Formats the output of measure_cyclcompl ([filename, stats], [failures])."""
        self.format_failures(map(utils.prettify_path, files_stats_failures[1]))
        allrows = []
        for filename, stat in files_stats_failures[0]:
            filename = utils.prettify_path(filename)
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
        for type, name, cc in stats.flatStats:
            if cc >= self.threshold:
                rows.append([type, name, str(cc)])
        tbl = tableprint.Table(['Type', 'Name', 'CC'], rows)
        return tbl

    def format_file_and_stats(self, filename, stats):
        tbl = self._get_table_for_stats(stats)
        if tbl.rows:
            self._outstream.write(filename)
            self._outstream.write('\n')
            tbl.write(self.outstream())
        elif self.writeempty:
            self._outstream.write('No items with a CC >= %s\n\n' % self.threshold)
        return tbl.rows

