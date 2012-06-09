#!/usr/bin/env python

import sys

import pynocle.tableprint as tableprint
import pynocle.utils as utils

#Anything under 7 is considered fine.
DEFAULT_THRESHOLD = 6


def _above_threshold(flatstat, threshold):
    """Returns true of the CC of flatstat is
    equal to or above self.threshold."""
    return flatstat[2] >= threshold #ind 2 is cc amount


def _infostr(newline='<br />'):
    """Returns the informational string about CC."""
    return ('Cyclomatic Complexity is a measure of decisions that can be '
            'made in a procedure.{0}'
            'Values <= 10 are fine, between 11 and 20 should be refactored, '
            'and values above 20 are usually '
            'considered unacceptable and should be refactored.').format(
        newline)


def _showingstr(threshold):
    return 'Showing items with a CC greater than or equal to %s.' % threshold


def _validate_threshold(threshold):
    """Raises if threshold is not valid, returns threshold if valid,
    or returns DEFAULT_THRESHOLD if None.
    """
    if threshold is None:
        threshold = DEFAULT_THRESHOLD
    elif threshold < 1:
        raise ValueError('threshold must be greater than 0, got ' +
                         str(threshold))
    return threshold


class CCGoogleChartFormatter(utils.IReportFormatter):
    """Base class for formatting Cyclomatic Complexity reports.

    :param out: The stream to write the report out to.
    :param threshold: Items with CC values less than threshold
      will not be included in the report.
      If None, use `DEFAULT_THRESHOLD`.
    :param leading_path: Strip off this leading path from result filenames.
    """
    def __init__(self, out=sys.stdout, threshold=None, leading_path=None):
        self.threshold = _validate_threshold(threshold)
        self._outstream = out
        self.leading_path = leading_path

        self.chart = tableprint.GoogleChartTable(
            [('Filename', 'string'),
                ('Type', 'string'),
                ('Name', 'string'),
                ('CC', 'number')])

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        firstp = '<p>%s</p>\n<p>%s</p>\n<p>%s</p>' % (
            _infostr(),
            _showingstr(self.threshold),
            'Files under "%s".' % self.leading_path)
        self.outstream().write(self.chart.last_part(abovetable=firstp))

    def format_data(self, files_stats_failures):
        """Formats the output of measure_cyclcompl
        ([filename, stats], [failures])."""
        rows = []
        def abovethreshold(flatstat):
            return _above_threshold(flatstat, self.threshold)
        for filename, stats in files_stats_failures[0]:
            filename = utils.prettify_path(filename, self.leading_path)
            for type, name, cc in filter(abovethreshold, stats.flatStats):
                rows.append([filename, type, name, cc])
        self.outstream().write(self.chart.second_part(rows))
