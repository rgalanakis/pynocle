#!/usr/bin/env python
"""
Module that defines the client class (XmlRpcRenderer) and service (XmlRpcRendererService), and can be run to
run the xmlrpc service itself.

Useful when you have a central machine you can install graphviz on, and then anyone can use it (and the dot machine
doesn't need to be set up with the rest of pynocle, just this client code and dot.
"""
import logging
import optparse
import SimpleXMLRPCServer
import sys
import tempfile
import subprocess
import xmlrpclib

import rendering

class XmlRpcRenderer(rendering.IRenderer):
    """Renderer that sends its dot file to a remote server via XMLRPC to rendering.

    renderer: The renderer to use to create the dot file."""
    def __init__(self, renderer, server_uri='http://localhost:8745/'):
        self.renderer = renderer
        self.proxy = xmlrpclib.ServerProxy(server_uri)

    def savedot(self, filename):
        return self.renderer.savedot(filename)

    def dotexe(self):
        raise NotImplementedError, 'This class does not support running the exe directly.'

    def render(self, outputfilename, dotpath=None, overrideformat=None, wait=True, moreargs=()):
        format = self.getformat(outputfilename, overrideformat)
        dotpath = self.savedot(dotpath) if dotpath else self.savetempdot()
        with open(dotpath, 'rb') as f:
            binarydot = xmlrpclib.Binary(f.read())
        outbytesWrapper = self.proxy.render_dot(binarydot, format)
        with open(outputfilename, 'wb')as f:
            f.write(outbytesWrapper.data)

def parse_args(args=sys.argv):
    o = optparse.OptionParser()
    o.add_option('--host', default='localhost', help='The host to connect the server to.')
    o.add_option('--port', default=8745, help='The port to connect the server to.')
    o.add_option('--log', default='rendererservice.log', help='Log filename.')
    o.add_option('--dot', default='dot', help='dot.exe filename.')
    return o.parse_args(args=args)

class XmlRpcRendererService:
    def __init__(self, dotexe):
        self.logger = logging.getLogger()
        self.dotexe = dotexe

    def render_dot(self, binarydot, format):
        """Takes in an xmlrpclib.Binary of a dot file's contents and a target format, and returns a Binary wrapper
        around the image file's bytes.
        """
        self.logger.info('Inside render_dot.')
        tempdot = tempfile.mkstemp('.dot')[1]
        self.logger.info('Saving dot file to %s' % tempdot)
        with open(tempdot, 'wb') as f:
            f.write(binarydot.data)

        tempout = tempfile.mkstemp()[1]
        clargs = [self.dotexe, '-T' + format, tempdot, '-o', tempout]
        self.logger.info('Opening a subprocess with: %s', clargs)
        try:
            p = subprocess.Popen(clargs)
            p.communicate()
            self.logger.info('Call to dot returned successfully.')
        except WindowsError:
            import traceback
            self.logger.exception(traceback.format_exc())
            #Let's swallow errors here, we don't have any persistent state and this is a very simple server.

        with open(tempout, 'rb') as f:
            outbytes = f.read()
        self.logger.info('Returning %s bytes', len(outbytes))
        return xmlrpclib.Binary(outbytes)

if __name__ == '__main__':
    opts, args = parse_args()
    logging.basicConfig(filename=opts.log)
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(logging.StreamHandler())
    logging.info('Starting service.  clargs: %s', sys.argv)
    server = SimpleXMLRPCServer.SimpleXMLRPCServer((opts.host, int(opts.port)))
    server.register_instance(XmlRpcRendererService(opts.dot))
    logging.info('Serving...')
    server.serve_forever()