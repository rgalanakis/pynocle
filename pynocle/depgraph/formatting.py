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

    def infostr(self, linebreak='', newline='<br />'):
        return ('Measures the coupling between modules.{1}'
            'Afferent coupling (Ca) is the number of modules that use a given module.  0 can indicate dead code.{1}'
            'Efferent coupling (Ce)is the number of modules a given module imports.  A high value can indicate a{0}'
            'brittle module.{1}'
            'Instability (I) is the ratio of Ce to total coupling. I = Ce / (Ce + Ca). Indicates the{0}'
            "module's resilience to change between 0 (completely stable) and 1 (unstable)."
            ).format(linebreak, newline)

    def get_rows(self, dependencygroup):
        """Return the rows for dependencygroup.  Caller may have to format the values as strings."""
        rows = []
        sortedfilenames = sorted(dependencygroup.depnode_to_ca.keys())
        for i in range(len(sortedfilenames)):
            f = sortedfilenames[i]
            ca = dependencygroup.depnode_to_ca[f]
            ce = dependencygroup.depnode_to_ce[f]
            rows.append([utils.prettify_path(f, self.leading_path), ca, ce, self._calc_instability(ca, ce)])
        return rows


class CouplingGoogleChartFormatter(_CouplingFormatter):
    def __init__(self, *args, **kwargs):
        super(CouplingGoogleChartFormatter, self).__init__(*args, **kwargs)
        cols = [('Filename', 'string'), ('Afferent Coupling (Ca)', 'number'), ('Efferent Coupling (Ce)', 'number'),
            ('Instability (I)', 'number')]
        self.chart = tableprint.GoogleChartTable(cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        info = '<p>%s</p>' % self.infostr()
        self.outstream().write(self.chart.last_part(info))

    def _js_instab(self, val):
        return {'v': val, 'f':'%.3f' % val}

    def format_data(self, dependencygroup):
        def stringify(row):
            return row[:3] + [self._js_instab(row[3])]
        rows = map(stringify, self.get_rows(dependencygroup))
        self.outstream().write(self.chart.second_part(rows))


class _RankFormatter(utils.IReportFormatter):
    def __init__(self, out=sys.stdout, leading_path=None):
        self._outstream = out
        self.leading_path = leading_path

    def _fmt_rank(self, val):
        """Returns value (between 0 and 1) formatted as a percentage."""
        return '%.5f' % (100 * val)

    def infostr(self, linebreak='', newline='<br />'):
        return ("Google's PageRank algorithm applied to Coupling{1}"
                'High vaules are more "important" in the same way highly ranked webpages are.'
            ).format(linebreak, newline)

    def create_rows(self, dependencygroup):
        """Returns a list of rows for a dependencygroup."""
        converter = pagerank.DependenciesToLinkMatrix(dependencygroup.dependencies)
        matrix = converter.create_matrix()
        ranking = pagerank.pageRank(matrix)
        ids = [idx for idx in range(len(matrix))]
        filenames = [utils.prettify_path(converter.id_to_node_map[nid], self.leading_path) for nid in ids]

        rowinfos = zip(filenames, ranking, ids, matrix)
        rowinfos.sort(key=lambda item: item[1]) #sort by ranking
        rowinfos.reverse()
        return rowinfos


class RankGoogleChartFormatter(_RankFormatter):
    def __init__(self, *args, **kwargs):
        super(RankGoogleChartFormatter, self).__init__(*args, **kwargs)
        cols = ('Filename', 'string'), ('PageRank', 'number'), ('PageID', 'number'), ('Outgoing Links', 'string')
        self.chart = tableprint.GoogleChartTable(cols)

    def format_report_header(self):
        self.outstream().write(self.chart.first_part())

    def format_report_footer(self):
        abovep = '<p>%s</p>' % self.infostr()
        self.outstream().write(self.chart.last_part(abovep))

    def _js_perc(self, val):
        """Returns a JS dict for formatting val."""
        return {'v':val, 'f':self._fmt_rank(val)}

    def format_data(self, dependencygroup):
        def stringify(row):
            return [row[0], self._js_perc(row[1]), row[2], str(row[3])]
        rows = map(stringify, self.create_rows(dependencygroup))
        self.outstream().write(self.chart.second_part(rows))
