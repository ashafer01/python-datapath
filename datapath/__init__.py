"""
datapath -- implement dotted.and.indexed[0].paths for recursive list/dict structures

* dict keys can be any string excluding "[" and "." characters
* inside "[" and "]" must be an integer list index

"""
from typing import Any, Iterable, TypeGuard, cast

import regex as re

_key_pattern = '(?P<part>[^[.]+)'
_index_pattern = r'(?P<part>\[[0-9]+\])'
_key_with_index_pattern = _key_pattern + _index_pattern + '?'
_part_pattern = _key_with_index_pattern + '|' + _index_pattern
_path_re = re.compile('^(?:' + _part_pattern + r')(?:\.' + _part_pattern + ')*$')

Key = int|str
SplitPath = tuple[Key, ...]
Collection = list|dict[str, Any]

_key_types = (int, str)
_collection_types = (list, dict)

NO_DEFAULT = object()


class DatapathError(Exception):
    """base datapath error"""


class ValidationError(DatapathError):
    """generic issue validating arguments"""


class TypeValidationError(ValidationError):
    """a type was not valid"""


class TypeMismatchValidationError(ValidationError):
    """two codependent types did not match"""
    def __init__(self, message: str):
        ValidationError.__init__(self, f'key and collection type mismatch; {message}')


def is_path(path: str) -> bool:
    """validate the path string and return a bool, True if it's valid"""
    return bool(_path_re.match(path))


def validate_path(path: str) -> None:
    """validate the path string and raise a ValidationError if it's invalid"""
    if not is_path(path):
        raise ValidationError('invalid path string')


def split(path: str) -> SplitPath:
    """split the path string to it's component keys/indexes in order"""
    if not path:
        return ()
    split_path: list[Key] = []
    match = _path_re.match(path)
    if not match:
        raise ValidationError('invalid path string')
    for part in match.captures('part'):
        if part[0] == '[' and part[-1] == ']':
            split_path.append(int(part[1:-1]))
        else:
            split_path.append(part)
    return tuple(split_path)


def join(split_path: Iterable[Key]) -> str:
    """inverse of split()
    combine an iterable of keys/indexes into a dotted-path format
    Example:
    ```
    >>> join(['a', 'b', 5])
    'a.b[5]'
    ```
    """
    path = ''
    for i, part in enumerate(split_path):
        if isinstance(part, str):
            if path:
                path = f'{path}.{part}'
            else:
                path = part
        elif isinstance(part, int):
            if path:
                path = f'{path}[{part}]'
            else:
                path = f'[{part}]'
        else:
            raise ValidationError(f'index {i} is invalid, must be str/int, '
                                  f'got {type(part).__name__}')
    return path


def _validate_key_collection_type(obj: Collection, key: Key) -> None:
    """validate a collection object and key are valid and corresponding types
    raise a ValidationError if they are not
    """
    if not isinstance(obj, _collection_types):
        raise TypeValidationError('object must be list/dict')
    if not isinstance(key, _key_types):
        raise TypeValidationError('path parts must all be str or int')
    if isinstance(key, int) and not isinstance(obj, list):
        raise TypeMismatchValidationError(f'int key requires list, got {type(obj).__name__}')
    if isinstance(key, str) and not isinstance(obj, dict):
        raise TypeMismatchValidationError(f'str key requires dict, got {type(obj).__name__}')


def _contextual_validate_key_collection_type(at_path: list[Key],
                                             obj: Collection,
                                             key: Key) -> None:
    """
    validate_key_collection_type(), except the path where the error occurred is prepended
    to the exception message
    mutates at_path to track the current path
    """
    at_path.append(key)
    try:
        _validate_key_collection_type(obj, key)
    except ValidationError as e:
        raise ValidationError(f'{join(at_path)}: {e}') from None


CollectionKey = tuple[list, int]|tuple[dict[str, Any], str]


