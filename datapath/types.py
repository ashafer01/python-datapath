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
