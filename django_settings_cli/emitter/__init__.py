import ast
from argparse import ArgumentParser
from enum import Enum
from sys import stdin, stdout

import astor

from django_settings_cli.utils import _file_or_dash

__desc__ = "Django settings.py emitter"


class MergeStrategy(Enum):
    upsert = "upsert"
    merge_into = "merge_into"
    merge_from = "merge_from"

    def __str__(self):
        return self.value


def _parser_cli_args(parser=None):
    parser = ArgumentParser(description=__desc__) if parser is None else parser
    parser.add_argument("query", help="Query string", default=".")
    parser.add_argument(
        "infile",
        help="Input file",
        type=lambda x: _file_or_dash(parser, x),
        nargs="?",
        default=stdin,
    )
    parser.add_argument("-o", "--outfile", help="Outfile")
    parser.add_argument("-i", "--input", dest="input_s", help="Input to merge")
    parser.add_argument(
        "-m",
        "--merge",
        help="Merge strategy",
        type=MergeStrategy,
        choices=tuple(MergeStrategy),
    )
    return parser


def emit(infile, query, input_s, merge, outfile):
    keys = query.split(".")
    tree = astor.parse_file(infile)  # parse_file(infile=infile, keys=keys)

    # print(astor.dump_tree(tree))

    if merge == MergeStrategy.upsert:
        # TODO: Traverse and remove existent node(s) that match
        tree.body.append(ast.parse(input_s, filename="input_s"))
    else:
        raise NotImplementedError(merge)

    stream = stdout if outfile is None else open(outfile, "wt")
    stream.write(astor.to_source(tree))

    # stream_tree_as_json(outfile=outfile, r=tree, raw_strings=None)
