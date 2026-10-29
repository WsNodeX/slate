"""Error types, the missing-value sentinel and validation results for Slate.

Slate is a dependency-free toolkit for validating and transforming untrusted
data (API payloads, configuration files, scraped records, ...).  Every field
produces a :class:`ValidationResult` that is either valid (carrying the coerced
value) or invalid (carrying a list of :class:`ErrorDetail`, each with a JSON-path
style location, a human readable message and a stable machine code).
"""

from datetime import datetime, date


# Sentinel used to distinguish "key absent" from "key present with value None".
MISSING = object()


class _CoercionError:
    """Internal marker returned by ``_coerce`` to signal a type mismatch.

    It is never exposed to callers; :class:`Field.validate` converts it into a
    normal :class:`ErrorDetail`.
    """

    __slots__ = ("message", "code")

    def __init__(self, message, code):
        self.message = message
        self.code = code


class ErrorDetail:
    """A single validation failure located at ``path``."""

    __slots__ = ("path", "message", "code")

    def __init__(self, path, message, code="error"):
        self.path = path
        self.message = message
        self.code = code

    def __repr__(self):
        return (
            f"ErrorDetail(path={self.path!r}, message={self.message!r}, "
            f"code={self.code!r})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, ErrorDetail)
            and self.path == other.path
            and self.message == other.message
            and self.code == other.code
        )


class ValidationError(Exception):
    """Raised by ``parse`` / ``raise_for_errors`` when validation fails."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__(self._format())

    def _format(self):
        if not self.errors:
            return "validation failed"
        return "; ".join(
            (f"{e.path}: " if e.path else "") + e.message for e in self.errors
        )


class ValidationResult:
    """The outcome of validating a single value or an entire model."""

    __slots__ = ("value", "errors")

    def __init__(self, value=None, errors=None):
        self.value = value
        self.errors = list(errors) if errors else []

    @property
    def valid(self):
        return not self.errors

    def raise_for_errors(self):
        """Raise :class:`ValidationError` if this result is invalid."""
        if self.errors:
            raise ValidationError(self.errors)

    def __repr__(self):
        if self.valid:
            return f"ValidationResult(valid=True, value={self.value!r})"
        return f"ValidationResult(valid=False, errors={self.errors!r})"

    def __eq__(self, other):
        return (
            isinstance(other, ValidationResult)
            and self.value == other.value
            and self.errors == other.errors
        )


def _hashable(value):
    """Best-effort hashable projection of a value for uniqueness checks."""
    try:
        hash(value)
        return value
    except TypeError:
        try:
            import json

            return json.dumps(value, sort_keys=True, default=str)
        except Exception:
            return repr(value)
