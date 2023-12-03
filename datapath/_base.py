"""
datapath -- implement dotted.and.indexed[0].paths for recursive list/dict structures
"""
import functools
import sys
from typing import Any, Generator, Iterable

import regex as re

from .types import (
    Key,
    SplitPath,
    Collection,
    CollectionKey,
    NO_DEFAULT,
    ITERATION_POINT,
    DatapathError,
    ValidationError,
    TypeValidationError,
    TypeMismatchValidationError,
    InvalidIterationError,
    PathLookupError,
)

_key_pattern = '(?P<part>[^[.]+)'
_number_pattern = r'-?[0-9]'
_range_parts_pattern = '(?::' + _number_pattern + '*){0,2}'
_index_pattern = r'(?P<part>\[' + _number_pattern + r'*' + _range_parts_pattern + r'\])'
_key_with_index_pattern = _key_pattern + _index_pattern + '?'
_part_pattern = _key_with_index_pattern + '|' + _index_pattern
_path_re = re.compile('^(?:' + _part_pattern + r')(?:\.' + _part_pattern + ')*$')

_key_types = (int, str)
_collection_types = (list, dict)


def _match_validate(path: str) -> re.Match:
    match = _path_re.match(path)
    if not match:
        raise ValidationError('invalid path string')
    return match


def is_path(path: str, iterable: bool = True) -> bool:
    """validate the path string and return a bool, True if it's valid

    * all public methods that accept path strings validate them first
    * set `iterable=False` if you do not want interable paths to be considered valid
    """
    if path == '':
        return True
    match = _path_re.match(path)
    if iterable:
        return bool(match)
    else:
        try:
            _split_match(match, iterable=False)
            return True
        except ValidationError:
            return False


def validate_path(path: str, iterable: bool = True) -> None:
    """validate the path string and raise a ValidationError if it's invalid

    * all public methods that accept path strings validate them first
    * set `iterable=False` if you do not want interable paths to be considered valid
    """
    if path == '':
        return
    match = _match_validate(path)
    if not iterable:
        _split_match(match, iterable=False)


def _parse_range(range_part: str) -> range:
    parts = range_part.split(':')
    num_parts = len(parts)
    if num_parts == 2:
        start, stop = parts
        step = ''
    elif num_parts == 3:
        start, stop, step = parts
    else:
        raise ValueError(f'bug: unhandled number of delimiters ({num_parts-1}) in range syntax')
    if start:
        start = int(start)
    else:
        start = 0
    if stop:
        stop = int(stop)
    else:
        stop = sys.maxsize
    if step:
        step = int(step)
    else:
        step = 1
    return range(start, stop, step)



def split(path: str, iterable: bool = False) -> SplitPath:
    """inverse of join() -- split the path string to it's component keys/indexes in order"""
    if path == '':
        return ()
    match = _match_validate(path)
    return _split_match(match, iterable)


def _split_match(match: re.Match, iterable: bool) -> SplitPath:
    split_path: list[Key] = []
    for part in match.captures('part'):
        if part[0] == '[' and part[-1] == ']':
            index = part[1:-1]
            if ':' in index:
                if not iterable:
                    raise InvalidIterationError('iterable range syntax is not allowed here')
                split_path.append(_parse_range(index))
            elif index:
                split_path.append(int(index))
            elif iterable:
                split_path.append(ITERATION_POINT)
            else:
                raise InvalidIterationError('iterable empty square brackets is not allowed here')
        elif '*' in part:
            if iterable:
                split_path.append(part)
            else:
                raise InvalidIterationError('iterable *-key is not allowed here')
        else:
            split_path.append(part)
    return tuple(split_path)


def join(split_path: Iterable[Key]) -> str:
    """inverse of split() -- combine an iterable of keys/indexes into a dotted-path format

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
        elif part is ITERATION_POINT:
            if path:
                path = f'{path}[]'
            else:
                path = '[]'
        else:
            raise ValidationError(f'index {i} is invalid, must be str/int, '
                                  f'got {type(part).__name__}')
    return path


def _validate_key_collection_type(obj: Collection, key: Key) -> None:
    """
    validate a collection object and key are valid and corresponding types
    raise a ValidationError if they are not
    """
    if key is ITERATION_POINT:
        raise TypeError('bug: iteration not supported here')
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
    """
    at_path.append(key)
    try:
        _validate_key_collection_type(obj, key)
    except ValidationError as e:
        raise type(e)(f'{join(at_path)}: {e}') from None


def leaf(obj: Collection, path: str) -> CollectionKey:
    """find the collection object and key/index at the right side of the path"""
    return _leaf(obj, split(path))


def _leaf(obj: Collection, split_path: SplitPath) -> CollectionKey:
    """leaf() on an already-split path"""
    at_path: list[Key] = []
    for key in split_path[:-1]:
        _contextual_validate_key_collection_type(at_path, obj, key)
        try:
            obj = obj[key]
        except LookupError:
            raise PathLookupError(f'{join(at_path[:-1])}: could not find key/index {key!r}') from None
    leaf_key = split_path[-1]
    _contextual_validate_key_collection_type(at_path, obj, leaf_key)
    return obj, leaf_key


def get(obj: Collection, path: str, default: Any = NO_DEFAULT) -> Any:
    """obtain the value at the path

    * if any non-leaf path parts are not found, a PathLookupError will always be raised
    * if default is passed, return it if the leaf value was not found
    * if default is not passed and the leaf value is not found, propagate the LookupError
    """
    return _get(obj, split(path), default)


