django_settings_cli
===============
Basic parsing, modifying & emitting for Django settings.py files

## Install dependencies

    pip install -r requirements.txt

## Install package

    pip install .

Or if you aren't developing:

    pip install https://api.github.com/repos/offscale/django-settings-cli/zipball#egg=django_settings_cli

## Usage

    usage: python -m django_settings_cli [-h] [--version] {parse,emit} ...
    
    Basic parsing, modifying & emitting for Django settings.py files.
    
    positional arguments:
      {parse,emit}  parse and emit
        parse       Django settings.py emitter
        emit        Django settings.py emitter
    
    optional arguments:
      -h, --help    show this help message and exit
      --version     show program's version number and exit

### `parse` subcommand

    usage: python -m django_settings_cli parse [-h] [-o OUTFILE] [-r]
                                               [-f FORMAT_STR] [--no-eval]
                                               query [infile]
    
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

## Example

Using the `local.py.example` file in this package:

    $ python django_settings_cli parse .DATABASES.default local.py.example
    {
      "ENGINE": "django.db.backends.postgresql",
      "NAME": "taiga",
      "USER": "taiga",
      "PASSWORD": "changeme",
      "HOST": "localhost",
      "PORT": "5432"
    }

Another example, this time from stdin, with a format string and raw (quoteless) output:

    $ cat local.py.example | python django_settings_cli parse .DATABASES.default -f 'postgres://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgres://taiga@localhost:5432/taiga

Let's generalise so it works with any engine:

    $ python django_settings_cli parse .DATABASES.default local.py.example -f '{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgresql://taiga@localhost:5432/taiga

You can also set default values with `or`, like:

    $ python django_settings_cli parse .DATABASES.default local.py.example -f '{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST or "localhost"}:{PORT or 5432}/{NAME}' -r
    postgresql://taiga@localhost:5432/taiga

Security warning: these last examples call `eval`, so people can call `exit(1)` and other more nefarious things. Disable with `--no-eval` argument.
