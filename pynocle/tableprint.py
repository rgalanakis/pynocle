#!/usr/bin/env python
"""
Module that handles the formatting of table information.
"""

class GoogleChartTable(object):
    """Helper for writing out table data using Google Chart Tools.

    :param title: The title of the page.
    :param colnames_and_types: Should be a collection of two item tuples that
      specify the type and name of the columns, ie:

        [('Filename', 'string'), ('Value', 'number')]

    :param table_var: The variable name for the DataTable object in JS.
    """
    def __init__(self, title, colnames_and_types, table_var='data'):
        self.colnames_and_types = colnames_and_types
        self.table_var = table_var
        self.title = title

    def first_part(self):
        """Returns the first part of the html file for a table as a string.
        Includes the table column definitions.
        After this, the caller should call the 'second_part'
        function to fill the table with actual data.
        """
        lines =["""
<html>
  <head>
    <title>%(title)s</title>
    <link rel="stylesheet" type="text/css" href="pynocle.css" media="screen" />
    <script type='text/javascript' src='https://www.google.com/jsapi'></script>
    <script type='text/javascript'>
      google.load('visualization', '1', {packages:['table']});
      google.setOnLoadCallback(drawTable);
      function drawTable() {
        var %(table_var)s = new google.visualization.DataTable();
        """ % self.__dict__]
        for colname, coltype in self.colnames_and_types:
            lines.append("        data.addColumn('%s', '%s');" % (coltype, colname))
        lines.append('\n')
        return '\n'.join(lines)

    def second_part(self, rows):
        """Writes each row in rows to the table, using formatstr."""
        entrystr = '        data.addRow(%s);\n'
        return '\n'.join([entrystr % row for row in rows])

    def last_part(self, abovetable='', belowtable=''):
        """Returns the final part of the html file for a table as a string.
        This includes the actual drawing,
        and the rest of the html head/body elements.

        :param abovetable: Any HTML to include above the table.
        :param belowtable: Any HTML to include below the table.
        """
        return """
        var table = new google.visualization.Table(document.getElementById('table_div'));
        table.draw(%s, {showRowNumber: true});
      }
    </script>
  </head>

  <body>
    %s<div id='table_div'></div>%s
  </body>
</html>""" % (self.table_var, abovetable, belowtable)
