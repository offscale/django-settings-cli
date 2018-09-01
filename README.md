django_settings_cli
===============
Basic parsing, modifying & emitting for Django settings.py files

## Install dependencies

    pip install -r requirements.txt

## Install package

    pip install .

## Usage

    usage: python -m django_settings_cli [-h] [-o OUTFILE] [-r] [--version]
                                         query infile
    
    Basic parsing, modifying & emitting for Django settings.py files.
    
    positional arguments:
      query                 Query string
      infile                Input file location, or `-` for stdin
    
    optional arguments:
      -h, --help            show this help message and exit
      -o OUTFILE, --outfile OUTFILE
                            Outfile
      -r, --raw-strings     output raw strings, not JSON texts
      --version             show program's version number and exit

## Example

Using the `local.py.example` file in this package:

    $ cat local.py.example | python -m django_settings_cli .DATABASES -
    {
      "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "taiga",
        "USER": "taiga",
        "PASSWORD": "changeme",
        "HOST": "",
        "PORT": ""
      }
    }
