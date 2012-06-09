#!/usr/bin/env python

class SlocInfo(object):
    """Simple data wrapper for SLOC info that can be accessed by attribute, key, or index.  Index order is code,
    comment, blank.

    code, comment, and blank args/attrs are the lines of code of those classifications.
    """
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

    kvps: 2-item tuples of additional keys and values to set as attrs on the class, add to the by-index collection, and
        the by-key collection.
    Other arguments are same as SlocInfo.
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
    """Converts a SlocInfo to a SlocInfoExt.  Equivalent to
    SlocInfoExt(slocinfo.code, slocinfo.comment, slocinfo.blank, kvps=kvps)
    """
    return SlocInfoExt(slocinfo.code, slocinfo.comment, slocinfo.blank, kvps=kvps)

def count_lines(codelines):
    """Returns a SlocInfo for all the lines of code in codelines."""
    codecount, commentcount, blankcount = 0, 0, 0
    for line in codelines:
        if line.isspace():
            blankcount += 1
        elif line.strip().startswith('#'):
            commentcount += 1
        else:
            codecount += 1
    return SlocInfo(codecount, commentcount, blankcount)

def count_file(filename):
    """Returns a SlocInfo for the source code at filename."""
    with open(filename) as f:
        return count_lines(f.xreadlines())

def count_files(filenames):
    """Yields SlocInfos for each file in filenames."""
    for f in filenames:
        yield count_file(f)

class SlocGroup(object):
    """Stores a dictionary at self.filenamesToSlocInfos where the keys are filenames and each value is a SlocInfoExt.
    The SlocInfo objects in the values of SlocGroup.filenamesToSlocInfos will be SlocInfoExt instances with a
    totalperc attribute which represents the percentage of the total lines in the
    SlocGroup that are contained in the file.

    filenames: A collection of filenames to populate with.
    slocinfos: A collection of SlocInfo for each filename.  If not provided, calculate the SlocInfo for each
        filename on initialization.  If values is provided, use that instead.  SlocInfoExt will be derived from
        them (and they'll have a totalperc/property).
    """
    def __init__(self, filenames, slocinfos=None):
        valuesext = []
        for si in slocinfos or list(count_files(filenames)):
            valuesext.append(to_slocinfoext(si)) #We need to use ext for the 'total' attribute below.
        sumtotal = float(sum(map(lambda x: x.total, valuesext)))
        self.filenamesToSlocInfos = {}
        for i in range(len(filenames)):
            sie = valuesext[i]
            #update it with totalperc
            self.filenamesToSlocInfos[filenames[i]] = to_slocinfoext(sie, kvps=[('totalperc', sie.total / sumtotal)])

    def totallines(self, key='total'):
        """Return the total number of lines in the group.

        key: The SlocInfoExt key to get the total of.  Default is to return sum total of all lines.
        """
        values = map(lambda x: x[key], self.filenamesToSlocInfos.values())
        sumtotal = sum(values)
        return sumtotal
