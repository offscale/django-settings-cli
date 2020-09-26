# from typing import Hashable
import ast
from functools import partial
from itertools import takewhile
from os import environ
from string import ascii_letters, digits
from sys import modules, version

from django_settings_cli import get_logger
from django_settings_cli.parser import _nameToLevel

if version[0] == "2":
    from itertools import imap as map

    range = xrange

log = get_logger(modules[__name__].__name__)
log.setLevel(_nameToLevel[environ.get("DJANGO_SETTING_CLI_LOG_LEVEL", "INFO")])

raw_types = frozenset(("str", "unicode", "int", "long", "type(None)"))


def get_value(node):
    if type(node) in raw_types:
        return node
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return node.n
    elif hasattr(node, "value"):
        if hasattr(node.value, "value"):
            return node.value.value
        else:
            return node.value
    elif isinstance(node, ast.Dict):
        return astdict_to_dict(node)
    log.debug(
        "NotImplemented for: {value}, of type: {typ} ;".format(
            value=node, typ=type(node)
        )
    )
    return node


def astdict_to_dict(node):
    if not isinstance(node, ast.Dict) or isinstance(node, dict):
        return node

    return dict(zip(map(get_value, node.keys), map(get_value, node.values)))


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

    return map(it, node)


def node_to_python(node):
    if isinstance(node.value, ast.Dict):
        return astdict_to_dict(node.value)
    elif isinstance(node.value, ast.Str):
        return node.value.s
    elif isinstance(node.value, ast.Num):
        return node.value.n
    elif isinstance(node.value, ast.List):
        return list(resolve_collection(node.value.elts))
    elif isinstance(node.value, ast.Tuple):
        return tuple(resolve_collection(node.value.elts))
    elif version[0] == "3" and isinstance(node.value, (ast.Constant, ast.NameConstant)):
        return node.value.value
    log.debug(
        "NotImplemented for: {value}, of type: {typ} ;".format(
            value=node.value, typ=type(node.value)
        )
    )


# From: https://stackoverflow.com/a/4285211
def parenthetic_contents(s):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(s):
        if c == "{":
            stack.append(i)
        elif c == "}" and stack:
            start = stack.pop()
            yield s[start + 1 : i]


def eval_parens(k, r, ref, no_eval):
    num = sum(1 for _ in takewhile(lambda ch: ch in ascii_letters + digits, k))

    val = r[k[:num]]
    if k[num:]:
        if not no_eval:
            evil = '"{}"{}'.format(
                r[k[:num]], k[num:].replace(k[:num], '"{}"'.format(r[k[:num]]))
            )
            val = eval(evil, r)
        ref["format_str"] = ref["format_str"].replace(k, k[:num])

    return k[:num], val
