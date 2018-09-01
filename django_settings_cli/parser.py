from __future__ import print_function

import ast
import fileinput
import operator
from io import TextIOWrapper
from json import dump, dumps
from logging import _nameToLevel
from os import environ
from platform import python_version_tuple
from sys import modules, stdout

import astor

from django_settings_cli import get_logger
from django_settings_cli.parser_utils import astdict_to_dict, resolve_collection, node_to_python, parenthetic_contents

if python_version_tuple()[0] == '3':
    from functools import reduce

    imap = map
    xrange = range

log = get_logger(modules[__name__].__name__)
log.setLevel(_nameToLevel[environ.get('DJANGO_SETTING_CLI_LOG_LEVEL', 'INFO')])


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
    filter_value = None  # type: tuple
    candidates = []
    outer_key = None

    def visit_Assign(self, node):  # type: (AssignQuerierVisitor, ast.Assign) -> any
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id == self.filter_value[0]:
                    self.candidates.append(target.id)
                # log.debug('target.ctx:', target.ctx, ';')
            elif isinstance(target, ast.Subscript):
                log.debug('target.slice.value.s: {} ;'.format(target.slice.value.s))
                if len(self.filter_value) > 1 and target.slice.value.s == self.filter_value[1]:
                    self.candidates.append(target.slice.value.s)
                    self.outer_key = target.slice.value.s
                if isinstance(target.value, ast.Name):
                    log.debug('target.value.id: {} ;'.format(target.value.id))
            else:
                log.debug('type(target): {} ;'.format(type(target)))

        if len(self.candidates) & 1 == 0:
            return

        self.candidates.append(
            (lambda py: py if self.outer_key is None else {self.outer_key: py})(node_to_python(node))
        )
        self.outer_key = None


def debug_py(infile):
    parsed = astor.parse_file(infile)
    DebugVisitor().visit(parsed)
    # log.debug(astor.dump_tree(parsed))


def parse_file(infile, keys):
    visitor = AssignQuerierVisitor()
    visitor.filter_value = (keys[1], keys[2]) if len(keys) > 2 else (keys[1],)

    fstr = ''.join(line.replace('\r\n', '\n').replace('\r', '\n')
                   for line in (infile if isinstance(infile, TextIOWrapper) else fileinput.input(infile)))
    if infile == '-' or isinstance(infile, TextIOWrapper):
        infile = 'stdin'
    visitor.visit(ast.parse(fstr, filename=infile))

    log.debug('visitor.candidates: {} ;'.format(visitor.candidates))
    r = reduce(operator.getitem, keys[2:-1],
               visitor.candidates[1])[keys[-1]] if len(keys) > 2 else visitor.candidates[1]
    return r


def query_py(infile, query, raw_strings, format_str, outfile):
    keys = query.split('.')
    if keys == ['', '']:
        return

    r = parse_file(infile, keys)

    stream = stdout if outfile is None else open(outfile, 'wt')
    if format_str:
        r = format_str.format(**{k: r[k] for k in parenthetic_contents(format_str)})
    if raw_strings:
        s = dumps(r, indent=2)
        stream.write(s[1:-1] if s.startswith('"') or s.startswith("'") else s)
    else:
        dump(r, stream, indent=2)
    stream.write('\n')
    stream.close()
