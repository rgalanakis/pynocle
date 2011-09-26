#!/usr/bin/env python

import os
import unittest

import rendering
import xmlrpcrenderer

#class TestRpc(unittest.TestCase):
#    """"Uncomment and try this out while a local server is running, if you want to see the xmlrpc in action.""""
#    def testAll(self):
#        deps = (
#            ('foo', 'bar'),
#            ('foo', 'eggs'),
#            ('bar', 'eggs'))
#        ren = xmlrpcrenderer.XmlRpcRenderer(rendering.DefaultRenderer(deps))
#        output = os.path.join(os.path.dirname(__file__), 'temp_testoutput.png')
#        ren.render(output)
#        self.assertTrue(os.path.exists(output))
  