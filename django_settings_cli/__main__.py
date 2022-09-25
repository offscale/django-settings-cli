#!/usr/bin/env python

from argparse import ArgumentParser
from sys import argv, modules

from django_settings_cli import __version__
from django_settings_cli import emitter as django_settings_emitter
from django_settings_cli import parser as django_settings_parser


def _build_parser():
    """
    CLI parser builder using builtin `argparse` module

    :returns: instanceof ArgumentParser
    :rtype: ```ArgumentParser```
    """
    parser = ArgumentParser(
        prog="python -m {}".format(modules[__name__].__package__),
        description="Basic parsing, modifying & emitting for Django settings.py files.",
    )
    subparsers = parser.add_subparsers(help="parse and emit", dest="command")

    django_settings_parser._parser_cli_args(
        subparsers.add_parser("parse", help=django_settings_parser.__desc__)
    )

    django_settings_emitter._parser_cli_args(
        subparsers.add_parser("emit", help=django_settings_emitter.__desc__)
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    return parser


if __name__ == "__main__":
    idx = next((_idx for _idx, arg in enumerate(argv) if arg == "-"), None)
    if idx is not None:
        del argv[idx]

    kwargs = dict(_build_parser().parse_args()._get_kwargs())
    # django_settings_parser.debug_py
    command = kwargs.pop("command")
    {
        "parse": django_settings_parser.query_py_with_output,
        "emit": django_settings_emitter.emit,
    }[command](**kwargs)
