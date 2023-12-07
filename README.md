# python-datapath

A python package for working with dotted and square-bracketed paths on a recursive data structure made of dicts and
lists, such as are returned by most JSON and YAML decoders, and other common data interchange formats.

_In development_: public API is not stable, support available solely at developer discretion

* [Public API Reference Document](REFERENCE.md)
* Requires Python 3.10+
* Example paths that refer to a single value:
  * `hello`
  * `hello.world`
  * `hello.world[0]`
  * `hello.world[0].name`
* Example iterable paths:
  * `hello.world[].name`
  * `hello.world[1:10:2].name`
  * `objects[].attributes.*` - iterates all values in each `"attributes"` dict
  * `objects[].attributes.*hello*` - same, but the key must contain the substring `hello`
* Dictionary keys may be any string excluding the characters `*`, `[`, and `.`
* List indicies within square brackets must parse to an integer
* For iteration:
  * Dictionary keys may contain `*` to iterate over all keys in the preceeding dictionary; iterating all keys
    matching a wildcard pattern is also supported
  * Square brackets may be empty to iterate over all items in the preceeding list
  * The Python range syntax `[x:y:z]` is fully supported
  * An `InvalidIterationError` will be raised if these iterable path parts are passed to functions other than
    `iterate()`.
* A `ValidationError` will be raised if the data structure does not match types of all path parts:
  * Strings keys (outside of square brackets) MUST correspond to an object that subclasses `dict`
  * Numerical indicies (within square brackets) MUST correspond to an object that subclasses `list`
