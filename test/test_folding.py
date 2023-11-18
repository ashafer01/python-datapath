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
            with self.assertRaises(datapath.ValidationError):
                datapath.folding._complete_partial_list(test)

    def test_unfold_path_dict_single(self):
        tests = (
            ({'': []},     {'': []}),
            ({'': {}},     {'': {}}),
            ({'a': 5},     {'': {'a': 5}}),
            ({'a.b': 17},  {'': {'a': {'b': 17}}}),
            ({'[0]': 5},   {'': [5]}),
            ({'a[0]': 17}, {'': {'a': [17]}}),
        )
        for i, (path_dict, expected_root_path_dict) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                actual_root_path_dict = datapath.folding.unfold_path_dict(path_dict)
                root = actual_root_path_dict.pop('')
                self.assertFalse(actual_root_path_dict, 'extra keys in root path dict')
                for path, value in path_dict.items():
                    self.assertEqual(datapath.get(root, path), value)
