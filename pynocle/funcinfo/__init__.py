#!/usr/bin/env python

import compiler
import compiler.ast


import pynocle.utils as utils


class FuncInfo(object):
    def __init__(self, filename, astnode):
        self.filename = filename


def all_func_nodes(astnode):
        isclass = lambda x: isinstance(x, compiler.ast.Class)
        nodes = filter(isclass, utils.flatten(astnode, lambda x: x.getChildNodes()))
        return nodes


def extract_funcinfos(*filenames):
    result = []
    for f in filenames:
        try:
            ast = compiler.parseFile(f)
        except SyntaxError:
            continue
        for node in all_func_nodes(ast):
            fi = FuncInfo(f, node)
            result.append(fi)
    return result
