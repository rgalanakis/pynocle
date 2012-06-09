import os
import shutil
import sys
import tempfile
import unittest

import pynocle._modulefinder as modulefinder


THISDIR = os.path.dirname(os.path.abspath(__file__))


class TestGetModuleFilename(unittest.TestCase):
    def setUp(self):
        self.temproot = None

    def tearDown(self):
        if self.temproot:
            shutil.rmtree(self.temproot)
            sys.path.remove(self.temproot)

    def buildTempDirs(self):
        """Creates the tree of directories and files that can be used for testing."""
        self.temproot = tempfile.mkdtemp()
        sys.path.append(self.temproot)
        def makedir(a, *p):
            path = os.path.join(a, *p)
            os.mkdir(path)
            return path

        self.temp_fake = makedir(self.temproot, '_fake')
        open(os.path.join(self.temp_fake, '__init__.py'), 'w').close()

        self.temp_fake_a = makedir(self.temp_fake, 'a')
        open(os.path.join(self.temp_fake_a, '__init__.py'), 'w').close()

        self.temp_fake_aa = makedir(self.temp_fake_a, 'aa')
        open(os.path.join(self.temp_fake_aa, '__init__.py'), 'w').close()
        open(os.path.join(self.temp_fake_aa, 'eggs.py'), 'w').close()
        open(os.path.join(self.temp_fake_aa, 'spam.py'), 'w').close()

    def testFindsBuiltins(self):
        """Test that it returns only the modulename for builtin modules."""
        self.assertEqual('sys', modulefinder.get_module_filename('sys'))
        self.assertEqual('time', modulefinder.get_module_filename('time'))

    def testRelativePackageImport(self):
        """Test that the a/aa/__init__ module is found when the a/aa module is imported relatively
        from a file in that folder."""
        self.buildTempDirs()
        expected = os.path.join(self.temp_fake_aa, '__init__')
        aaeggs = os.path.join(self.temp_fake_aa, 'eggs.py')
        self.assertEqual(expected, modulefinder.get_module_filename('aa', aaeggs))

    def testAbsolutePackageImport(self):
        """Test that the a/aa/__init__ module is found when the a/aa module is imported relatively
        from a file in that folder."""
        self.buildTempDirs()
        expected = os.path.join(self.temp_fake_aa, '__init__')
        aaeggs = os.path.join(self.temp_fake_aa, 'eggs.py')
        self.assertEqual(expected, modulefinder.get_module_filename('aa', aaeggs))

    def testRelativeImport(self):
        """Test that the a/aa/spam.py module is found when the a/aa/eggs.py module is importing it relatively."""
        self.buildTempDirs()
        expected = os.path.join(self.temp_fake_aa, 'spam')
        aaeggs = os.path.join(self.temp_fake_aa, 'eggs.py')
        self.assertEqual(expected, modulefinder.get_module_filename('spam', aaeggs))

    def testFindAASpamAbs(self):
        """Test that the a/aa/spam.py module is found when the a/aa/eggs.py module is importing it absolutely."""
        self.buildTempDirs()
        expected = os.path.join(self.temp_fake_aa, 'spam')
        aaeggs = os.path.join(self.temp_fake_aa, 'eggs.py')
        self.assertEqual(expected, modulefinder.get_module_filename('_fake.a.aa.spam', aaeggs))

    def testPynocleImportsPynocle(self):
        """Test that importing pynocle works from a folder in the pynocle folder."""
        self.buildTempDirs()
        expected = os.path.join(THISDIR, '__init__')
        self.assertEqual(expected, modulefinder.get_module_filename('pynocle', __file__))
