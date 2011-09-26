#!/usr/bin/env python

import sys

import pagerank
import pynocle.tableprint as tableprint
import pynocle.utils as utils


class CouplingTextFormatter(utils.IReportFormatter):
    """Functionality for formatting coupling info into a readable file."""
    def __init__(self, out=sys.stdout):
        self._outstream = out

    def format_report_header(self):
        """Prints out a coupling explanation and header to self.out."""
        self._outstream.write('Afferent and Efferent Coupling\n')
        self._outstream.write('Measures the coupling between modules.\n'
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
        formatted = '%.3f' % instab
        return formatted

    def format_data(self, dependencygroup):
        header = 'Filename', 'Ca', 'Ce', 'I'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c
        rows = []
        sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
        for i in range(len(sortedfilenames)):
            f = sortedfilenames[i]
            ca = dependencygroup.depnode_to_ca[f]
            ce = dependencygroup.depnode_to_ce[f]
            rows.append([utils.prettify_path(f), str(ca), str(ce), self._calc_instability(ca, ce)])
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self._outstream)


class RankTextFormatter(utils.IReportFormatter):
    """Functionality for formatting SLOC info into a readable file."""
    def __init__(self, out=sys.stdout):
        self._outstream = out

    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self._outstream.write("Google's PageRank algorithm applied to Coupling\n")
        self._outstream.write('High vaules are more "important" in the same way highly ranked webpages are.\n\n')

    def _fmt_rank(self, val):
        return '%.5f' % val

    def format_data(self, dependencygroup):
        header = 'Filename', 'PageRank', 'PageID', 'Outgoing Links'
        converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)

        matrix = converter.create_matrix()
        ranking = pagerank.pageRank(matrix)
        ids = [idx for idx in range(len(matrix))]
        filenames = [utils.prettify_path(converter.id_to_node_map[nid]) for nid in ids]

        rowinfos = zip(filenames, ranking, ids, matrix)
        rowinfos.sort(key=lambda item: item[1]) #sort by ranking
        rowinfos.reverse()
        rows = []
        for rowi in rowinfos:
            row = (rowi[0], self._fmt_rank(rowi[1]), str(rowi[2]), str(rowi[3]))
            rows.append(row)
        tbl = tableprint.Table(header, rows)
        tbl.write(self._outstream)
