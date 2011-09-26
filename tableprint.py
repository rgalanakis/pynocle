#!/usr/bin/env python
"""
Module that handles the formatting of table information.
"""

import StringIO
import sys

JUST_L = str.ljust
JUST_R = str.rjust
JUST_C = str.center

class Table(object):
    """Represents a table (column header and rows).  Call write to format to a stream or repr to get the table as a
    string.
    """
    def __init__(self, header, rows, sep='-', padding=4, just=JUST_L):
        """Initialize.

        header: Collection of strings that represent the column headers.
        rows: Collection of rows (each row is a collection of strings that MUST have the same length as headers).
        sep: Character that seperates the table/header.
        padding: Spacing between columns.
        just: JUST_* const that controls the alignment of each column.  Can pass a collection of JUST_ consts,
            one for each row, that controls the justification of each row.
        """
        self.header = header
        self.rows = rows
        self.sep = sep
        self.paddingstr = (padding * ' ')
        self.colwidths = map(self._max_col_width, range(len(self.header)))
        if callable(just):
            #Store a collection of the method repeated for each column
            self.just = map(lambda i: just, range(len(self.header)))
        else:
            self.just = just

    def _max_col_width(self, ind):
        """Return an integer of the max column width, where ind is the column index in header and rows."""
        colvals = map(lambda row: row[ind], self.rows)
        colvallens = map(lambda s: len(s), colvals)
        colvallens.append(len(self.header[ind]))
        return max(colvallens)

    def _create_row_string(self, row):
        strs = []
        for i in range(len(row)):
            just = self.just[i]
            s = just(row[i], self.colwidths[i])
            strs.append(s)
        return self.paddingstr.join(strs)
    
    def write(self, out=sys.stdout):
        """Formats the table to out (file-like object)."""
        headerstr = self._create_row_string(self.header)
        tablesep = (self.sep * len(headerstr)) + '\n'
        out.write(tablesep)
        out.write(headerstr)
        out.write('\n')
        out.write(tablesep)
        for row in self.rows:
            rowstr = self._create_row_string(row)
            out.write(rowstr)
            out.write('\n')
        out.write(tablesep)
        out.write('\n')

    def __repr__(self):
        with StringIO.StringIO() as sio:
            self.write(sio)
        return sio.getvalue()