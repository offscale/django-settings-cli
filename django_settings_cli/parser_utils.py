# from typing import Hashable
import ast
from platform import python_version_tuple
from sys import modules

from django_settings_cli import get_logger

if python_version_tuple()[0] == '3':
    imap = map
    xrange = range

log = get_logger(modules[__name__].__name__)
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
    log.debug('NotImplemented for: {value}, of type: {typ} ;'.format(value=node, typ=type(node)))
    return node


def astdict_to_dict(node):
    if not isinstance(node, ast.Dict) or isinstance(node, dict):
        return node

    return dict(zip(imap(get_value, node.keys),
                    imap(get_value, node.values)))


def collection_to_value(node):
    if type(node) in raw_types:
        return node
    return (get_value(n) for n in node)


def ast_type_to_native(node):
    if isinstance(node, ast.Tuple):
        return tuple
    elif isinstance(node, ast.List):
        return list
    return node


def resolve_collection(node):
    def it(e):
        typ = ast_type_to_native(e)
        return typ(collection_to_value(e.elts)) if typ in (list, tuple) else e.elts

    return imap(it, node)


def node_to_python(node):
    if isinstance(node.value, ast.NameConstant):
        return node.value.value
    elif isinstance(node.value, ast.Dict):
        return astdict_to_dict(node.value)
    elif isinstance(node.value, ast.Str):
        return node.value.s
    elif isinstance(node.value, ast.Num):
        return node.value.n
    elif isinstance(node.value, ast.List):
        return list(resolve_collection(node.value.elts))
    elif isinstance(node.value, ast.Tuple):
        return tuple(resolve_collection(node.value.elts))
    elif isinstance(node.value, ast.NameConstant):
        return node.value.value

    log.debug('NotImplemented for: {value}, of type: {typ} ;'.format(value=node.value, typ=type(node.value)))
