import builtins
import string
from typing import Any, Callable, Generator

from ._base import get, iterate, iterate_result
from .types import Collection, NO_DEFAULT


class _Format(string.Formatter):
    """implements the `format()` function"""

    def __init__(self, obj: Collection):
        string.Formatter.__init__(self)
        self._datapath_obj = obj

    def get_field(self, field_name, args, kwargs):
        return get(self._datapath_obj, field_name), None


def format(obj: Collection, format_string: str) -> str:
    """
    Given a standard Python format string with {} notation, interpret the identifiers
    as a datapath within `obj`, and apply standard formatting language to the result.
    """
    return _Format(obj).format(format_string)


def _do_format(value: Any, format_spec: str, conversion: str) -> str:
    """do the standard !r / !s / !a format string conversions, followed by builtins.format"""
    if not conversion:
        pass
    elif conversion == 'r':
        value = repr(value)
    elif conversion == 's':
        value = str(value)
    elif conversion == 'a':
        value = ascii(value)
    else:
        raise ValueError(f'unhandled conversion flag {conversion!r}')
    return builtins.format(value, format_spec)


def format_iterate(obj: Collection,
                   format_string: str,
                   default: Any = NO_DEFAULT,
                   iter_func: Callable = zip) -> Generator[str, None, None]:
    """
    Given a standard Python format string with {} notation, interpret the identifiers as iterable datapaths within `obj`.
    One value will be consumed from each iterable path and formatted using the standard language.

    `default` is passed through to all `iterate()` calls, which in turn passes it through to the leaf `get()` calls.
    There is no way to use a different default value for different iterable datapaths in replacement fields.

    By default, the values from the iterators will be obtained with the
    [`zip()` builtin](https://docs.python.org/3/library/functions.html#zip) with `strict=False`, meaning if the different
    iterable format strings produce a differnt number of results, iteration will stop when the shortest one stops, and
    the values will all correspond to the same index from each `iterate()` result.

    Example:

    ```
    >>> test_obj = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}, {'a': 5, 'b': 6}]
    >>> for text in format_iterate(test_obj, 'a {[].a} b {[].b}'):
    ...     print(text)
    ...
    a 1 b 2
    a 3 b 4
    a 5 b 6

    ```

    If different behavior is desired, a different function can be passed:

    `iter_func` must have approximately the same basic signature as `builtins.zip()`,
    [`itertools.product()`](https://docs.python.org/3/library/itertools.html#itertools.product),
    and [`itertools.zip_longest()`](https://docs.python.org/3/library/itertools.html#itertools.zip_longest).

    More specifically, it must accept an arbitrary number of Iterables (specifically the Generator
    returned by `datapath.iterate()`), and yield a Sequence with a value from each one in order when the return
    value is iterated.

    You can supply extra keyword arguments to any function with this signature by utilizing
    [`functools.partial()`](https://docs.python.org/3/library/functools.html#functools.partial). Passing positional
    arguments to a partial will probably not work as expected, and is not recommended.

    Example with a partial and `itertools.zip_longest()`:

    ```
    >>> import functools, itertools
    >>> test_obj = {'a': list('123'), 'b': list('4567')}
    >>> for text in format_iterate(test_obj, 'a {a[]} b {b[]}',
    ...                            iter_func=functools.partial(itertools.zip_longest, fillvalue='X')):
    ...     print(text)
    a 1 b 4
    a 2 b 5
    a 3 b 6
    a X b 7

    ```
    """
    iterators = []
    path_formats = []
    plain_format_string = ''
    for literal_text, field_name, format_spec, conversion in string.Formatter().parse(format_string):
        plain_format_string += literal_text
        if not field_name:
            continue
        plain_format_string += '{}'
        iterators.append(iterate(obj, field_name, default))
        path_formats.append((format_spec, conversion))

    for results in iter_func(*iterators):
        values = []
        for index, result in enumerate(results):
            if isinstance(result, iterate_result):
                _, value = result
            else:
                value = result
            format_spec, conversion = path_formats[index]
            values.append(_do_format(value, format_spec, conversion))
        yield plain_format_string.format(*values)
