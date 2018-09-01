from __future__ import print_function

import ast
from platform import python_version_tuple
from pprint import PrettyPrinter

import astor

if python_version_tuple()[0] == '3':
    imap = map
    xrange = range

pp = PrettyPrinter(indent=4).pprint

# from typing import Hashable
raw_types = frozenset(('str', 'unicode', 'int', 'long', 'NoneType'))


def get_value(node):
    if type(node) in raw_types:
        return node
    if any((
        isinstance(node, ast.Subscript),
        isinstance(node, ast.NameConstant)
    )):
        return node.value
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return node.n
    elif hasattr(node, 'value') and hasattr(node.value, 'value'):
        return node.value.value
    elif isinstance(node, ast.Dict):
        return astdict_to_dict(node)
    print('Not handling:', node, 'of type:', type(node), ';')
    return node


def astdict_to_dict(node):
    if not isinstance(node, ast.Dict) or isinstance(node, dict):
        return node

    return dict(zip(map(get_value, node.keys),
                    map(get_value, node.values)))


def collection_to_value(node):
    if type(node) in raw_types:
        return node
    return (get_value(n) for n in node)


def ast_type_to_native(node):
    if isinstance(node, ast.Tuple):
        return tuple
    elif isinstance(node, ast.List):
        return list
    print('type', type(node), node)
    return node


def resolve_collection(node):
    def it(e):
        typ = ast_type_to_native(e)
        return typ(collection_to_value(e.elts)) if typ in (list, tuple) else e.elts

    return map(it, node)


class DebugVisitor(ast.NodeVisitor):
    filter_value = None  # type: str

    def visit_Assign(self, node):  # type: (DebugVisitor, ast.Assign) -> any
        for target in node.targets:
            if isinstance(target, ast.Name):
                print('target.id:', target.id, ';')
                # print('target.ctx:', target.ctx, ';')
            elif isinstance(target, ast.Subscript):
                print('target.slice', target.slice.value.s)
                if isinstance(target.value, ast.Name):
                    print('target.value.id', target.value.id, ';')
            else:
                print('type(target):', type(target), ';')
        if isinstance(node.value, ast.NameConstant):
            print('node.value.value:', node.value.value, ';')
        if isinstance(node.value, ast.Dict):
            print('node as dict', astdict_to_dict(node.value), ';')
        elif isinstance(node.value, ast.Str):
            print('node.value.s:', node.value.s, ';')
        elif isinstance(node.value, ast.Num):
            print('node.value.n:', node.value.n, ';')
        elif isinstance(node.value, ast.List):
            print('LIST node.value.elts:', list(resolve_collection(node.value.elts)), ';')
        elif isinstance(node.value, ast.Tuple):
            print('TUPLE node.value.elts:', tuple(resolve_collection(node.value.elts)), ';')
        elif isinstance(node.value, ast.NameConstant):
            print('node.value.s:', node.value.value, ';')
        else:
            print('Not handling:', node.value, 'of type:', type(node.value), ';')

        print('\n')


def parse_settings(fname):
    parsed = astor.parse_file(fname)
    DebugVisitor().visit(parsed)
    # print(astor.dump_tree(parsed))
