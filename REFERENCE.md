# datapath Reference

## Types

```
Key = int | str
SplitPath = tuple[Union[datapath.types.Key, datapath.types._IterationPoint], ...]
Map = dict[str, Any]
Collection = Union[list, datapath.types.Map]
CollectionKey = tuple[list, int] | tuple[datapath.types.Map, str]
PartialList = list[tuple[int, Any]]
PartialCollection = Union[datapath.types.PartialList, datapath.types.Map]
PathDict = dict[str, Any]
RootPathDict = dict[str, datapath.types.Collection]
```

## Public API

The API semantics are optimized for use with `import datapath`, without any `from` clause

### function `get()`

```
get(obj: datapath.types.Collection, path: str, default: Any = NO_DEFAULT) -> Any
```

obtain the value at the path

* if any non-leaf path parts are not found, a PathLookupError will always be raised
* if default is passed, return it if the leaf value was not found
* if default is not passed and the leaf value is not found, propagate the LookupError



### function `iterate()`

```
iterate(obj: datapath.types.Collection, path: str, default: Any = NO_DEFAULT) -> Generator[tuple[str, Any], NoneType, NoneType]
```

yield entries from a collection using an iterable path -- that is, one containing one or more
sets of empty square brackets (`[]`) or a key with a `*` (`*`/`wild*cards*`/etc.)

* the path part just before an iteration point must refer to a list for `[]` and a dict
  for `*`-keys
* each yielded value is a tuple (path, value); paths will be resolved with specific indexes
  placed into all empty square brackets and specific keys replacing `*`-keys
* `default` passes through to leaf `get()` calls
* raises `PathLookupError` if a collection before an iteration point is not found, or an
  intermediate element leading to a collection is not found

Examples:

* `test1.test2[3]`  # no empty square brackets, yields one result, equivalent to get()
* `test1[]`         # "test1" in a root dict must be a list, each entry will be yielded
* `test1[].test2`   # "test1" in a root dict must be a list, key "test2" from each dict entry will be yielded
* `test1[].test2[]` # recursion works
* `[][0]`           # works without dicts
* `test1.*`         # "test1" in a root dict must be a dict, yield each key
* `test1.test*`     # "test1" in a root dict must be a dict, yield each key that starts with "test"
* `test1.*test*`    # "test1" in a root dict must be a dict, yield each key that contains "test"
* `test1[].*`       # combining dict and list iteration works



### function `put()`

```
put(obj: datapath.types.Collection, path: str, value: Any) -> None
```

set the value at the path

* mutates the leaf collection object
* if any non-leaf path parts are not found, a LookupError will always be
  propagated to the caller
* for leaf lists, this will propagate an IndexError if the index was not already set
* for leaf dicts, this should always succeed



### function `delete()`

```
delete(obj: datapath.types.Collection, path: str) -> None
```

delete the value at the path

* mutates the leaf collection object
* if any non-leaf path parts are not found, a LookupError will always be
  propagated to the caller
* always propagates a LookupError if the key/index was not already set



### function `discard()`

```
discard(obj: datapath.types.Collection, path: str) -> None
```

ensure the path does not exist

* mutates the leaf collection object
* if any non-leaf path parts are not found, a LookupError will always be
  propagated to the caller
* if the leaf exists, it will be deleted
* if the leaf does not exist, do nothing



### function `is_path()`

```
is_path(path: str) -> bool
```

validate the path string and return a bool, True if it's valid


### function `validate_path()`

```
validate_path(path: str) -> None
```

validate the path string and raise a ValidationError if it's invalid


### function `split()`

```
split(path: str, iterable: bool = False) -> datapath.types.SplitPath
```

inverse of join() -- split the path string to it's component keys/indexes in order


### function `join()`

```
join(split_path: Iterable[datapath.types.Key]) -> str
```

inverse of split() -- combine an iterable of keys/indexes into a dotted-path format

Example:

```
>>> join(['a', 'b', 5])
'a.b[5]'
```



### function `leaf()`

```
leaf(obj: datapath.types.Collection, path: str) -> datapath.types.CollectionKey
```

find the collection object and key/index at the right side of the path


### function `unfold_path_dict()`

```
unfold_path_dict(paths: datapath.types.PathDict, processor: datapath.folding.UnfoldProcessor = <DefaultUnfoldProcessor>, root_path: bool = True, complete_root: bool = True, complete_intermediates: bool = True) -> Union[datapath.types.RootPathDict, datapath.types.Collection]
```

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
    'key1[0]: 17,    # this wants root field 'key1' to be a list, but it's a dict already
                     #   this is *invalid*
  }
  ```

* reminder that dict iteration ordering is not determinate; therefore, for inconsistent
  type ValidationErrors, the types reported in the error may differ from one run to the next
  on the same data set



### function `fold_path_dict()`

```
fold_path_dict(root: datapath.types.Collection, root_path: str = '') -> datapath.types.PathDict
```

* inverse of `unfold_path_dict()`
* accept a Collection to treat as the root, and optional root path string to prepend
* return a folded path dict, where each key is a dotted path to a leaf value, and values are
  the leaf values themselves.



### class `collection`

```
collection(root_obj: datapath.types.Collection, wrap: bool = False)
```

wrapper for a list/dict object that calls get/iterate/put/delete/discard on it's wrapped
object.

also supports square bracket syntax -- if a key is a string it will always be
treated as a path; otherwise it will be treated as a key on the wrapped object

wrap=True causes any returned list/dict object to be wrapped in a new collection
instance by default. collection.get() can override this behavior


#### method `collection.get()`
```
collection.get(root_obj: datapath.types.Collection, wrap: bool = False)
```

identical to get() for the wrapped root object

if the path refers to a Collection object and wrap or self.wrap is True,
then the result will be wrapped in a new collection instance


#### method `collection.iterate()`
```
collection.iterate(root_obj: datapath.types.Collection, wrap: bool = False)
```

identical to iterate() for the wrapped root object

if the iteration yields a Collection object and wrap or self.wrap is True,
then the yielded result will be wrapped in a new collection instance


#### method `collection.put()`
```
collection.put(root_obj: datapath.types.Collection, wrap: bool = False)
```

identical to put() for the wrapped root object

#### method `collection.delete()`
```
collection.delete(root_obj: datapath.types.Collection, wrap: bool = False)
```

identical to delete() for the wrapped root object

#### method `collection.discard()`
```
collection.discard(root_obj: datapath.types.Collection, wrap: bool = False)
```

identical to discard() for the wrapped root object

#### method `collection.fold()`
```
collection.fold(root_obj: datapath.types.Collection, wrap: bool = False)
```

convert the collection to a flat path dict using `fold_path_dict()`


### class `UnfoldProcessor`

```
UnfoldProcessor()
```

Base class used to enable custom processing of the data structure during unfold operations

#### method `UnfoldProcessor.process_list()`
```
UnfoldProcessor.process_list()
```

called on a completed list; return value is inserted into the resulting data structure
instead of the original list


#### method `UnfoldProcessor.process_dict()`
```
UnfoldProcessor.process_dict()
```

called on a completed dict; return value is inserted into the resulting data structure
instead of the original dict



### exception `DatapathError`

base datapath error


### exception `ValidationError`

generic issue validating arguments


### exception `InvalidIterationError`

disallowed or unsupported use of iteration (empty square brackets in a path)


### exception `PathLookupError`

raised when an intermediate collection in a path is not found


