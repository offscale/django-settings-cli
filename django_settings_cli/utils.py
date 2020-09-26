from json import dumps
from os import path
from pprint import PrettyPrinter
from string import ascii_letters
from sys import stdout, version

if version[0] == "3":
    string_types = (str,)
else:
    string_types = (basestring,)


def _file_or_dash(parser, arg):
    if arg != "-" and not path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return arg


pp = PrettyPrinter(indent=4).pprint


def stream_tree_as_json(outfile, r, raw_strings):
    stream = stdout if outfile is None else open(outfile, "wt")
    is_str = isinstance(r, string_types)
    new_line = is_str
    if raw_strings:
        s = r if is_str else dumps(r, indent=2)
        stream.write(s[1:-1] if s.startswith('"') else s)
        new_line = r.endswith("\n")
    elif is_str:
        stream.write(quote_str(r))
        new_line = r.endswith("\n")
    else:
        s = r if is_str else dumps(r, indent=2)
        stream.write(quote_str(s))
    if not new_line:
        stream.write("\n")
    if stream != stdout:
        stream.close()


def quote_str(s):
    return '"{}"'.format(s) if len(s) and s[0] in ascii_letters else s
