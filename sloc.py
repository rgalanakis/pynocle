import os
import sys

import tableprint

class SlocInfo(object):
    """Simple data wrapper for SLOC info that can be accessed by attribute, key, or index.  Index order is code,
    comment, blank."""
    def __init__(self, code, comment, blank):
        self.code = code
        self.comment = comment
        self.blank = blank
        self.byinds = code, comment, blank
        self.bykey = {'code':code, 'comment':comment, 'blank':blank}

    def __getitem__(self, item):
        if isinstance(item, basestring):
            return self.bykey[item]
        elif isinstance(item, int):
            return self.byinds[item]
        raise AttributeError, str(item) + ' could not be used as an index or key.'

class SlocInfoExt(SlocInfo):
    """Simple data wrapper for extended SLOC info that can be accessed by attribute, key, or index.
    Index order is code, comment, blank, codeperc, commentperc, blankperc, total, *kvps
    """
    def __init__(self, code, comment, blank, kvps=()):
        """Initialize.  Same as SlocInfo.

        kvps: 2-item tuples of additional keys and values.
        """
        super(SlocInfoExt, self).__init__(code, comment, blank)
        self.total = sum(self.byinds)
        ftotal = max(float(self.total), 1)
        self.codeperc = self.code / ftotal
        self.commentperc = self.comment / ftotal
        self.blankperc = self.blank / ftotal
        for k, v in kvps:
            setattr(self, k, v)

        self.byinds = (self.byinds +
                        (self.codeperc, self.commentperc, self.blankperc, self.total) +
                        tuple(map(lambda kvp: kvp[1], kvps)))

        self.bykey.update({'codeperc':self.codeperc, 'commentperc':self.commentperc, 'blankperc':self.blankperc,
                           'total':self.total})
        self.bykey.update(kvps)

def to_slocinfoext(slocinfo, kvps=()):
    """SlocInfoExt(slocinfo.code, slocinfo.comment, slocinfo.blank, kvps=kvps)"""
    return SlocInfoExt(slocinfo.code, slocinfo.comment, slocinfo.blank, kvps=kvps)

def countlines(filename):
    """Returns a SlocInfo for the source code at filename."""
    codecount, commentcount, blankcount = 0, 0, 0
    with open(filename) as f:
        for line in f.xreadlines():
            if line.isspace():
                blankcount += 1
            elif line.strip().startswith('#'):
                commentcount += 1
            else:
                codecount += 1
    return SlocInfo(codecount, commentcount, blankcount)

def countfiles(filenames):
    """Yields SlocInfos for each file in filenames."""
    for f in filenames:
        yield countlines(f)

class SlocGroup(object):
    """Stores a dictionary at self.d where the keys are filenames and each value is a SlocInfoExt.  The SlocInfo
    objects in the values of SlocGroup.d will be SlocInfoExt instances with a totalperc attribute which represents the
    percentage of the total lines in the SlocGroup that are contained in the file.
    """
    def __init__(self, filenames, slocinfos=None):
        """Initialize.

        filenames: A collection of filenames to populate with.
        slocinfos: A collection of SlocInfo for each filename.  If not provided, calculate the SlocInfo for each
            filename on initialization.  If values is provided, use that instead.  SlocInfoExt will be derived from
            them (and they'll have a totalperc/property).
        """
        valuesext = []
        for si in slocinfos or list(countfiles(filenames)):
            valuesext.append(to_slocinfoext(si)) #We need to use ext for the 'total' attribute below.
        sumtotal = float(sum(map(lambda x: x.total, valuesext)))
        self.d = {}
        for i in range(len(filenames)):
            sie = valuesext[i]
            #update it with totalperc
            self.d[filenames[i]] = to_slocinfoext(sie, kvps=[('totalperc', sie.total / sumtotal)])

    def total(self, key='total'):
        """Return the total number of lines in the group.

        key: The SlocInfoExt key to get the total of.  Default is to return sum total of all lines.
        """
        values = map(lambda x: x[key], self.d.values())
        sumtotal = sum(values)
        return sumtotal

class _CountAll:
    """Helper state class for counting lines of groups of files."""
    def __init__(self, files_and_folders):
        self.processed_files = {}
        self.countall(files_and_folders)

    def countfiles(self, filenames):
        """Updes processed_files with new python files in filenames."""
        newfiles = filter(lambda x: x.endswith('.py'), filenames)
        newfiles = filter(lambda x: x not in self.processed_files, newfiles)
        self.processed_files.update(zip(newfiles, countfiles(newfiles)))

    def countall(self, files_and_folders):
        """Counts the lines of code recursively in all files and folders."""
        self.countfiles(files_and_folders)
        for d in filter(os.path.isdir, files_and_folders):
            paths = map(lambda x: os.path.join(d, x), os.listdir(d))
            self.countall(paths)


def countall(files_and_folders):
    """Return a SlocGroup that includes the filenames of all files in files_and_folders, searched recursively."""
    d = _CountAll(files_and_folders).processed_files
    return SlocGroup(d.keys(), d.values())

class SlocFormatter:
    """Functionality for formatting SLOC info into a readable file."""
    def __init__(self, slocgroup, out=sys.stdout):
        """Initialize.

        slocgroup: A SlocGroup instance.
        out: File-like object.  Defaults to sys.stdout.
        """
        self.slocgroup = slocgroup
        self.out = out
        
    def print_sloc_header(self):
        """Prints out a SLOC explanation and header to self.out."""
        self.out.write('SLOC (Source Lines of Code)\n')
        self.out.write('Measures physical lines of code, lines of comments, and blank lines, in number and\n')
        self.out.write('percentage of file.  Also measures total line count as percentage of total codebase lines.\n')

        self.out.write('\n')

    def _fmtperc(self, i):
        """Format number i as a percentage."""
        perc = '%.1f%%' % (i * 100)
        return perc

    def print_sloc_perfile(self):
        self.out.write('Per-file information for %s files:\n' % len(self.slocgroup.d))
        header = 'Filename', 'Code', 'Code%', 'Comment', 'Comment%', 'Blank', 'Blank%', 'Total', 'Total%'
        c = tableprint.JUST_C
        justs = tableprint.JUST_L, c, c, c, c, c, c, c, c
        rows = []
        sortedbyfilename = sorted(self.slocgroup.d.items(), key=lambda kvp: kvp[0])
        for filename, d in sortedbyfilename:
            row = (filename,
                   str(d['code']), self._fmtperc(d['codeperc']),
                   str(d['comment']), self._fmtperc(d['commentperc']),
                   str(d['blank']), self._fmtperc(d['blankperc']),
                   str(d['total']), self._fmtperc(d['totalperc']))
            rows.append(row)
        tableprint.Table(header, rows, just=justs).write(self.out)


  