django_settings_cli
===================
[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech)
[![License](https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)

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

    $ python -m django_settings_cli parse .DATABASES.default local.py.example
    {
      "ENGINE": "django.db.backends.postgresql",
      "NAME": "taiga",
      "USER": "taiga",
      "PASSWORD": "changeme",
      "HOST": "localhost",
      "PORT": "5432"
    }

Another example, this time from stdin, with a format string and raw (quoteless) output:

    $ cat local.py.example | python -m django_settings_cli parse .DATABASES.default -f 'postgres://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgres://taiga@localhost:5432/taiga

Let's generalise so it works with any engine:

    $ python -m django_settings_cli parse .DATABASES.default local.py.example -f '{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST}:{PORT}/{NAME}' -r
    postgresql://taiga@localhost:5432/taiga

You can also set default values with `or`, like:

    $ python -m django_settings_cli parse .DATABASES.default local.py.example -f '{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST or "localhost"}:{PORT or 5432}/{NAME}' -r
    postgresql://taiga@localhost:5432/taiga

Security warning: these last examples call `eval`, so people can call `exit(1)` and other more nefarious things. Disable with `--no-eval` argument.

## License

Licensed under any of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)
- CC0 license ([LICENSE-CC0](LICENSE-CC0) or <https://creativecommons.org/publicdomain/zero/1.0/legalcode>)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
licensed as above, without any additional terms or conditions.
