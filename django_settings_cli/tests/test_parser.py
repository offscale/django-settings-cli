from os import path, environ
from sys import modules
from unittest import TestCase, main as unittest_main

from pkg_resources import resource_filename

from django_settings_cli.parser import query_py_parser


class TestParser(TestCase):
    local_py_example = resource_filename(
        path.basename(modules[__name__].__spec__.origin.replace('/tests/{}.py'.format(__name__), '')),
        path.join('_data', 'local.py.example'))

    def setUp(self):
        environ['DJANGO_SETTING_CLI_LOG_LEVEL'] = 'NOTSET'

    def test_empty_query(self):
        with open(self.local_py_example, 'rt') as f:
            self.assertEqual(query_py_parser(infile=self.local_py_example, query='.'), f.read())

    def test_simple_key_val(self):
        self.assertFalse(query_py_parser(infile=self.local_py_example, query='.DEBUG'))

    def test_simple_key_collection_val(self):
        self.assertEqual(query_py_parser(infile=self.local_py_example, query='.ADMINS'),
                         (('Admin', 'example@example.com'),))

    def test_sliced_key_collection_val(self):
        self.assertEqual(query_py_parser(infile=self.local_py_example, query='.REST_FRAMEWORK.DEFAULT_THROTTLE_RATES'),
                         {'anon-read': None,
                          'anon-write': '20/min',
                          'create-memberships': None,
                          'import-dump-mode': '1/minute',
                          'import-mode': None,
                          'login-fail': None,
                          'register-success': None,
                          'user-detail': None,
                          'user-read': None,
                          'user-update': None,
                          'user-write': None})

    def test_sliced_key_collection_val_sub_val(self):
        self.assertEqual(
            query_py_parser(infile=self.local_py_example, query='.REST_FRAMEWORK.DEFAULT_THROTTLE_RATES.anon-write'),
            '20/min')

    def test_format_str(self):
        self.assertEqual(
            query_py_parser(
                infile=self.local_py_example, query='.DATABASES.default',
                format_str='{ENGINE[ENGINE.rfind(".")+1:]}://{USER}@{HOST}:{PORT}/{NAME}'),
            'postgresql://taiga@localhost:5432/taiga')


if __name__ == '__main__':
    unittest_main()
