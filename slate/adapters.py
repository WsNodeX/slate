"""Stand-alone validation of a single value via :class:`TypeAdapter`."""

from .errors import ValidationResult, ValidationError
from .types import Field, _infer_type


class TypeAdapter:
    """Validate one value against a field, without declaring a full model.

    Accepts either a :class:`Field` instance or a bare Python type that can be
    inferred (``int``, ``str``, ``float``, ``bool``, ``list``, ``dict``, ...).
    """

    def __init__(self, field):
        if isinstance(field, Field):
            self.field = field
        else:
            self.field = _infer_type(field)

    def validate(self, value, path=""):
        return self.field.validate(value, path)

    def parse(self, value, path=""):
        """Return the coerced value or raise :class:`ValidationError`."""
        result = self.field.validate(value, path)
        result.raise_for_errors()
        return result.value
