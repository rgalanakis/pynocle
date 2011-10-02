#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils

class _SlocFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, leading_path=None):
        self.out = out
        self.leading_path = leading_path

    def outstream(self):
        return self.out

    def _fmtperc(self, i):
        """Format number i as a percentage."""
        perc = '%.1f%%' % (i * 100)
        return perc

class SlocTextFormatter(_SlocFormatter):
    """Functionality for formatting SLOC info into a readable file."""
    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self.out.write('SLOC (Source Lines of Code)\n')
        self.out.write('Measures physical lines of source code (SLOC), lines of comments, and blank lines, in\n'
            'number and percentage of file.  Also measures total line count (TLOC) and as percentage of\n'
            'total codebase lines.\n\n')

    def _get_totals_row(self, slocgroup):
        tl = slocgroup.totallines
        def average(key):
            total = tl(key)
            return self._fmtperc(total / len(slocgroup.filenamesToSlocInfos))
        return map(str, ['TOTALS',
                         tl('code'), average('codeperc'),
                         tl('comment'), average('commentperc'),
                         tl('blank'), average('blankperc'),
                         tl('total'), self._fmtperc(tl('totalperc'))])

    def format_data(self, slocgroup):
        header = 'Filename', 'Code', 'Code%', 'Comment', 'Comment%', 'Blank', 'Blank%', 'Total', 'Total%'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c, c, c, c, c, c
        rows = []
        sortedbyfilename = sorted(slocgroup.filenamesToSlocInfos.items(), key=lambda kvp: kvp[0])
        for filename, d in sortedbyfilename:
            row = (utils.prettify_path(filename, self.leading_path),
                   str(d['code']), self._fmtperc(d['codeperc']),
                   str(d['comment']), self._fmtperc(d['commentperc']),
                   str(d['blank']), self._fmtperc(d['blankperc']),
                   str(d['total']), self._fmtperc(d['totalperc']))
            rows.append(row)
        rows.append([''] * len(header)) #blank row
        rows.append(self._get_totals_row(slocgroup))
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self.out)


class SlocGoogleChartFormatter(_SlocFormatter):

    def format_report_header(self):
        cols = [('Filename', 'string'),
                ('Code', 'number'),
                ('Code%', 'number'),
                ('Comment', 'number'),
                ('Comment%', 'number'),
                ('Blank', 'number'),
                ('Blank%', 'number'),
                ('Total', 'number'),
                ('Total%', 'number')]
        self.outstream().write(tableprint.googlechart_table_html_header(colnames_and_types=cols))

    def format_report_footer(self):
        self.outstream().write(tableprint.googlechart_table_html_footer())

    def _js_perc(self, value):
        """Return a dict for JS for formatting value as a percent."""
        s = self._fmtperc(value)
        return {'v': value, 'f': s}

        #{v: new Date(1999,0,1), f: 'January First, Nineteen ninety-nine'}
    def _get_totals_row(self, slocgroup):
        tl = slocgroup.totallines
        def average(key):
            total = tl(key)
            return self._js_perc(total / len(slocgroup.filenamesToSlocInfos))
        return ['TOTALS',
                 tl('code'), average('codeperc'),
                 tl('comment'), average('commentperc'),
                 tl('blank'), average('blankperc'),
                 tl('total'), self._js_perc(tl('totalperc'))]

    def format_data(self, slocgroup):
        rows = []
        sortedbyfilename = sorted(slocgroup.filenamesToSlocInfos.items(), key=lambda kvp: kvp[0])
        for filename, d in sortedbyfilename:
            row = [utils.prettify_path(filename, self.leading_path),
                   d['code'], self._js_perc(d['codeperc']),
                   d['comment'], self._js_perc(d['commentperc']),
                   d['blank'], self._js_perc(d['blankperc']),
                   d['total'], self._js_perc(d['totalperc'])]
            rows.append(row)
        rows.append(self._get_totals_row(slocgroup))
        for row in rows:
            self.outstream().write('        data.addRow(%s);\n' % row)


formatter_registry = utils.ExtensionFormatterRegistry({'.txt': SlocTextFormatter, '.html': SlocGoogleChartFormatter})