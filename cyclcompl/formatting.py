import abc
import sys

import pynocle.tableprint as tableprint

#Anything under 7 is considered fine.
DEFAULT_THRESHOLD = 5

def format_cyclcompl(ccformatter, files_and_stats, failures=()):
    """Invokes the proper methods on ccformatter with files_and_stats, which should be the result of measure_cyclcompl
    (a collection of 2 item tuples of (filename, FlatStat instance)).
    """
    ccformatter.format_report_header()
    ccformatter.format_failures(failures)
    for filename, stat in files_and_stats:
        ccformatter.format_file_and_stats(filename, stat)
    ccformatter.format_report_footer()

    
class ICCFormatter(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def outstream(self):
        """Returns a file-like object to write to."""

    @abc.abstractmethod
    def format_report_header(self):
        """Writes the information that should be at the top of the report to self.outstream()."""

    def format_report_footer(self):
        """Writes the information that should be at the bottom of the report.  Usually a no-op."""

    @abc.abstractmethod
    def format_failures(self, failures):
        """Handles the writing of any modules that failed to parse into self.outstream().

        failures: A collection of filenames that failed to parse.
        """

    @abc.abstractmethod
    def format_file_and_stats(self, filename, stats):
        """Handles the writing of the stats for a file.

        filename: The filename of the file being reported.
        stats: The instance of Stats responsible representing this file.
        """

    @abc.abstractmethod
    def format_stats(self, stats):
        """Writes the actual Stats information.  Subclasses should handle the filtering of threshold if they choose to.
        Returns the number of 'rows' written.
        """


class CCTextFormatter(ICCFormatter):
    def __init__(self, threshold=None, out=sys.stdout):
        if threshold is None:
            threshold = DEFAULT_THRESHOLD
        elif threshold < 1:
            raise ValueError, 'threshold must be greater than 0, got ' + str(threshold)
        self.threshold = threshold
        self.out = out

    def outstream(self):
        return self.out
    
    def format_report_header(self):
        self.out.write('Cyclomatic Complexity is a measure of decisions that can be made in a procedure.\n')
        self.out.write('See http://en.wikipedia.org/wiki/Cyclomatic_complexity\n')
        self.out.write('Showing items with a CC greater than or equal to %s\n\n' % self.threshold)
        
    def format_failures(self, failures):
        if not failures:
            return
        self.out.write('WARNING: The following files failed to parse:\n')
        for f in failures:
            self.out.write('\t%s\n' % f)
        self.out.write('\n')

    def format_file_and_stats(self, filename, stats):
        self.out.write(filename)
        self.out.write('\n')
        self.format_stats(stats)

    def format_stats(self, stats):
        #Filter and convert the stat rows
        rows = []
        for type, name, cc in stats.flatStats:
            if cc >= self.threshold:
                rows.append([type, name, str(cc)])
        if rows:
            tbl = tableprint.Table(['Type', 'Name', 'CC'], rows)
            tbl.write(self.out)
        else:
            self.out.write('No items with a CC >= %s\n\n' % self.threshold)
        return len(rows)
