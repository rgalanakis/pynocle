#!/usr/bin/env python

import sys

import _doc
import pagerank
import pynocle.tableprint as tableprint
import pynocle.utils as utils


def _calc_instability(ca, ce):
    """Returns the instability ratio between ca and ce."""
    if ca or ce:
        caf, cef = float(ca), float(ce)
        instab = cef / (cef + caf)
    else:
        instab = 0
    return instab


def _coupling_infostr(leadingpath):
    s = _doc.about_coupling()
    s += '\nShowing the coupling between files under %s.' % (
        leadingpath.replace('\\', '/'))
    return s


def get_rows(dependencygroup, leadingpath):
    """Return the rows for dependencygroup.
    Caller may have to format the values as strings."""
    rows = []
    sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
    for i in range(len(sortedfilenames)):
        f = sortedfilenames[i]
        ca = dependencygroup.depnode_to_ca[f]
        ce = dependencygroup.depnode_to_ce[f]
        rows.append([utils.prettify_path(f, leadingpath),
                     ca, ce, _calc_instability(ca, ce)])
    return rows


class CouplingGoogleChartFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, leading_path=None):
        self._outstream = out
        self.leading_path = leading_path
        cols = [('Filename', 'string'),
            ('Afferent Coupling (Ca)', 'number'),
            ('Efferent Coupling (Ce)', 'number'),
            ('Instability (I)', 'number')]
        self.chart = tableprint.GoogleChartTable('Coupling', cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        info = utils.rst_to_html(_coupling_infostr(self.leading_path))
        self.outstream().write(self.chart.last_part(info))

    def _js_instab(self, val):
        return {'v': val, 'f':'%.3f' % val}

    def format_data(self, dependencygroup):
        def stringify(row):
            return row[:3] + [self._js_instab(row[3])]
        rows = map(stringify, get_rows(dependencygroup, self.leading_path))
        self.outstream().write(self.chart.second_part(rows))


def _fmt_rank(val):
    """Returns value (between 0 and 1) formatted as a percentage."""
    return '%.5f' % (100 * val)


def _rank_infostr(leadingpath):
    s = _doc.about_rank()
    s += '\nShowing PageRank coupling for %s.' % leadingpath.replace('\\', '/')
    return s


def create_rows(dependencygroup, leadingpath):
    """Returns a list of rows for a dependencygroup."""
    converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)
    matrix = converter.create_matrix()
    ranking = pagerank.page_rank(matrix)
    ids = [idx for idx in range(len(matrix))]
    filenames = [utils.prettify_path(converter.id_to_node_map[nid], leadingpath)
                 for nid in ids]

    rowinfos = zip(filenames, ranking, ids, matrix)
    rowinfos.sort(key=lambda item: item[1]) #sort by ranking
    rowinfos.reverse()
    return rowinfos


class RankGoogleChartFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, leading_path=None):
        self._outstream = out
        self.leading_path = leading_path
        cols = [('Filename', 'string'),
            ('PageRank', 'number'),
            ('PageID', 'number'),
            ('Outgoing Links', 'string')]
        self.chart = tableprint.GoogleChartTable('Coupling PageRank', cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        s = utils.rst_to_html(_rank_infostr(self.leading_path))
        self.outstream().write(self.chart.last_part(s))

    def _js_perc(self, val):
        """Returns a JS dict for formatting val."""
        return {'v': val, 'f': _fmt_rank(val)}

    def format_data(self, dependencygroup):
        def stringify(row):
            return [row[0], self._js_perc(row[1]), row[2], str(row[3])]
        rows = map(stringify, create_rows(dependencygroup, self.leading_path))
        self.outstream().write(self.chart.second_part(rows))
