import doctest
import unittest
from importlib import import_module

import datapath


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(import_module('datapath.format')))
    return tests


class TestFormat(unittest.TestCase):
    def test_format_simple(self):
        format_strings = (
            ('one {} two {} three', 2),
            ('{} one', 1),
            ('one {}', 1),
            ('{}{}{}', 3),
            ('{}', 1),
        )
        test_obj = {
            'a': list('123'),
            'b': [{'c': list('456')}, 7],
        }
        paths = (
            ('{a[0]}', test_obj['a'][0]),
            ('{b[1]}', test_obj['b'][1]),
            ('{b[0].c[2]}', test_obj['b'][0]['c'][2]),
        )
        for index, (format_string, num_paths) in enumerate(format_strings):
            with self.subTest(msg=f'index {index}'):
                my_paths = (path[0] for path in paths[:num_paths])
                values = (path[1] for path in paths[:num_paths])
                real_format_string = format_string.format(*my_paths)
                expected = format_string.format(*values)
                actual = datapath.format(test_obj, real_format_string)
                self.assertEqual(expected, actual)


class TestFormatIterate(unittest.TestCase):
    def test_format_iterate_no_literal(self):
        test_obj = {'a': list('1234')}
        expected = '1234'
        for index, value in enumerate(datapath.format_iterate(test_obj, '{a[]}')):
            self.assertEqual(value, expected[index])

    def test_format_iterate_trailing_literal(self):
        test_obj = {'a': list('1234')}
        expected = '1234'
        for index, value in enumerate(datapath.format_iterate(test_obj, '{a[]} x')):
            self.assertEqual(value, expected[index] + ' x')
