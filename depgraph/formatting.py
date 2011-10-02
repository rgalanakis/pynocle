#!/usr/bin/env python

import sys

import pagerank
import pynocle.tableprint as tableprint
import pynocle.utils as utils


class _CouplingFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, leading_path=None):
        self._outstream = out
        self.leading_path = leading_path

    def _calc_instability(self, ca, ce):
        """Returns the instability ratio between ca and ce."""
        if ca or ce:
            caf, cef = float(ca), float(ce)
            instab = cef / (cef + caf)
        else:
            instab = 0
        return instab
    
class CouplingTextFormatter(_CouplingFormatter):
    """Functionality for formatting coupling info into a readable file."""

    def format_report_header(self):
        """Prints out a coupling explanation and header to self.out."""
        self._outstream.write('Afferent and Efferent Coupling\n')
        self._outstream.write('Measures the coupling between modules.\n'
            'Afferent coupling (Ca) is the number of modules that use a given module.  0 can indicate dead code.\n'
            'Efferent coupling (Ce)is the number of modules a given module imports.  A high value can indicate a\n'
            'brittle module.\n'
            'Instability (I) is the ratio of Ce to total coupling. I = Ce / (Ce + Ca). Indicates the\n'
            "module's resilience to change between 0 (completely stable) and 1 (unstable).\n\n")

    def format_data(self, dependencygroup):
        def instab(ca_, ce_):
            return '%.3f' % self._calc_instability(ca_, ce_)

        header = 'Filename', 'Ca', 'Ce', 'I'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c
        rows = []
        sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
        for i in range(len(sortedfilenames)):
            f = sortedfilenames[i]
            ca = dependencygroup.depnode_to_ca[f]
            ce = dependencygroup.depnode_to_ce[f]
            rows.append([utils.prettify_path(f, self.leading_path), str(ca), str(ce), instab(ca, ce)])
        tbl = tableprint.Table(header, rows, just=justs)
        tbl.write(self._outstream)


class CouplingGoogleChartFormatter(_CouplingFormatter):
    def format_report_header(self):
        cols = ('Filename', 'string'), ('Ca', 'number'), ('Ce', 'number'), ('I', 'number')
        self.outstream().write(tableprint.googlechart_table_html_header(colnames_and_types=cols))

    def format_report_footer(self):
        self.outstream().write(tableprint.googlechart_table_html_footer())

    def _js_instab(self, ca, ce):
        val = self._calc_instability(ca, ce)
        return {'v': val, 'f':'%.3f' % val}

    def format_data(self, dependencygroup):
        sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
        for i in range(len(sortedfilenames)):
            f = sortedfilenames[i]
            ca = dependencygroup.depnode_to_ca[f]
            ce = dependencygroup.depnode_to_ce[f]
            row = [utils.prettify_path(f, self.leading_path), ca, ce, self._js_instab(ca, ce)]
            self.outstream().write('        data.addRow(%s);\n' % row)


class RankTextFormatter(_CouplingFormatter):

    def format_report_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self._outstream.write("Google's PageRank algorithm applied to Coupling\n")
        self._outstream.write('High vaules are more "important" in the same way highly ranked webpages are.\n\n')

    def _fmt_rank(self, val):
        return '%.5f' % (100 * val)

    def format_data(self, dependencygroup):
        header = 'Filename', 'PageRank', 'PageID', 'Outgoing Links'
        converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)

        matrix = converter.create_matrix()
        ranking = pagerank.pageRank(matrix)
        ids = [idx for idx in range(len(matrix))]
        filenames = [utils.prettify_path(converter.id_to_node_map[nid], self.leading_path) for nid in ids]

        rowinfos = zip(filenames, ranking, ids, matrix)
        rowinfos.sort(key=lambda item: item[1]) #sort by ranking
        rowinfos.reverse()
        rows = []
        for rowi in rowinfos:
            row = (rowi[0], self._fmt_rank(rowi[1]), str(rowi[2]), str(rowi[3]))
            rows.append(row)
        tbl = tableprint.Table(header, rows)
        tbl.write(self._outstream)


class RankGoogleChartFormatter(_CouplingFormatter):

    def format_report_header(self):
        cols = ('Filename', 'string'), ('PageRank', 'number'), ('PageID', 'number'), ('Outgoing Links', 'string')
        self._outstream.write(tableprint.googlechart_table_html_header(colnames_and_types=cols))

    def format_report_footer(self):
        self.outstream().write(tableprint.googlechart_table_html_footer())

    def _fmt_rank(self, val):
        return '%.5f' % (100 * val)

    def _js_perc(self, val):
        """Returns a JS dict for formatting val."""
        return {'v':val, 'f':self._fmt_rank(val)}

    def format_data(self, dependencygroup):
        converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)
        matrix = converter.create_matrix()
        ranking = pagerank.pageRank(matrix)
        ids = [idx for idx in range(len(matrix))]
        filenames = [utils.prettify_path(converter.id_to_node_map[nid], self.leading_path) for nid in ids]

        rowinfos = zip(filenames, ranking, ids, matrix)
        rowinfos.sort(key=lambda item: item[1]) #sort by ranking
        rowinfos.reverse()
        for rowi in rowinfos:
            row = [rowi[0], self._js_perc(rowi[1]), rowi[2], str(rowi[3])]
            self.outstream().write('        data.addRow(%s);\n' % row)
            

coupling_formatter_registry = utils.ExtensionFormatterRegistry({'.txt': CouplingTextFormatter,
                                                                '.html': CouplingGoogleChartFormatter})

couplingrank_formatter_registry = utils.ExtensionFormatterRegistry({'.txt': RankTextFormatter,
                                                                '.html': RankGoogleChartFormatter})