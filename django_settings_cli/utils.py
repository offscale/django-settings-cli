from os import path


def _file_or_dash(parser, arg):
    if arg != '-' and not path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return arg
