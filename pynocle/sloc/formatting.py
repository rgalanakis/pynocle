#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils


class _SlocFormatter(utils.IReportFormatter):
    """Base class for formatters for SLOC info.

    out: The stream to write the report to.
    leading_path: The path to strip off from filenames in the report.
    """
    def __init__(self, out=sys.stdout, leading_path=None):
        self.out = out
        self.leading_path = leading_path

    def outstream(self):
        return self.out

    def _fmtperc(self, i):
        """Format number i as a percentage, to one decimal place."""
        perc = '%.1f%%' % (i * 100)
        return perc

    def infostr(self, linebreak='', newline='<br />'):
        return ('Measures physical source lines of code (SLOC), lines of comments, and blank lines, in{0}'
            'number and percentage of file.{1}'
            'Also measures total line count and as percentage of total codebase lines.').format(linebreak, newline)

    def _get_totals_row(self, slocgroup):
        """Returns the row for TOTALS."""
        totallines = slocgroup.totallines
        def average(key):
            total = totallines(key)
            return total / len(slocgroup.filenamesToSlocInfos)
        return ['TOTALS',
                 totallines('code'), average('codeperc'),
                 totallines('comment'), average('commentperc'),
                 totallines('blank'), average('blankperc'),
                 totallines('total'), totallines('totalperc')]

    def create_rows(self, slocgroup):
        """Returns a list of rows.  The caller may need to call _stringify on them for display."""
        rows = []
        sortedbyfilename = sorted(slocgroup.filenamesToSlocInfos.items(), key=lambda kvp: kvp[0])
        for filename, d in sortedbyfilename:
            row = [utils.prettify_path(filename, self.leading_path),
                   d['code'], d['codeperc'],
                   d['comment'], d['commentperc'],
                   d['blank'], d['blankperc'],
                   d['total'], d['totalperc']]
            rows.append(row)
        rows.append(self._get_totals_row(slocgroup))
        return rows


class SlocGoogleChartFormatter(_SlocFormatter):
    def __init__(self, *args, **kwargs):
        super(SlocGoogleChartFormatter, self).__init__(*args, **kwargs)
        cols = [('Filename', 'string'),
                ('Code', 'number'),
                ('Code%', 'number'),
                ('Comment', 'number'),
                ('Comment%', 'number'),
                ('Blank', 'number'),
                ('Blank%', 'number'),
                ('Total', 'number'),
                ('Total%', 'number')]
        self.chart = tableprint.GoogleChartTable(cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        abovepart = '<p>%s</p>' % self.infostr()
        self.outstream().write(self.chart.last_part(abovetable=abovepart))

    def _js_perc(self, value):
        """Return a dict for JS for formatting value as a percent."""
        s = self._fmtperc(value)
        return {'v': value, 'f': s}
        #{v: new Date(1999,0,1), f: 'January First, Nineteen ninety-nine'}

    def _stringify(self, row):
        """Returns a row/list as a list of properly formatted strings."""
        return [row[0],
               row[1], self._js_perc(row[2]),
               row[3], self._js_perc(row[4]),
               row[5], self._js_perc(row[6]),
               row[7], self._js_perc(row[8])]

    def format_data(self, slocgroup):
        rows = map(self._stringify, self.create_rows(slocgroup))
        self.outstream().write(self.chart.second_part(rows))