def leaf(obj: Collection, path: str) -> CollectionKey:
    """find the collection object and key/index at the right side of the path"""
    split_path = split(path)
    at_path: list[Key] = []
    for key in split_path[:-1]:
        _contextual_validate_key_collection_type(at_path, obj, key)
        obj = obj[key]
    leaf_key = split_path[-1]
    _contextual_validate_key_collection_type(at_path, obj, leaf_key)
    return cast(CollectionKey, (obj, leaf_key))


def get(obj: Collection, path: str, default: Any = NO_DEFAULT) -> Any:
    """obtain the value at the path

    * if any non-leaf path parts are not found, a LookupError will always be
      propagated to the caller
    * if default is passed, return it if the leaf value was not found
    * if default is not passed and the leaf value is not found, propagate
      the LookupError
    """
    leaf_obj, leaf_key = leaf(obj, path)
    try:
        return leaf_obj[leaf_key]
    except LookupError:
        if default is NO_DEFAULT:
            raise
        return default


def put(obj: Collection, path: str, value: Any) -> None:
    """set the value at the path

    * mutates the leaf collection object
    * if any non-leaf path parts are not found, a LookupError will always be
      propagated to the caller
    * for leaf lists, this will propagate an IndexError if the index was not already set
    * for leaf dicts, this should always succeed
    """
    leaf_obj, leaf_key = leaf(obj, path)
    leaf_obj[leaf_key] = value


def delete(obj: Collection, path: str) -> None:
    """delete the value at the path

    * mutates the leaf collection object
    * if any non-leaf path parts are not found, a LookupError will always be
      propagated to the caller
    * always propagates a LookupError if the key/index was not already set
    """
    obj, leaf_key = leaf(obj, path)
    del obj[leaf_key]


def discard(obj: Collection, path: str) -> None:
    """ensure the path does not exist

    * mutates the leaf collection object
    * if any non-leaf path parts are not found, a LookupError will always be
      propagated to the caller
    * if the leaf exists, it will be deleted
    * if the leaf does not exist, do nothing
    """
    obj, leaf_key = leaf(obj, path)
    try:
        del obj[leaf_key]
    except LookupError:
        pass


class collection:
    """
    wrapper for a list/dict object that calls get/put/delete/discard on it's wrapped
    object.

    also supports square bracket syntax -- if a key is a string it will always be
    treated as a path; otherwise it will be treated as a key on the wrapped object

    wrap=True causes any returned list/dict object to be wrapped in a new collection
    instance by default. collection.get() can override this behavior
    """
    def __init__(self, root_obj: Collection, wrap: bool = False):
        self.root = root_obj
        self.wrap = wrap

    def get(self, path: str, default: Any = NO_DEFAULT, wrap: bool = False) -> Any:
        """identical to get() for the wrapped root object

        if the path refers to a Collection object and wrap or self.wrap is True,
        then the result will be wrapped in a new collection instance
        """
        wrap = (wrap or self.wrap)
        result = get(self.root, path, default)
        if wrap and isinstance(result, _collection_types):
            return collection(result, wrap=wrap)
        return result

    def __getitem__(self, key: Key) -> Any:
        if isinstance(key, str):
            return self.get(key)
        if isinstance(key, int) and isinstance(self.root, list):
            return self.root[key]
        raise TypeError('unsupported key type')

    def put(self, path: str, value: Any) -> None:
        """identical to put() for the wrapped root object"""
        put(self.root, path, value)

    def __setitem__(self, key: Key, value: Any) -> None:
        if isinstance(key, str):
            self.put(key, value)
        elif isinstance(key, int) and isinstance(self.root, list):
            self.root[key] = value
        raise TypeError('unsupported key type')

    def delete(self, path: str) -> None:
        """identical to delete() for the wrapped root object"""
        delete(self.root, path)

    def __delitem__(self, key: Key) -> None:
        if isinstance(key, str):
            self.delete(key)
        elif isinstance(key, int) and isinstance(self.root, list):
            del self.root[key]
        raise TypeError('unsupported key type')

    def discard(self, path: str) -> None:
        """identical to discard() for the wrapped root object"""
        discard(self.root, path)
