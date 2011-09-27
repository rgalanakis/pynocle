#!/usr/bin/env python

import os
import shutil
import tempfile
import unittest

import utils

class MockFormatter(utils.IReportFormatter):
    def __init__(self):
        self.headered = 0
        self.dataed = 0
        self.footered = 0
    def format_report_header(self):
        self.headered += 1
    def format_data(self, data):
        self.dataed += 1
    def format_report_footer(self):
        self.footered += 1

class TestWriteReport(unittest.TestCase):
    def testMethodsCalled(self):
        """Test that the header, data, and footer methods are called."""
        m = MockFormatter()
        utils.write_report(tempfile.mkstemp()[1], '', lambda fs: m)
        self.assertEqual(m.headered, 1)
        self.assertEqual(m.dataed, 1)
        self.assertEqual(m.footered, 1)


class TestSplitRootFileExt(unittest.TestCase):
    def testRegularPath(self):
        """Test the method's behavior on regular paths."""
        v = utils.splitpath_root_file_ext(r'F:\foo\bar.py')
        self.assertEqual(v, ('F:\\foo', 'bar', '.py'))
        v = utils.splitpath_root_file_ext((r'J:\spam.py'))
        self.assertEqual(v, ('J:\\', 'spam', '.py'))

    def testDirOnly(self):
        """Test behavior when passed a path only."""
        v = utils.splitpath_root_file_ext(r'C:\foo\bar')
        self.assertEqual(v, ('C:\\foo', 'bar', ''))
        v = utils.splitpath_root_file_ext('C:\\')
        self.assertEqual(v, ('C:\\', '', ''))

    def testFileOnly(self):
        """Test behavior when passed a filename only."""
        v = utils.splitpath_root_file_ext(r'spam.eggs')
        self.assertEqual(v, ('', 'spam', '.eggs'))
        v = utils.splitpath_root_file_ext(r'spam')
        self.assertEqual(v, ('', 'spam', ''))
        v = utils.splitpath_root_file_ext('.eggs')
        self.assertEqual(v, ('', '.eggs', ''))


class TestSwapKeysAndValues(unittest.TestCase):
    def testWorks(self):
        """Test that it works as described."""
        d = {'a':1, 'b':2}
        d2 = utils.swap_keys_and_values(d)
        self.assertEqual(d2, {1:'a', 2:'b'})

    def testChoosesLastForDuplicateValues(self):
        """Test that function raises an FOO exception if there are duplicate values in values."""
        d = {'a':1, 'b':1, 'c':1}
        self.assertRaises(KeyError, utils.swap_keys_and_values, d)


class TestPrettifyPath(unittest.TestCase):
    def testWorks(self):
        """Test basic functionality."""
        s = utils.prettify_path(r'C:\foo\bar\eggs.spam', leading='C:\\')
        self.assertEqual(s, 'foo\\bar\\eggs')


class TestFindAll(unittest.TestCase):
    """Test the findall function.  We do this by testing against files in a temporary directory with the following
    structure:
    /<temp>/
        bar.ham
        foo.ham
        foo.spam
        /bar/
            bar.ham
            foo.ham
            foo.spam
        /blah/
            bar.ham
            foo.ham
            foo.spam
            /sub/
                bar.ham
                foo.ham
                foo.spam
    """
    def getAndMakeAllTestContentFolders(self):
        """Returns a tuple of absolute paths for all folders including and under self.tempdir.  Will also
        create all directories.
        """
        j = os.path.join
        dirs = (
            self.tempdir,
            j(self.tempdir, 'bar'),
            j(self.tempdir, 'blah'),
            j(self.tempdir, 'blah', 'sub')
        )
        for d in dirs[1:]:
            os.mkdir(d)
        return dirs

    def getAndMakeAllTestContentAbsFilenames(self, dirs):
        """Will create and return the paths of all test content.  dirs should be a a collection of folders, a set of
        test files will be written to each one.
        """
        result = []
        for d in self.dirs:
            result.extend([os.path.join(d, 'bar.ham'), os.path.join(d, 'foo.ham'), os.path.join(d, 'foo.spam')])
        for fn in result:
            with open(fn, 'w') as f:
                f.write('')
        return result

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.dirs = self.getAndMakeAllTestContentFolders()
        self.files = self.getAndMakeAllTestContentAbsFilenames(self.dirs)
        self.assertEqual(len(self.dirs), 4)
        self.assertEqual(len(self.files), 12)
        #Assign our dirs and files to member variables, so we can see what we're accessing- it is better than using
        #indices, IMO
        self.dtc, self.dbar, self.dblah, self.dsub = self.dirs
        self.ftc_bh, self.ftc_fh, self.ftc_fs, self.fbar_bh, self.fbar_fh, self.fbar_fs, self.fblah_bh, \
            self.fblah_fh, self.fblah_fs, self.fsub_bh, self.fsub_fh, self.fsub_fs = self.files

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testFindsFilesOnly(self):
        """Test when given a collection of files, resolves properly."""
        files = utils.find_all([self.ftc_bh, self.ftc_bh, self.ftc_fs, self.fsub_fh, self.fsub_fs], pattern="*.ham")
        #Make sure we don't have .spam files
        ideal = [self.ftc_bh, self.ftc_bh, self.fsub_fh]
        self.assertEqual(sorted(files), sorted(ideal))

    def testFindFoldersOnly(self):
        """Test when given a collection of paths, resolves properly."""
        files = utils.find_all([self.dblah, self.dbar], pattern="*.spam")
        ideal = [self.fblah_fs, self.fsub_fs, self.fbar_fs]
        self.assertEqual(sorted(files), sorted(ideal))

    def testFindFoldersHasOnlyUnique(self):
        """Test that if we pass in multiple folders, some of which are under each other, we don't get duplicate files.
        """
        files = utils.find_all([self.dtc, self.dsub], pattern='*.spam')
        ideal = [self.ftc_fs, self.fbar_fs, self.fblah_fs, self.fsub_fs]
        print files
        print ideal
        self.assertEqual(sorted(files), sorted(ideal))

    def testFindMixed(self):
        """Test when given files and folders, resolves properly."""
        files = utils.find_all([self.dsub, self.fbar_bh, self.fblah_fs], pattern='*.ham')
        ideal = [self.fsub_bh, self.fsub_fh, self.fbar_bh]
        self.assertEqual(sorted(files), sorted(ideal))

    def testExcludesMissing(self):
        """Test that missing files and dirs are excluded from results."""
        fakedir = os.path.join(self.dtc, 'FAKERY')
        fakefile = os.path.join(self.dblah, 'FAKERY2.spam')
        files = utils.find_all([self.dsub, fakedir, fakefile, self.ftc_fs], pattern='*.spam')
        ideal = [self.fsub_fs, self.ftc_fs]
        self.assertEqual(sorted(files), sorted(ideal))