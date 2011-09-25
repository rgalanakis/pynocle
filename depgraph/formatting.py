import abc
import sys

import pagerank
import tableprint

def format_coupling(dependencygroup, couplingformatter):
    couplingformatter.format_report_header()
    couplingformatter.format_dependencygroup(dependencygroup)
    couplingformatter.format_report_footer()
    
class ICouplingFormatter(object):
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
    def format_dependencygroup(self, dependencygroup):
        """Writes all the data in dependencygroup to self.outstream()."""


class CouplingTextFormatter(ICouplingFormatter):
    """Functionality for formatting coupling info into a readable file."""
    def __init__(self, out=sys.stdout):
        self.out = out

    def outstream(self):
        return self.out
    
    def format_report_header(self):
        """Prints out a coupling explanation and header to self.out."""
        self.out.write('Afferent and Efferent Coupling\n')
        self.out.write('Measures the coupling between modules.\n'
            'Afferent coupling (Ca) is the number of modules that use a given module.  0 can indicate dead code.\n'
            'Efferent coupling (Ce)is the number of modules a given module imports.  A high value can indicate a\n'
            'brittle module.\n'
            'Instability (I) is the ratio of Ce to total coupling. I = Ce / (Ce + Ca). Indicates the\n'
            "module's resilience to change between 0 (completely stable) and 1 (unstable).\n\n")

    def _calc_instability(self, ca, ce):
        """Calculate the instability ratio between ca and ce and returns it as a string."""
        if ca or ce:
            caf, cef = float(ca), float(ce)
            instab = cef / (cef + caf)
        else:
            instab = 0
        formatted = '%.1f' % instab
        return formatted

    def format_dependencygroup(self, dependencygroup):
        header = 'Filename', 'Ca', 'Ce', 'I'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c
        rows = []
        sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
        for i in range(len(sortedfilenames)):
            f = sortedfilenames[i]
            ca = dependencygroup.depnode_to_ca[f]
            ce = dependencygroup.depnode_to_ce[f]
            rows.append([f, str(ca), str(ce), self._calc_instability(ca, ce)])
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self.out)


class RankTextFormatter(ICouplingFormatter):
    """Functionality for formatting SLOC info into a readable file."""
    def __init__(self, out=sys.stdout):
        self.out = out

    def outstream(self):
        return self.out

    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self.out.write("Google's PageRank algorithm applied to Coupling\n")
        self.out.write('High vaules are more "important" in the same way highly ranked webpages are.\n\n')

    def _fmt_rank(self, val):
        return '%.5f' % val

    def format_dependencygroup(self, dependencygroup):
        header = 'Filename', 'PageRank', 'PageID', 'Outgoing Links'
        converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)

        matrix = converter.create_matrix()
        ranking = pagerank.pageRank(matrix)
        ids = [idx for idx in range(len(matrix))]
        filenames = [converter.id_to_node_map[nid] for nid in ids]

        rowinfos = zip(filenames, ranking, ids, matrix)
        rowinfos.sort(key=lambda item: item[1]) #sort by ranking
        rowinfos.reverse()
        rows = []
        for rowi in rowinfos:
            row = (rowi[0], self._fmt_rank(rowi[1]), str(rowi[2]), str(rowi[3]))
            rows.append(row)
        tbl = tableprint.Table(header, rows)
        tbl.write(self.out)
