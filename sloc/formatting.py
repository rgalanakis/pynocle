#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils

class SlocTextFormatter(utils.IReportFormatter):
    """Functionality for formatting SLOC info into a readable file."""
    def __init__(self, out=sys.stdout):
        self.out = out

    def outstream(self):
        return self.out
    
    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self.out.write('SLOC (Source Lines of Code)\n')
        self.out.write('Measures physical lines of source code (SLOC), lines of comments, and blank lines, in\n'
            'number and percentage of file.  Also measures total line count (TLOC) and as percentage of\n'
            'total codebase lines.\n\n')

    def _fmtperc(self, i):
        """Format number i as a percentage."""
        perc = '%.1f%%' % (i * 100)
        return perc

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
            row = (utils.prettify_path(filename),
                   str(d['code']), self._fmtperc(d['codeperc']),
                   str(d['comment']), self._fmtperc(d['commentperc']),
                   str(d['blank']), self._fmtperc(d['blankperc']),
                   str(d['total']), self._fmtperc(d['totalperc']))
            rows.append(row)
        rows.append([''] * len(header)) #blank row
        rows.append(self._get_totals_row(slocgroup))
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self.out)
