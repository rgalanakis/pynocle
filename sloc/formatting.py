import abc
import sys

import pynocle.tableprint as tableprint

def format_slocgroup(slocgroup, slocformatter):
    slocformatter.format_report_header()
    slocformatter.format_slocgroup(slocgroup)
    slocformatter.format_report_footer()

    
class ISlocFormatter(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def outstream(self):
        """Returna  file-like object that will be written to."""

    @abc.abstractmethod
    def format_report_header(self):
        """Writes the data that should be at the beginning of the report file to self.outstream()."""

    def format_report_footer(self):
        """Writes the information that should be at the bottom of the report.  Usually a no-op."""

    @abc.abstractmethod
    def format_slocgroup(self, slocgroup):
        """Writes all the data in slocgroup to self.outstream()."""


class SlocTextFormatter(ISlocFormatter):
    """Functionality for formatting SLOC info into a readable file."""
    def __init__(self, out=sys.stdout):
        self.out = out

    def outstream(self):
        return self.out
    
    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self.out.write('SLOC (Source Lines of Code)\n')
        self.out.write('Measures physical lines of code, lines of comments, and blank lines, in number and\n')
        self.out.write('percentage of file.  Also measures total line count as percentage of total codebase lines\n\n')

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

    def format_slocgroup(self, slocgroup):
        header = 'Filename', 'Code', 'Code%', 'Comment', 'Comment%', 'Blank', 'Blank%', 'Total', 'Total%'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c, c, c, c, c, c
        rows = []
        sortedbyfilename = sorted(slocgroup.filenamesToSlocInfos.items(), key=lambda kvp: kvp[0])
        for filename, d in sortedbyfilename:
            row = (filename,
                   str(d['code']), self._fmtperc(d['codeperc']),
                   str(d['comment']), self._fmtperc(d['commentperc']),
                   str(d['blank']), self._fmtperc(d['blankperc']),
                   str(d['total']), self._fmtperc(d['totalperc']))
            rows.append(row)
        rows.append([''] * len(header)) #blank row
        rows.append(self._get_totals_row(slocgroup))
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self.out)
