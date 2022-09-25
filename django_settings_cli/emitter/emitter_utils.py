import ast
import fileinput
from os import environ
from sys import modules, version

from django_settings_cli import get_logger
from django_settings_cli.parser import AssignQuerierVisitor

if version[0] == "2":
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
else:
    from io import StringIO, TextIOWrapper

log = get_logger(modules[__name__].__name__)
log.setLevel(_nameToLevel[environ.get("DJANGO_SETTING_CLI_LOG_LEVEL", "INFO")])


def parse_file(infile, keys):
    visitor = AssignQuerierVisitor()
    visitor.filter_value = (keys[1], keys[2]) if len(keys) > 2 else (keys[1],)

    irregular_fh = isinstance(infile, TextIOWrapper) or isinstance(infile, StringIO)

    fstr = "".join(
        line.replace("\r\n", "\n").replace("\r", "\n")
        for line in (infile if irregular_fh else fileinput.input(infile))
    )
    if infile == "-" or irregular_fh:
        infile = "stdin"

    if keys == ["", ""]:
        return fstr

    return ast.parse(fstr, filename=infile)

    """

    visitor.visit()

    log.debug('visitor.candidates: {} ;'.format(visitor.candidates))
    r = reduce(operator.getitem, keys[2:-1],
               visitor.candidates[1])[keys[-1]] if len(keys) > 2 else visitor.candidates[1]
    return r
    """
