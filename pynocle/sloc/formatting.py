#!/usr/bin/env python

import sys

import _doc
import pynocle.tableprint as tableprint
import pynocle.utils as utils


def _fmtperc(i):
    """Format number i as a percentage, to one decimal place."""
    perc = '%.1f%%' % (i * 100)
    return perc


def _get_infostr(leadingpath):
    s = _doc.about() + '\nShowing SLOC for files under %s.' % (
        leadingpath.replace('\\', '/'))
    return s


def _get_totals_row(slocgroup):
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


def _create_rows(slocgroup, leading_path):
    """Returns a list of rows."""
    rows = []
    sortedbyfilename = sorted(
        slocgroup.filenamesToSlocInfos.items(),
        key=lambda kvp: kvp[0])
    for filename, d in sortedbyfilename:
        row = [utils.prettify_path(filename, leading_path),
               d['code'], d['codeperc'],
               d['comment'], d['commentperc'],
               d['blank'], d['blankperc'],
               d['total'], d['totalperc']]
        rows.append(row)
    rows.append(_get_totals_row(slocgroup))
    return rows


class SlocGoogleChartFormatter(utils.IReportFormatter):
    """Google chart formatter for sloc info.

    :param out: The stream to write the report to.
    :param leading_path: The path to strip off from filenames in the report.
    """
    def __init__(self, out=sys.stdout, leading_path=None):
        self._outstream = out
        self.leading_path = leading_path
        cols = [('Filename', 'string'),
                ('Code', 'number'),
                ('Code%', 'number'),
                ('Comment', 'number'),
                ('Comment%', 'number'),
                ('Blank', 'number'),
                ('Blank%', 'number'),
                ('Total', 'number'),
                ('Total%', 'number')]
        self.chart = tableprint.GoogleChartTable('SLOC', cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        s = utils.rst_to_html(_get_infostr(self.leading_path))
        self.outstream().write(self.chart.last_part(abovetable=s))

    def _js_perc(self, value):
        """Return a dict for JS for formatting value as a percent."""
        s = _fmtperc(value)
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
        rows = map(self._stringify, _create_rows(slocgroup, self.leading_path))
        self.outstream().write(self.chart.second_part(rows))
