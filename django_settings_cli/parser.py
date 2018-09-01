from __future__ import print_function

import ast
import fileinput
import operator
from json import dump
from logging import INFO
from platform import python_version_tuple
from pprint import pprint
from sys import modules, stdout

import astor

from django_settings_cli import get_logger
from django_settings_cli.parser_utils import astdict_to_dict, resolve_collection, node_to_python

if python_version_tuple()[0] == '3':
    from functools import reduce

    imap = map
    xrange = range

log = get_logger(modules[__name__].__name__)
log.setLevel(INFO)


class DebugVisitor(ast.NodeVisitor):
    def visit_Assign(self, node):  # type: (DebugVisitor, ast.Assign) -> any
        for target in node.targets:
            if isinstance(target, ast.Name):
                log.debug('target.id: {} ;'.format(target.id))
                # log.debug('target.ctx: {} ;'.format(target.ctx))
            elif isinstance(target, ast.Subscript):
                log.debug('target.slice.value.s: {} ;'.format(target.slice.value.s))
                if isinstance(target.value, ast.Name):
                    log.debug('target.value.id: {} ;'.format(target.value.id))
            else:
                log.debug('type(target):', type(target), ';')
        if isinstance(node.value, ast.NameConstant):
            log.debug('node.value.value: {} ;'.format(node.value.value))
        if isinstance(node.value, ast.Dict):
            log.debug('astdict_to_dict(node.value)', astdict_to_dict(node.value), ';')
        elif isinstance(node.value, ast.Str):
            log.debug('node.value.s: {} ;'.format(node.value.s))
        elif isinstance(node.value, ast.Num):
            log.debug('node.value.n: {} ;'.format(node.value.n))
        elif isinstance(node.value, ast.List):
            log.debug('LIST node.value.elts: {} ;'.format(list(resolve_collection(node.value.elts))))
        elif isinstance(node.value, ast.Tuple):
            log.debug('TUPLE node.value.elts: {} ;'.format(tuple(resolve_collection(node.value.elts))))
        elif isinstance(node.value, ast.NameConstant):
            log.debug('node.value.value: {} ;'.format(node.value.value))
        else:
            log.debug('NotImplemented for: {value}, of type: {typ} ;'.format(value=node.value, typ=type(node.value)))

        log.debug('\n')


class AssignQuerierVisitor(ast.NodeVisitor):
    filter_value = None  # type: str
    candidates = []

    def visit_Assign(self, node):  # type: (AssignQuerierVisitor, ast.Assign) -> any
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id == self.filter_value:
                    self.candidates.append(target.id)
                    continue
                # log.debug('target.ctx:', target.ctx, ';')
            elif isinstance(target, ast.Subscript):
                log.debug('target.slice.value.s: {} ;'.format(target.slice.value.s))
                if isinstance(target.value, ast.Name):
                    log.debug('target.value.id: {} ;'.format(target.value.id))
            else:
                log.debug('type(target): {} ;'.format(type(target)))

        if len(self.candidates) & 1 == 0:
            return

        self.candidates.append(node_to_python(node))


def debug_py(infile):
    parsed = astor.parse_file(infile)
    DebugVisitor().visit(parsed)
    # log.debug(astor.dump_tree(parsed))


def query_py(infile, query, raw_strings, outfile):
    keys = query.split('.')
    if keys == ['', '']:
        return

    visitor = AssignQuerierVisitor()
    visitor.filter_value = keys[1]

    fstr = ''.join(line.replace('\r\n', '\n').replace('\r', '\n') for line in fileinput.input(infile))
    if infile == '-':
        infile = 'stdin'

    visitor.visit(ast.parse(fstr, filename=infile))

    log.debug('visitor.candidates: {} ;'.format(visitor.candidates))

    r = reduce(operator.getitem, keys[2:-1],
               visitor.candidates[1])[keys[-1]] if len(keys) > 2 else visitor.candidates[1]

    stream = stdout if outfile is None else open(outfile, 'wt')
    if raw_strings:
        pprint(r, stream)
    else:
        dump(r, stream, indent=2)
        stream.write('\n')
    stream.close()
