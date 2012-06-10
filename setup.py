#!/usr/bin/env python

from distutils.core import setup

setup(name="pynocle",
    version="0.3.1",
    author="Rob Galanakis",
    author_email="rob.galanakis@gmail.com",
    url="http://code.google.com/p/pynocle/",
    download_url='http://pypi.python.org/pypi/pynocle',

    packages=['pynocle',
              'pynocle.cyclcompl',
              'pynocle.depgraph',
              'pynocle.funcinfo',
              'pynocle.inheritance',
              'pynocle.sloc'],

    description="Software metrics for your python code",
    long_description=open('README.txt').read(),

    license = "MIT",
    platforms = ['POSIX', 'Windows'],

    requires = ['numpy', 'docutils'],

    classifiers = [
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",

        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Documentation',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development',
        'Topic :: Software Development :: Testing',

        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
    ]
)
