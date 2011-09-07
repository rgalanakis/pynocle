import glob
import optparse
import os
import sys

import cc

USAGE = 'usage: %prog [options] *.py'
VERSION = 'Sat Aug 21 version with support for overall complexity (http://aufather.wordpress.com)'


def create_optionparser():

    parser = optparse.OptionParser(usage=USAGE, version=VERSION)
    parser.add_option('-c', '--complexity', dest='complexity',
            action='store_true', default=False,
            help='print complexity details for each file/module')
    parser.add_option('-t', '--threshold', dest='threshold',
            type='int', default=7,
            help='threshold of complexity to be ignored (default=7)')
    parser.add_option('-a', '--all', dest='allItems',
            action='store_true', default=False,
            help='print all metrics')
    parser.add_option('-s', '--summary', dest='summary',
            action='store_true', default=False,
            help='print cumulative summary for each file/module')
    parser.add_option('-r', '--recurs', dest='recurs',
            action='store_true', default=False,
            help='process files recursively in a folder')
    parser.add_option('-d', '--debug', dest='debug',
            action='store_true', default=False,
            help='print debugging info like file being processed')
    parser.add_option('-o', '--outfile', dest='outfile',
            default=None,
            help='output to OUTFILE (default=stdout)')
    return parser

def parse_cmd_args(argv=sys.argv, parser=create_optionparser()):
    """Calls/returns parser.parse_args(argv), and performs some additional configuration of options if needed."""
    options, args = parser.parse_args(args=argv)
    if options.allItems:
        options.complexity = True
        options.summary = True
    return options, args

def create_file_list(paths, recurse=False):
    """Return a collection of files collected from paths.

    paths: Collection fo files and/or directory paths.
    recurs: Whether to recurse the directories in paths.
    """
    fl = _FileList(paths, recurse)
    fl.get_all()
    return fl.files

class _FileList(object):
    def __init__(self, paths, recurs=False):
        """Initialize.  You need to call getAll to fill the .files attribute.  Use create_file_list to wrap this in
        an easier API.

        paths: Collection of file and/or directory paths.
        recurs: Recurse directories or not.
        """
        self.paths = paths
        self.recurs = recurs
        self.files = set()

    def get_all(self):
        for path in self.paths:
            arg = os.path.expandvars(os.path.expanduser(path))
            if os.path.isdir(arg):
                self._get_dirs(arg)
            elif os.path.isfile(arg):
                self._get_files(arg)
            else:
                self._get_packages(arg)

    def _get_dirs(self, name):
        if self.recurs:
            self._get_dirs_recursively(name)
            return

        for f in glob(os.path.join(name, '*.py')):
            if os.path.isfile(f):
                self.files.add(os.path.abspath(f))

    def _get_dirs_recursively(self, name):
        for root, folders, files in os.walk(name):
            for f in files:
                if f.endswith(".py"):
                    self.files.add(os.path.abspath(os.path.join(root, f)))

    def _get_files(self, name):
        if name.endswith(".py"):
            # only check for python files
            self.files.add(os.path.abspath(name))

    def _get_packages(self, name):
        join = os.path.join
        exists = os.path.exists
        partial_path = name.replace('.', os.path.sep)
        for p in sys.path:
            path = join(p, partial_path, '__init__.py')
            if exists(path):
                self.files.add(os.path.abspath(path))
            path = join(p, partial_path + '.py')
            if exists(path):
                self.files.add(os.path.abspath(path))
        raise Exception('invalid module')

def print_fail_files(fail, outfile=sys.stdout):
    """Print out files in fail to outfile."""
    if fail:
        outfile.write("Totally %d files failed\n" % len(fail))
        for f in fail:
            outfile.write("FAILED to process file: %s\n" % f)


def main(argv=sys.argv):
    options, args = parse_cmd_args(argv=argv)
    files = create_file_list(args, options.recurs)
    outfile = open(options.outfile, 'w') if options.outfile else sys.stdout
    pp = cc.PrettyPrinter(outfile, options.complexity, options.threshold, options.summary)
    fail = set()
    sumStats = cc.FlatStats()
    for f in files:
        if options.debug:
            print "File being processed: ", f
        code = open(f).read() + '\n'
        stats = cc.measure_complexity(code, f)
        if not stats:
            fail.add(f)
            continue
        sumStats = sumStats + stats
        pp.pprint(f, stats)
    outfile.write("Total Cumulative Statistics\n")
    outfile.write(str(sumStats))
    outfile.write('\n')
    print_fail_files(fail, outfile)

