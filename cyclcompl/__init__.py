import abc

#Anything under 7 is considered fine.
DEFAULT_THRESHOLD = 5

class CCFormatter(object):
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

def measure_cyclcompl(files):
    """Returns 2 items: A collection of (filename, FlatStat instance for file) tuples, and a collection of files that
    failed to parse.
    """
    result = []
    failures = []
    for f in files:
        try:
            stats = statbuilder.measure_file_complexity(f)
            result.append((f, stats))
        except SyntaxError:
            failures.append(f)
    return result, failures

def format_cyclcompl(ccformatter, files_and_stats, failures=()):
    """Invokes the proper methods on ccformatter with files_and_stats, which should be the result of measure_cyclcompl
    (a collection of 2 item tuples of (filename, FlatStat instance)).
    """
    ccformatter.format_report_header()
    ccformatter.format_failures(failures)
    for filename, stat in files_and_stats:
        ccformatter.format_file_and_stats(filename, stat)
    ccformatter.format_report_footer()

import statbuilder
import formatting