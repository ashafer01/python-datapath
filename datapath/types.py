from typing import Any

Key = int|str
SplitPath = tuple[Key, ...]
Collection = list|dict[str, Any]
CollectionKey = tuple[list, int]|tuple[dict[str, Any], str]

PartialList = list[tuple[int, Any]]
PathDict = dict[str, Any]
RootPathDict = dict[str, Collection]

NO_DEFAULT = object()
