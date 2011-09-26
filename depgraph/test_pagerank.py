#!/usr/bin/env python

import unittest

import pagerank

class TestPageRank(unittest.TestCase):
    def testOneCircle(self):
        links = [
                [1, 1, 1, 1],
                [2],
                [3],
                [4],
                [0]
        ]
        result = pagerank.pageRank(links, alpha=1.0)
        self.assertEqual(str(result), '[ 0.2  0.2  0.2  0.2  0.2]')
    def testTwoCircles(self):
        links = [
                [1, 2],
                [2],
                [3],
                [4],
                [0]
        ]
        result = pagerank.pageRank(links)
        self.assertEqual(str(result), '[ 0.2116109   0.12411822  0.2296187   0.22099231  0.21365988]')
    def testDocMatrix(self):
        links = [
          [0, 2, 2, 3],
          [0],
          [3, 2],
          [0],
        ]
        result = pagerank.pageRank(links)
        self.assertEqual(str(result), '[ 0.36723503  0.0375      0.33665007  0.25861487]')

class TestDepsToMatrix(unittest.TestCase):
    def testConvert(self):
        deps = [
            ['foo', 'bar'],
            ['bar', 'foo'],
            ['foo', 'eggs'],
            ['spam', 'eggs'],
            ['foo', 'bacon']
        ]
        #foo (bar, eggs, bacon),
        #bar (foo),
        #eggs (),
        #spam (eggs),
        #bacon()
        ideal = [
            [1, 2, 4],
            [0],
            [],
            [2],
            []
        ]
        result = pagerank.DependenciesToLinkMatrix(deps).create_matrix()
        self.assertEqual(result, ideal)