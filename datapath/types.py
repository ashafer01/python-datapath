from typing import Any, NewType


class _IterationPoint:
    def __str__(self) -> str:
        return 'ITERATION_POINT'

    def __repr__(self) -> str:
        return 'ITERATION_POINT'


class _NoDefault:
    def __str__(self) -> str:
        return 'NO_DEFAULT'

    def __repr__(self) -> str:
        return 'NO_DEFAULT'


Key = NewType('Key', int|str)
SplitPath = NewType('SplitPath', tuple[Key|_IterationPoint, ...])
Map = NewType('Map', dict[str, Any])
Collection = NewType('Collection', list|Map)
CollectionKey = NewType('CollectionKey', tuple[list, int]|tuple[Map, str])

PartialList = NewType('PartialList', list[tuple[int, Any]])
PartialCollection = NewType('PartialCollection', PartialList|Map)
PathDict = NewType('PathDict', dict[str, Any])
RootPathDict = NewType('RootPathDict', dict[str, Collection])

NO_DEFAULT = _NoDefault()
ITERATION_POINT = _IterationPoint()


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
