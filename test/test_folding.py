import unittest

import datapath
import datapath.folding


class TestFolding(unittest.TestCase):
    def test_complete_partial_list_valid(self):
        tests = (
            ([(0, 'a')], ['a']),
            ([(1, 'b'), (0, 'a')], ['a', 'b']),
        )
        for i, (test, expected) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                actual = datapath.folding._complete_partial_list(test)
                self.assertEqual(actual, expected)

    def tests_complete_partial_list_invalid(self):
        tests = (
            [(1, 'x')],
            [(0, 'x'), (2, 'y')],
            [(2, 'x'), (0, 'y')],
            [(2, 'x'), (2, 'y')],
        )
        for i, test in enumerate(tests):
            with self.subTest(msg='index {i}'), self.assertRaises(datapath.ValidationError):
                datapath.folding._complete_partial_list(test)

    def test_unfold_path_dict_valid(self):
        tests = (
            ({'': []},     {'': []}),
            ({'': {}},     {'': {}}),
            ({'a': 5},     {'': {'a': 5}}),
            ({'a.b': 17},  {'': {'a': {'b': 17}}}),
            ({'[0]': 5},   {'': [5]}),
            ({'a[0]': 17}, {'': {'a': [17]}}),
            ({
                'a.a': 1,
                'a.b': 2,
                'a.c': 3,
                'a.d[0]': 4,
                'a.d[1]': 5,
                'a.d[2]': 6,
                'b': 7,
                'c': 8,
            }, {'': {
                'a': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': [4, 5, 6],
                },
                'b': 7,
                'c': 8,
            }}),
            ({
                '[0].a': 1,
                '[0].b': 2,
                '[1].a': 3,
                '[2].a.b.c': 4,
            }, {'': [
                {'a': 1, 'b': 2},
                {'a': 3},
                {'a': {'b': {'c': 4}}},
            ]}),
        )
        for i, (path_dict, expected_root_path_dict) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                actual_root_path_dict = datapath.folding.unfold_path_dict(path_dict)
                root = actual_root_path_dict.pop('')
                self.assertFalse(actual_root_path_dict, 'extra keys in root path dict')
                for path, value in path_dict.items():
                    self.assertEqual(datapath.get(root, path), value)

    def test_unfold_path_dict_invalid(self):
        tests = (
            {
                '[0]': 1,
                'a': 2,
            }, {
                'a[11]': 1,
                'a[13]': 2,
            }, {
                'a[0]': 1,
                'a[2]': 2,
            },
            {'': 17},
            {},
        )
        for i, test in enumerate(tests):
            with self.subTest(msg=f'index {i}'), self.assertRaises(datapath.ValidationError):
                datapath.folding.unfold_path_dict(test)


    def test_fold_path_dict(self):
        test = {'a': {'b': list('cde'), 'f': 'g'}}
        expected_sort_items = (
            ('a.b[0]', 'c'),
            ('a.b[1]', 'd'),
            ('a.b[2]', 'e'),
            ('a.f', 'g'),
        )
        self.assertEqual(tuple(sorted(datapath.folding.fold_path_dict(test).items())), expected_sort_items)
