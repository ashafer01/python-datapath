from typing import Any, Generator

from ._base import (
    get,
    iterate,
    put,
    delete,
    discard,
    _collection_types,
)
from .folding import fold_path_dict
from .types import (
    Key,
    Collection,
    NO_DEFAULT,
)


class collection:
    """
    wrapper for a list/dict object that calls get/iterate/put/delete/discard on it's wrapped
    object.

    also supports square bracket syntax -- if a key is a string it will always be
    treated as a path; otherwise it will be treated as a key on the wrapped object

    wrap=True causes any returned list/dict object to be wrapped in a new collection
    instance by default. collection.get() can override this behavior
    """
    def __init__(self, root_obj: Collection, wrap: bool = False):
        self.root = root_obj
        self.wrap = wrap

    def _resolve_wrap(self, wrap: bool) -> bool:
        if wrap is NO_DEFAULT:
            return self.wrap
        return wrap

    def get(self, path: str, default: Any = NO_DEFAULT, wrap: bool = NO_DEFAULT) -> Any:
        """identical to get() for the wrapped root object

        if the path refers to a Collection object and wrap or self.wrap is True,
        then the result will be wrapped in a new collection instance
        """
        wrap = self._resolve_wrap(wrap)
        result = get(self.root, path, default)
        if wrap and isinstance(result, _collection_types):
            return collection(result, wrap=wrap)
        return result

    def __getitem__(self, key: Key) -> Any:
        if isinstance(key, str):
            return self.get(key)
        if isinstance(key, int) and isinstance(self.root, list):
            return self.root[key]
        raise ValueError('unsupported key type')

    def iterate(self, path: str, default: Any = NO_DEFAULT, wrap: bool = NO_DEFAULT) -> Generator[tuple[str, Any], None, None]:
        """identical to iterate() for the wrapped root object

        if the iteration yields a Collection object and wrap or self.wrap is True,
        then the yielded result will be wrapped in a new collection instance
        """
        wrap = self._resolve_wrap(wrap)
        for item_path, item in iterate(self.root, path, default):
            if wrap and isinstance(item, _collection_types):
                yield item_path, collection(item, wrap=wrap)

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

    def fold(self) -> dict:
        """convert the collection to a flat path dict using `fold_path_dict()`"""
        return fold_path_dict(self.root)
