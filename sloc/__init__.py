import abc

import slocing

def create_slocgroup(filenames):
    return slocing.SlocGroup(filenames)

class SlocFormatter(object):
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

import formatting

def format_slocgroup(slocgroup, slocformatter):
    slocformatter.format_report_header()
    slocformatter.format_slocgroup(slocgroup)
    slocformatter.format_report_footer()