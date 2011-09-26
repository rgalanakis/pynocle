#!/usr/bin/env python

import compiler

import pynocle.utils as utils

class ClassInfo(object):
    def __init__(self, filename, classname, bases):
        self.filename = filename
        self.classname = classname
        self.bases = bases

    def __str__(self):
        return 'ClassInfo(filename=%s, classname=%s, bases=%s)' % (self.filename, self.classname, self.bases)

    __repr__ = __str__


class ClassGraph(object):
    def __init__(self, classinfos):
        self.classinfos = classinfos

    def group_by_classname(self):
        """Returns a dictionary of dictionaries: {classname: {filename: [bases]}}.  Necessary because multiple files
        can contain the same class name.
        """
        byclass = {}
        for ci in self.classinfos:
            byfile = byclass.setdefault(ci.classname, {})
            byfile[ci.filename] = ci.bases


class InheritanceBuilder(object):
    def __init__(self, files):
        self._classinfos = []
        for f in files:
            self.process_file(f)

    def _all_class_nodes(self, astnode):
        isclass = lambda x: isinstance(x, compiler.ast.Class)
        nodes = filter(isclass, utils.flatten(astnode, lambda x: x.getChildNodes()))
        return nodes

    def _get_classname_from_node(self, node):
        if isinstance(node, compiler.ast.Class):
            return node.name
        if isinstance(node, compiler.ast.Getattr):
            return '%s.%s' % (node.expr.name, node.attrname)
        
    def process_file(self, filename):
        try:
            ast = compiler.parseFile(filename)
        except SyntaxError:
            return
        for node in self._all_class_nodes(ast):
            ci = ClassInfo(filename, node.name, [self._get_classname_from_node(node) for namenode in node.bases])
            self._classinfos.append(ci)

    def classinfos(self):
        return self.classinfos

        