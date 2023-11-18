from typing import Any

Key = int|str
SplitPath = tuple[Key, ...]
Map = dict[str, Any]
Collection = list|Map
CollectionKey = tuple[list, int]|tuple[Map, str]

PartialList = list[tuple[int, Any]]
PartialCollection = PartialList|Map
PathDict = dict[str, Any]
RootPathDict = dict[str, Collection]

NO_DEFAULT = object()
