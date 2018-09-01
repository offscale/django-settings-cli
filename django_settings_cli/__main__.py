#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from os import path
from sys import modules

from django_settings_cli import __version__
from django_settings_cli.parser import parse_settings


def _file_exists(parser, arg):
    if not path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return arg


def _build_parser():
    parser = ArgumentParser(
        prog='python -m {}'.format(modules[__name__].__package__),
        description='Basic parsing, modifying & emitting for Django settings.py files.'
    )
    parser.add_argument('-i', '--infile', help='Input file', type=lambda x: _file_exists(parser, x))
    parser.add_argument('-o', '--outile', help='Outfile', type=FileType('wt'))
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    return parser


if __name__ == '__main__':
    args = _build_parser().parse_args()
    parse_settings(args.infile)
