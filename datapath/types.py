import sys
from typing import Any, NewType, Generator

import regex as re

Key = NewType('Key', int|str)
Map = NewType('Map', dict[str, Any])
Collection = NewType('Collection', list|Map)
CollectionKey = NewType('CollectionKey', tuple[list, int]|tuple[Map, str])

PartialList = NewType('PartialList', list[tuple[int, Any]])
PartialCollection = NewType('PartialCollection', PartialList|Map)
PathDict = NewType('PathDict', dict[str, Any])
RootPathDict = NewType('RootPathDict', dict[str, Collection])


class _IterationPoint:
    name: str = '<none>'

    def __init__(self, path_part: str):
        self.path_part = path_part

    def __str__(self) -> str:
        return repr(self.path_part)

    def check(self, collection: Collection) -> None:
        raise NotImplementedError()

    def iter(self, collection: Collection) -> Generator[tuple[Key, Any], None, None]:
        raise NotImplementedError()

    def append_path(self, base_path: str) -> str:
        raise NotImplementedError()


class _StarIterationPoint(_IterationPoint):
    name: str = '*-key'

    def __init__(self, path_part: str):
        _IterationPoint.__init__(self, path_part)
        if path_part == '*':
            self._re = None
        else:
            substrings = map(re.escape, path_part.split('*'))
            self._re = re.compile('^' + '.*?'.join(substrings) + '$')

    def check(self, collection: Collection) -> None:
        if not isinstance(collection, dict):
            raise InvalidIterationError('*-keys must be preceeded by a dict')

    def _match(self, key: str) -> bool:
        if self._re:
            return bool(self._re.match(key))
        else:
            return True

    def iter(self, collection: Collection) -> Generator[tuple[Key, Any], None, None]:
        for key, value in collection.items():
            if not self._match(key):
                continue
            yield key, value

    def append_path(self, base_path: str) -> str:
        if base_path:
            return f'{base_path}.{self.path_part}'
        else:
            return self.path_part


class _BaseListIterationPoint(_IterationPoint):
    def check(self, collection: Collection) -> None:
        if not isinstance(collection, list):
            raise InvalidIterationError('[] must be preceeded by a list')

    def append_path(self, base_path: str) -> str:
        if base_path:
            return f'{base_path}{self.path_part}'
        else:
            return self.path_part


class _ListIterationPoint(_BaseListIterationPoint):
    name: str = 'empty square brackets'

    def iter(self, collection: Collection) -> Generator[tuple[Key, Any], None, None]:
        yield from enumerate(collection)


class _RangeIterationPoint(_BaseListIterationPoint):
    name: str = 'slice syntax'

    def __init__(self, path_part: str):
        _IterationPoint.__init__(self, path_part)
        self._range = self._parse_slice(path_part)

    @staticmethod
    def _parse_slice(path_part: str) -> range:
        parts = path_part.strip('[]').split(':')
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

    def iter(self, collection: Collection) -> Generator[tuple[Key, Any], None, None]:
        for index in self._range:
            try:
                yield index, collection[index]
            except IndexError:
                break


SplitPath = NewType('SplitPath', tuple[Key|_IterationPoint, ...])


class _NoDefault:
    def __repr__(self) -> str:
        return 'NO_DEFAULT'


NO_DEFAULT = _NoDefault()


class DatapathError(Exception):
    """base datapath error"""


class ValidationError(DatapathError):
    """generic issue validating arguments"""


class TypeValidationError(ValidationError):
    """a type was not valid"""


class TypeMismatchValidationError(ValidationError):
    """two codependent types did not match"""


class InvalidIterationError(ValidationError):
    """disallowed or unsupported use of iteration (empty square brackets in a path)"""


class PathLookupError(DatapathError, LookupError):
    """raised when an intermediate collection in a path is not found"""
