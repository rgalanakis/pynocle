#!/usr/bin/env python

import tempfile
import unittest

import pynocle.utils as utils


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
