#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from os import path
from sys import modules

from django_settings_cli import __version__
from django_settings_cli.parser import debug_py, query_py


def _file_or_dash(parser, arg):
    if arg != '-' and not path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return arg


def _build_parser():
    parser = ArgumentParser(
        prog='python -m {}'.format(modules[__name__].__package__),
        description='Basic parsing, modifying & emitting for Django settings.py files.'
    )
    parser.add_argument('query', help='Query string', default='.')
    parser.add_argument('infile', help='Input file', type=lambda x: _file_or_dash(parser, x))
    parser.add_argument('-o', '--outfile', help='Outfile')
    parser.add_argument('-r', '--raw-strings', help='output raw strings, not JSON texts', action='store_true')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    return parser


if __name__ == '__main__':
    args = _build_parser().parse_args()
    # debug_py
    query_py(**dict(args._get_kwargs()))
