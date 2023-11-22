import unittest

import datapath
import datapath._base
import datapath.folding

valid_paths = (
    'test',
    'test1.test2',
    'test[1]',
    'test[1][2]',
    '[1][2][3][4]',
    'test[1].test[2].test[3][4].test',
    ',%$^%^!@#$%',
    '],%$^%^!@#$%[1]',
    '1234567',
    '1234567[1]',
    '[0]',
    '[5]',
    '',
)

class TestDatapath(unittest.TestCase):
    def test_validate_path_valid_cases(self):
        for valid_path in valid_paths:
            with self.subTest(msg=f'valid path `{valid_path}`'):
                try:
                    datapath.validate_path(valid_path)
                except datapath.ValidationError:
                    self.fail(f'valid path `{valid_path}` was found invalid')


    def test_validate_path_invalid_cases(self):
        invalid_paths = (
            '[1'
            'test[1',
            '[1[2]',
            '[,%$^%^!@#$%[1]',
        )
        for invalid_path in invalid_paths:
            with self.subTest(msg=f'invalid path `{invalid_path}`'), self.assertRaises(datapath.ValidationError):
                datapath.validate_path(invalid_path)

    def test_split_path(self):
        tests = (
            ('', tuple()),
            ('test', ('test',)),
            ('test1.test2', ('test1', 'test2')),
            ('test[1]', ('test', 1)),
            ('test[1][2]', ('test', 1, 2)),
            ('[1][2][3][4]', (1, 2, 3, 4)),
            ('test[1].test[2].test[3][4].test', ('test', 1, 'test', 2, 'test', 3, 4, 'test')),
            (',%$^%^!@#$%', (',%$^%^!@#$%',)),
            ('],%$^%^!@#$%[1]', ('],%$^%^!@#$%', 1)),
            ('1234567', ('1234567',)),
            ('1234567[1]', ('1234567', 1)),
            ('[0]', (0,)),
            ('[5]', (5,)),
        )
        for path, expected in tests:
            with self.subTest(msg=path):
                try:
                    self.assertEqual(datapath.split(path), expected)
                except datapath.ValidationError:
                    self.fail(f'path `{path}` was found invalid')

    def test_split_join(self):
        for path in valid_paths:
            with self.subTest(msg=path):
                try:
                    self.assertEqual(datapath.join(datapath.split(path)), path)
                except datapath.ValidationError:
                    self.fail(f'path `{path}` was found invalid')

    def test_join_bad_type(self):
        with self.assertRaises(datapath.ValidationError):
            datapath.join([1.6])

    def test_validate_key_collection_type_valid(self):
        tests = (
            ({}, ''),
            ([], 0),
        )
        for i, (obj, key) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                try:
                    datapath._base._validate_key_collection_type(obj, key)
                except datapath.ValidationError:
                    self.fail(f'valid type combination was found invalid: obj {type(obj)} key {type(key)}')

    def test_validate_key_collection_type_bad_object(self):
        tests = (
            (0, 0),
            ('', ''),
            (object(), ''),
            (tuple(), 0),
        )
        for i, (obj, key) in enumerate(tests):
            with self.subTest(msg=f'index {i}'), self.assertRaises(datapath._base.TypeValidationError):
                datapath._base._validate_key_collection_type(obj, key)

    def test_validate_key_collection_bad_key(self):
        tests = (
            ({}, []),
            ([], {}),
            ([], 1.6),
        )
        for i, (obj, key) in enumerate(tests):
            with self.subTest(msg=f'index {i}'), self.assertRaises(datapath._base.TypeValidationError):
                datapath._base._validate_key_collection_type(obj, key)

    def test_validate_key_collection_type_mismatch(self):
        tests = (
            ({}, 0),
            ([], ''),
        )
        for i, (obj, key) in enumerate(tests):
            with self.subTest(msg=f'index {i}'), self.assertRaises(datapath._base.TypeMismatchValidationError):
                datapath._base._validate_key_collection_type(obj, key)

    def test_get(self):
        tests = (
            ([0], '[0]', 0),
            ([5], '[0]', 5),
            ({'a': 0}, 'a', 0),
            ({'a': [0]}, 'a[0]', 0),
            ({'a': {'b': [0, 1, 2], 'c': 5}}, 'a.b[1]', 1),
            ([[[[0, 1], [2]], [[3]]], [[[4]]]],
             '[0][0][0][0]', 0),
            ([[[[0, 1], [2]], [[3]]], [[[4]]]],
             '[1][0][0][0]', 4),
        )
        for i, (obj, path, expected) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                self.assertEqual(datapath.get(obj, path), expected)

    def test_get_default_already_set(self):
        self.assertEqual(datapath.get({'a': 1}, 'a', 42), 1)
        self.assertEqual(datapath.get([0], '[0]', 42), 0)

    def test_get_default_not_set(self):
        self.assertEqual(datapath.get({}, 'a', 42), 42)

    def test_get_root_path(self):
        test = set((4, 5, 6))
        self.assertIs(datapath.get(test, ''), test)

    def test_get_lookup_error(self):
        with self.assertRaises(LookupError):
            datapath.get({}, 'a')
        with self.assertRaises(LookupError):
            datapath.get([], '[0]')

    def test_put(self):
        tests = (
            ([0], '[0]', 42),
            ({'a': 0}, 'a', 42),
            ({'a': [0]}, 'a[0]', 42),
            ({'a': {'b': [0, 1, 2], 'c': 5}}, 'a.b[1]', 42),
            ([[[[0, 1], [2]], [[3]]], [[[4]]]],
             '[0][0][0][0]', 42),
            ([[[[0, 1], [2]], [[3]]], [[[4]]]],
             '[1][0][0][0]', 42),
            ({}, 'a', 42),
        )
        for i, (obj, path, value) in enumerate(tests):
            with self.subTest(msg=f'index {i}'):
                datapath.put(obj, path, value)
                updated_value = datapath.get(obj, path)
                self.assertEqual(value, updated_value)

    def test_put_leaf_list_lookup_error(self):
        with self.assertRaises(LookupError):
            datapath.put([], '[0]', 42)

    def test_delete_dict(self):
        test = {'a': 1}
        datapath.delete(test, 'a')
        self.assertEqual(len(test), 0)

    def test_delete_list(self):
        test = [0, 1]
        datapath.delete(test, '[0]')
        self.assertEqual(test[0], 1)
        self.assertEqual(len(test), 1)

    def test_delete_lookup_error(self):
        with self.subTest(msg='list'), self.assertRaises(LookupError):
            datapath.delete([], '[0]')
        with self.subTest(msg='dict'), self.assertRaises(LookupError):
            datapath.delete({}, 'a')

    def test_discard_deletes(self):
        try:
            test = {'a': 1}
            datapath.discard(test, 'a')
            self.assertEqual(len(test), 0)
        except LookupError:
            self.fail('discard did not suppress LookupError')

    def test_discard_noops(self):
        try:
            test = {'a': 1}
            datapath.discard(test, 'b')
            self.assertEqual(len(test), 1)
        except LookupError:
            self.fail('discard did not suppress LookupError')

    def test_iterate_valid(self):
        tests = (
            ('a[]', {'a': [1, 2, 3]}, (('a[0]', 1), ('a[1]', 2), ('a[2]', 3))),
            ('a.b[]', {'a': {'b': [1, 2, 3]}}, (('a.b[0]', 1), ('a.b[1]', 2), ('a.b[2]', 3))),
            (
                'a[].b[]',
                {'a': [
                    {'b': [1, 2, 3]},
                    {'b': [4, 5, 6]},
                ]},
                (
                    ('a[0].b[0]', 1),
                    ('a[0].b[1]', 2),
                    ('a[0].b[2]', 3),
                    ('a[1].b[0]', 4),
                    ('a[1].b[1]', 5),
                    ('a[1].b[2]', 6),
                ),
            ),
        )
        for i, (iter_path, obj, expected) in enumerate(tests):
            with self.subTest(f'index {i}'):
                self.assertEqual(tuple(datapath.iterate(obj, iter_path)), expected)
