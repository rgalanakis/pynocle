#!/usr/bin/env python

from distutils.core import setup

try:
    import pynocle
except ImportError:
    pynocle = None

setup(name="pynocle",
      version=pynocle.__version__,
      author=pynocle.__author__,
      author_email=pynocle.__email__,
      url="http://code.google.com/p/pynocle/",
      description="Software metrics for your python code",
      long_description=open('README.txt').read(),
      license='GPL',
      packages=['', 'cyclcompl', 'depgraph', 'inheritance', 'sloc'],
      install_requires=['numpy', 'coverage']
     )