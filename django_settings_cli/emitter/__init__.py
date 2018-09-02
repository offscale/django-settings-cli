from argparse import ArgumentParser
from sys import stdin

from django_settings_cli.utils import _file_or_dash

__desc__ = 'Django settings.py emitter'


def _parser_cli_args(parser=None):
    parser = ArgumentParser(description=__desc__) if parser is None else parser
    parser.add_argument('query', help='Query string', default='.')
    parser.add_argument('infile', help='Input file', type=lambda x: _file_or_dash(parser, x), nargs='?', default=stdin)
    parser.add_argument('-o', '--outfile', help='Outfile')
    return parser
