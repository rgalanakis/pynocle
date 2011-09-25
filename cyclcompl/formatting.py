import sys

import cyclcompl
import tableprint

class CCTextFormatter(cyclcompl.CCFormatter):
    def __init__(self, threshold=None, out=sys.stdout):
        if threshold is None:
            threshold = cyclcompl.DEFAULT_THRESHOLD
        elif threshold < 1:
            raise ValueError, 'threshold must be greater than 0, got ' + str(threshold)
        self.threshold = threshold
        self.out = out

    def outstream(self):
        return self.out
    
    def format_report_header(self):
        self.out.write('Cyclomatic Complexity is a measure of decisions that can be made in a procedure.\n')
        self.out.write('See http://en.wikipedia.org/wiki/Cyclomatic_complexity\n')
        self.out.write('Showing items with a CC greater than or equal to %s\n\n' % self.threshold)
        
    def format_failures(self, failures):
        if not failures:
            return
        self.out.write('WARNING: The following files failed to parse:\n')
        for f in failures:
            self.out.write('\t%s\n' % f)
        self.out.write('\n')

    def format_file_and_stats(self, filename, stats):
        self.out.write(filename)
        self.out.write('\n')
        self.format_stats(stats)

    def format_stats(self, stats):
        #Filter and convert the stat rows
        rows = []
        for type, name, cc in stats.flatStats:
            if cc >= self.threshold:
                rows.append([type, name, str(cc)])
        if rows:
            tbl = tableprint.Table(['Type', 'Name', 'CC'], rows)
            tbl.write(self.out)
        else:
            self.out.write('No items with a CC >= %s\n\n' % self.threshold)
        return len(rows)
