# datapath python module

from ._base import (
    is_path,
    validate_path,
    split,
    join,
    leaf,
    get,
    iterate,
    put,
    delete,
    discard,
)
from .collection import collection
from .folding import (
    unfold_path_dict,
    fold_path_dict,
    complete_collection,
    UnfoldProcessor,
)
from .types import (
    DatapathError,
    ValidationError,
    InvalidIterationError,
    PathLookupError,
)

__all__ = [
    'get',
    'iterate',
    'put',
    'delete',
    'discard',
    'is_path',
    'validate_path',
    'split',
    'join',
    'leaf',
    'unfold_path_dict',
    'fold_path_dict',
    'collection',
    'UnfoldProcessor',
    'DatapathError',
    'ValidationError',
    'InvalidIterationError',
    'PathLookupError',
]
