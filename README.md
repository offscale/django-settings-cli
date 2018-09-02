django_settings_cli
===============
Basic parsing, modifying & emitting for Django settings.py files

## Install dependencies

    pip install -r requirements.txt

## Install package

    pip install .

## Usage

    usage: python -m django_settings_cli [-h] [-o OUTFILE] [-r] [-f FORMAT_STR]
                                         [--no-eval] [--version]
                                         query [infile]
    
    Basic parsing, modifying & emitting for Django settings.py files.
    
    positional arguments:
      query                 Query string
      infile                Input file
    
    optional arguments:
      -h, --help            show this help message and exit
      -o OUTFILE, --outfile OUTFILE
                            Outfile
      -r, --raw-strings     output raw strings, not JSON texts
      -f FORMAT_STR, --format FORMAT_STR
                            Format (currently only supports top-level key of dict)
      --no-eval             Disable eval (for format str)
      --version             show program's version number and exit


## Example

Using the `local.py.example` file in this package:

    $ python -m django_settings_cli .DATABASES.default local.py.example
    {
      "ENGINE": "django.db.backends.postgresql",
      "NAME": "taiga",
      "USER": "taiga",
      "PASSWORD": "changeme",
      "HOST": "localhost",
      "PORT": "5432"
    }

Another example, this time from stdin, with a format string and raw (quoteless) output:

    $ cat local.py.example | python -m django_settings_cli .DATABASES.default -f 'postgres://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgres://taiga@localhost:5432/taiga

Let's generalise so it works with any engine:

    $ python -m django_settings_cli .DATABASES.default local.py.example -f '{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgresql://taiga@localhost:5432/taiga

Security warning: this last example calls `eval`, so people can call `exit(1)` and other more nefarious things. Disable with `--no-eval` argument.
