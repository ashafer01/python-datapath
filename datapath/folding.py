from typing import Any

from ._base import (
    split,
    join,
    _collection_types,
)
from .types import (
    Collection,
    Key,
    Map,
    PartialCollection,
    PartialList,
    PathDict,
    RootPathDict,
    ValidationError,
    _IndexPart,
    _KeyPart,
    InvalidIterationError,
)


class UnfoldProcessor:
    """Base class used to enable custom processing of the data structure during unfold operations"""

    def process_list(self, list_: list) -> Any:
        """
        called on a completed list; return value is inserted into the resulting data structure
        instead of the original list
        """
        return list_

    def process_dict(self, dict_: Map) -> Any:
        """
        called on a completed dict; return value is inserted into the resulting data structure
        instead of the original dict
        """
        return dict_


class _DefaultUnfoldProcessor(UnfoldProcessor):
    def __repr__(self) -> str:
        return '<DefaultUnfoldProcessor>'


_default_processor = _DefaultUnfoldProcessor()


def unfold_path_dict(paths: PathDict,
                     processor: UnfoldProcessor = _default_processor,
                     root_path: bool = True,
                     complete_root: bool = True,
                     complete_intermediates: bool = True) -> RootPathDict|Collection:
    """
    * inverse of `fold_path_dict()`
    * accepts a flat dictionary where keys are dotted paths, and values are the leaf values for a
      data structure
    * returns a dictionary with only one key, "" (the empty string, meaning the root path), which
      has the root recurisve Collection as it's value
    * if `root_path` is set to False, return the root collection rather than the root path dict
    * if `complete_root` is set to False, the working root collection will not have any processing done
      before returning; this is useful if a root is being assembled from multiple sources.
      `complete_collection(root, processor)` can be called to take this action separately
    * if `complete_intermediates` is set to False, the intermediate collections will also be left
      unprocessed
    * all paths must have consistent types for the same intermediate Collections, example:

      ```
      {
        'key1.key2': 5,  # this makes root field 'key1' a dict, with initial value {'key2': 5}
        'key1[0]': 17,   # this wants root field 'key1' to be a list, but it's a dict already
                         #   this is *invalid*
      }
      ```

    * reminder that dict iteration ordering is not determinate; therefore, for inconsistent
      type ValidationErrors, the types reported in the error may differ from one run to the next
      on the same data set
    """
    if not paths:
        raise ValidationError('paths cannot be empty')
    if not isinstance(paths.get('', []), _collection_types):
        raise ValidationError('existing root path must be list/dict')
    path_dict = paths.copy()
    path_length = max([len(split(path)) for path in paths])
    root_keys_tuple = ('',)
    safety_limit = 1000000
    while tuple(path_dict.keys()) != root_keys_tuple:
        if safety_limit == 0:
            raise RuntimeError('hit loop safety limit')
        safety_limit -= 1
        did_any = False
        for path in tuple(path_dict.keys()):
            split_path = split(path)
            if len(split_path) != path_length:
                continue
            did_any = True
            parent = join(split_path[:-1])
            path_part = split_path[-1]
            if isinstance(path_part, _IndexPart):
                default_collection: PartialList = []
            elif isinstance(path_part, _KeyPart):
                default_collection: Map = {}
            elif path_part.iterable:
                raise InvalidIterationError('iteration not supported here')
            else:
                raise TypeError('bug: unsupported path part type')
            collection: PartialCollection = path_dict.setdefault(parent, default_collection)
            value = path_dict.pop(path)
            if isinstance(default_collection, list) and isinstance(collection, list):
                collection.append((path_part.key, value))
            elif isinstance(default_collection, dict) and isinstance(collection, dict):
                collection[path_part.key] = value
            else:
                raise ValidationError(f'unsupported/inconsistent types: parent {parent!r} '
                                      f'has type {type(collection).__name__} for key/index {path_part.key!r}')
        if not did_any:
            path_length -= 1
            if complete_intermediates:
                for path, value in path_dict.items():
                    if len(split(path)) != path_length:
                        continue
                    path_dict[path] = complete_collection(value, processor, require_collection=False)
    if complete_root:
        try:
            path_dict[''] = complete_collection(path_dict[''], processor)
        except ValidationError:
            raise TypeError('bug: generated an invalid root collection type')
    if root_path:
        return path_dict
    else:
        return path_dict['']


def complete_collection(collection: Any,
                        processor: UnfoldProcessor = _default_processor,
                        require_collection: bool = True) -> Any:
    """
    perform final post-processing steps on a completed collection.

    * if require_collection is set to False and `collection` is not a Collection, return the
      original value unmodified
    * raises a ValidationError for non-collections by default
    """
    if isinstance(collection, list):
        return processor.process_list(_complete_partial_list(collection))
    elif isinstance(collection, dict):
        return processor.process_dict(collection)
    elif require_collection:
        raise ValidationError('must be list/dict')
    else:
        return collection


def _complete_partial_list(partial_list: PartialList) -> list:
    """
    * validate that an n, n+1, ... sequence of list indexes were found starting with 0
    * return a completed list with only the values sorted properly

    this enables discovering the list indexes out of order in a path dict
    """
    partial_list.sort()
    complete_list = []
    last_index = -1
    for index, value in partial_list:
        if index != last_index + 1:
            raise ValidationError(f'did not find index {last_index + 1}')
        last_index = index
        complete_list.append(value)
    return complete_list


def fold_path_dict(root: Collection, root_path: str = '') -> PathDict:
    """
    * inverse of `unfold_path_dict()`
    * accept a Collection to treat as the root, and optional root path string to prepend
    * return a folded path dict, where each key is a dotted path to a leaf value, and values are
      the leaf values themselves.
    """
    path_dict: PathDict = {}
    at_path = list(split(root_path))
    _fold_path_dict(path_dict, at_path, root)
    return path_dict


def _fold_path_dict(path_dict: PathDict, at_path: list[Key], element: Any) -> None:
    """
    recursive core of `fold_path_dict()`, mutates `path_dict` with results
    """
    if isinstance(element, list):
        iter_element = enumerate(element)
    elif isinstance(element, dict):
        iter_element = element.items()
    elif at_path:
        path_dict[join(at_path)] = element
        return
    else:
        raise ValidationError('root must be list/dict')
    for key, value in iter_element:
        path = [*at_path, key]
        _fold_path_dict(path_dict, path, value)
