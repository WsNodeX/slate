"""Slate — a dependency-free Python toolkit for typed data validation.

Validate and transform untrusted data (API payloads, config files, scraped
records) with a small, declarative, zero-dependency API.

Typical use::

    from slate import Model, Str, Int, Email

    class User(Model):
        name = Str(min_len=1, max_len=50)
        age = Int(ge=0, le=150)
        email = Email()

    result = User.validate({"name": "Ada", "age": 36, "email": "a@x.com"})
    if result.valid:
        user = result.value
"""

__version__ = "0.1.0"

from .errors import (
    ValidationError,
    ValidationResult,
    ErrorDetail,
)
from .types import (
    Str,
    Int,
    Float,
    Bool,
    Const,
    Any,
    Nil,
    Enum,
    DateTime,
    Email,
    Field,
)
from .collections import (
    List,
    Dict,
    Tuple,
    Optional,
    Union,
)
from .model import (
    Model,
    Nested,
    validator,
    model_validator,
)
from .adapters import TypeAdapter
from . import cli

__all__ = [
    "ValidationError",
    "ValidationResult",
    "ErrorDetail",
    "Str",
    "Int",
    "Float",
    "Bool",
    "Const",
    "Any",
    "Nil",
    "Enum",
    "DateTime",
    "Email",
    "Field",
    "List",
    "Dict",
    "Tuple",
    "Optional",
    "Union",
    "Model",
    "Nested",
    "validator",
    "model_validator",
    "TypeAdapter",
    "cli",
    "__version__",
]