def _get(obj: Collection, split_path: str, default: Any = NO_DEFAULT) -> Any:
    """get() on an already-split path"""
    if not split_path:
        return obj
    leaf_obj, leaf_key = _leaf(obj, split_path)
    try:
        return leaf_obj[leaf_key]
    except LookupError as e:
        if default is NO_DEFAULT:
            raise e from None
        return default


def iterate(obj: Collection,
            path: str,
            default: Any = NO_DEFAULT) -> Generator[tuple[str, Any], None, None]:
    """
    yield entries from a collection using an iterable path -- that is, one containing one or more
    sets of empty square brackets (`[]`) or a key with a `*` (`*`/`wild*cards*`/etc.)

    * the path part just before an iteration point must refer to a list for `[]` and a dict
      for `*`-keys
    * each yielded value is a tuple (path, value); paths will be resolved with specific indexes
      placed into all empty square brackets / ranges, and specific keys replacing `*`-keys
    * `default` passes through to leaf `get()` calls
    * raises `PathLookupError` if a collection before an iteration point is not found, or an
      intermediate element leading to a collection is not found

    Examples:

    * `test1.test2[3]`  # no empty square brackets, yields one result, equivalent to get()
    * `test1[]`         # "test1" in a root dict must be a list, each entry will be yielded
    * `test1[].test2`   # "test1" in a root dict must be a list, key "test2" from each dict entry will be yielded
    * `test1[].test2[]` # recursion works
    * `[][0]`           # works without dicts
    * `test[1:10:2]     # python slicing is supported
    * `test1.*`         # "test1" in a root dict must be a dict, yield each key
    * `test1.test*`     # "test1" in a root dict must be a dict, yield each key that starts with "test"
    * `test1.*test*`    # "test1" in a root dict must be a dict, yield each key that contains "test"
    * `test1[].*`       # combining dict and list iteration works
    """
    split_path = split(path, iterable=True)
    yield from _iterate(obj, split_path, (), default)


def _iterate(obj: Collection,
             split_path: SplitPath,
             base_path: SplitPath,
             default: Any) -> Generator[tuple[str, Any], None, None]:
    """recursive core of iterate()"""
    if not isinstance(obj, _collection_types):
        raise ValidationError(f'{join(base_path + split_path)}: must be list/dict')

    star_index = _star_part_index(split_path)
    range_index = _range_part_index(split_path)
    try:
        iter_index = split_path.index(ITERATION_POINT)
    except ValueError:
        iter_index = sys.maxsize

    min_iter_point = min((iter_index, star_index, range_index))

    if min_iter_point == sys.maxsize:
        # no iteration points found, just need to get()
        yield join(base_path + split_path), _get(obj, split_path, default)
        return
    elif min_iter_point == star_index:
        # first iteration point is a *-key, we need a dict and need to filter for wildcard matches
        iter_index = star_index
        check = _check_dict_iter
        def iter_collection(collection):
            for key, value in collection.items():
                if not _wildcard_match(split_path[star_index], key):
                    continue
                yield key, value
    elif min_iter_point == range_index:
        # first iteration point is a [x:y:z] range, we need a list and the original indicies
        iter_index = range_index
        check = _check_list_iter
        def iter_collection(collection):
            for index in split_path[range_index]:
                try:
                    yield index, collection[index]
                except IndexError:
                    break
    elif min_iter_point == iter_index:
        # first iteration point is a [] list iterator, just need to enumerate a list
        check = _check_list_iter
        iter_collection = enumerate
    else:
        raise RuntimeError('bug: unhandled min iter point')

    # find the collection referred to by the portion of the path before the first iteration point
    before_split_path = split_path[:iter_index]
    try:
        collection = _get(obj, before_split_path)
    except PathLookupError:
        raise
    except LookupError:
        path = join(base_path + before_split_path[:-1])
        if not path:
            path = '<root>'
        key = before_split_path[-1]
        raise PathLookupError(f'{path}: could not find collection at key/index {key!r} to iterate') from None
    check(collection)
    after_split_path = split_path[iter_index+1:]

    # iterate the collection
    for key, element in iter_collection(collection):
        key_split_path = base_path + before_split_path + (key,)
        if after_split_path:
            # if there is a path after the iteration point, element must be a Collection
            yield from _iterate(element, after_split_path, key_split_path, default)
        else:
            # if there is no path after, then this element is what we're after
            yield join(key_split_path), element


def _star_part_index(split_path: SplitPath) -> int:
    for index, part in enumerate(split_path):
        if isinstance(part, str) and '*' in part:
            return index
    return sys.maxsize


def _range_part_index(split_path: SplitPath) -> int:
    for index, part in enumerate(split_path):
        if isinstance(part, range):
            return index
    return sys.maxsize


def _wildcard_match(star_part: str, key: str) -> bool:
    if star_part == '*':
        return True
    substrings = map(re.escape, star_part.split('*'))
    pattern = '^' + '.*?'.join(substrings) + '$'
    return bool(re.match(pattern, key))


def _check_dict_iter(collection: Collection):
    if not isinstance(collection, dict):
        raise InvalidIterationError('*-keys must be preceeded by a dict')


def _check_list_iter(collection: Collection):
    if not isinstance(collection, list):
        raise InvalidIterationError('[] must be preceeded by a list')


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
