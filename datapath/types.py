from typing import Any


class _IterationPoint:
    def __str__(self) -> str:
        return 'ITERATION_POINT'

    def __repr__(self) -> str:
        return 'ITERATION_POINT'

Key = int|str
SplitPath = tuple[Key|_IterationPoint, ...]
Map = dict[str, Any]
Collection = list|Map
CollectionKey = tuple[list, int]|tuple[Map, str]

PartialList = list[tuple[int, Any]]
PartialCollection = PartialList|Map
PathDict = dict[str, Any]
RootPathDict = dict[str, Collection]

NO_DEFAULT = object()
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
