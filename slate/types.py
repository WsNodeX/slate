"""Scalar field types and the base :class:`Field` class.

A field owns two responsibilities:

* *coercion* (``_coerce``) — turn a loosely typed input into the canonical
  Python type, or return a :class:`_CoercionError` on a type mismatch;
* *checks* (``_check``) — enforce constraints (length, range, pattern, ...).

``validate`` wires the two together with missing-value handling and returns a
:class:`ValidationResult`.
"""

import re
import enum as _enum
from datetime import datetime, date

from .errors import MISSING, _CoercionError, ErrorDetail, ValidationResult

_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_bool(value):
    return isinstance(value, bool)


class Field:
    """Base class for every Slate field."""

    def __init__(
        self,
        *,
        required=True,
        default=MISSING,
        default_factory=None,
        alias=None,
        description=None,
    ):
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.alias = alias
        self.description = description
        self.name = None

    def _coerce(self, value):
        return value

    def _check(self, value, path):
        return []

    def validate(self, value, path=""):
        if value is MISSING:
            if self.default is not MISSING:
                value = self.default
            elif self.default_factory is not None:
                value = self.default_factory()
            elif self.required:
                return ValidationResult(
                    errors=[ErrorDetail(path, "field required", "required")]
                )
            else:
                return ValidationResult(value=None)

        coerced = self._coerce(value)
        if isinstance(coerced, _CoercionError):
            return ValidationResult(
                errors=[ErrorDetail(path, coerced.message, coerced.code)]
            )

        errors = self._check(coerced, path)
        if errors:
            return ValidationResult(
                errors=[ErrorDetail(path, m, c) for m, c in errors]
            )
        return ValidationResult(value=coerced)

    def describe(self):
        """Return a small schema description (used by tooling / dumps)."""
        info = {"type": type(self).__name__}
        if self.alias:
            info["alias"] = self.alias
        if self.description:
            info["description"] = self.description
        if self.default is not MISSING:
            info["default"] = self.default
        return info


class Str(Field):
    """Unicode string with optional length / pattern / case transforms."""

    def __init__(
        self,
        *,
        min_len=None,
        max_len=None,
        pattern=None,
        strip=False,
        lower=False,
        upper=False,
        **kw,
    ):
        super().__init__(**kw)
        self.min_len = min_len
        self.max_len = max_len
        self.pattern = re.compile(pattern) if pattern else None
        self.strip = strip
        self.lower = lower
        self.upper = upper

    def _coerce(self, value):
        if isinstance(value, str):
            s = value
        elif isinstance(value, (bytes, bytearray)):
            try:
                s = value.decode("utf-8")
            except UnicodeDecodeError:
                return _CoercionError("not a valid utf-8 string", "type")
        else:
            return _CoercionError("not a valid string", "type")
        if self.strip:
            s = s.strip()
        if self.lower:
            s = s.lower()
        if self.upper:
            s = s.upper()
        return s

    def _check(self, value, path):
        errs = []
        if self.min_len is not None and len(value) < self.min_len:
            errs.append(
                (
                    f"length {len(value)} is less than minimum {self.min_len}",
                    "min_length",
                )
            )
        if self.max_len is not None and len(value) > self.max_len:
            errs.append(
                (
                    f"length {len(value)} is greater than maximum {self.max_len}",
                    "max_length",
                )
            )
        if self.pattern is not None and not self.pattern.search(value):
            errs.append(
                (
                    f"string does not match pattern {self.pattern.pattern}",
                    "pattern",
                )
            )
        return errs


class Int(Field):
    """Integer with lenient coercion and range / multiple-of checks."""

    def __init__(
        self, *, ge=None, le=None, gt=None, lt=None, multiple_of=None, **kw
    ):
        super().__init__(**kw)
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.multiple_of = multiple_of

    def _coerce(self, value):
        if _is_bool(value):
            return _CoercionError("bool is not an int", "type")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return _CoercionError("float has a fractional part", "type")
        if isinstance(value, str):
            s = value.strip()
            if _INT_RE.match(s):
                return int(s)
            return _CoercionError("not a valid integer", "type")
        return _CoercionError("not a valid integer", "type")

    def _check(self, value, path):
        errs = []
        if self.gt is not None and not value > self.gt:
            errs.append((f"must be greater than {self.gt}", "gt"))
        if self.ge is not None and not value >= self.ge:
            errs.append((f"must be greater than or equal to {self.ge}", "ge"))
        if self.lt is not None and not value < self.lt:
            errs.append((f"must be less than {self.lt}", "lt"))
        if self.le is not None and not value <= self.le:
            errs.append((f"must be less than or equal to {self.le}", "le"))
        if self.multiple_of is not None and value % self.multiple_of != 0:
            errs.append((f"must be a multiple of {self.multiple_of}", "multiple_of"))
        return errs


class Float(Field):
    """Floating point number with lenient coercion and range checks."""

    def __init__(self, *, ge=None, le=None, gt=None, lt=None, **kw):
        super().__init__(**kw)
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt

    def _coerce(self, value):
        if _is_bool(value):
            return _CoercionError("bool is not a number", "type")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip()
            if _FLOAT_RE.match(s):
                return float(s)
            return _CoercionError("not a valid number", "type")
        return _CoercionError("not a valid number", "type")

    def _check(self, value, path):
        errs = []
        if self.gt is not None and not value > self.gt:
            errs.append((f"must be greater than {self.gt}", "gt"))
        if self.ge is not None and not value >= self.ge:
            errs.append((f"must be greater than or equal to {self.ge}", "ge"))
        if self.lt is not None and not value < self.lt:
            errs.append((f"must be less than {self.lt}", "lt"))
        if self.le is not None and not value <= self.le:
            errs.append((f"must be less than or equal to {self.le}", "le"))
        return errs


class Bool(Field):
    """Boolean with coercion from common string / numeric spellings."""

    def _coerce(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("true", "yes", "1"):
                return True
            if s in ("false", "no", "0"):
                return False
            return _CoercionError("not a valid boolean", "type")
        return _CoercionError("not a valid boolean", "type")


class Const(Field):
    """Accepts only a single constant value."""

    def __init__(self, value, **kw):
        super().__init__(**kw)
        self.value = value

    def _coerce(self, value):
        if value != self.value:
            return _CoercionError(f"must be equal to {self.value!r}", "const")
        return value


class Any(Field):
    """Accepts any value without coercion or checks."""


class Nil(Field):
    """Accepts only ``None``."""

    def _coerce(self, value):
        if value is None:
            return None
        return _CoercionError("must be null", "type")


class Enum(Field):
    """Accepts values belonging to a set (an ``enum.Enum`` or a list)."""

    def __init__(self, values, **kw):
        super().__init__(**kw)
        if isinstance(values, type) and issubclass(values, _enum.Enum):
            self.allowed = [e.value for e in values]
            self._by_name = {e.name: e.value for e in values}
        else:
            self.allowed = list(values)
            self._by_name = {}

    def _coerce(self, value):
        if value in self.allowed:
            return value
        if value in self._by_name:
            return self._by_name[value]
        return _CoercionError(f"must be one of {self.allowed}", "enum")


class DateTime(Field):
    """Accepts ``datetime`` objects or ISO-8601 strings."""

    def _coerce(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day)
        if isinstance(value, str):
            s = value.strip()
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                try:
                    return datetime.combine(
                        date.fromisoformat(s), datetime.min.time()
                    )
                except ValueError:
                    return _CoercionError("not a valid ISO-8601 datetime", "type")
        return _CoercionError("not a valid datetime", "type")


class Email(Str):
    """RFC-loose email string (sufficient for 99% of form validation)."""

    def __init__(self, **kw):
        kw.setdefault("pattern", _EMAIL_RE.pattern)
        super().__init__(**kw)


def _infer_type(t):
    """Map a bare Python type to a Slate field (used by container shorthand)."""
    if isinstance(t, Field):
        return t
    if t is int:
        return Int()
    if t is float:
        return Float()
    if t is str:
        return Str()
    if t is bool:
        return Bool()
    if t is type(None) or t is None:
        return Nil()
    if t is dict:
        from .collections import Dict

        return Dict()
    if t is list:
        from .collections import List

        return List(Any())
    if t is object:
        return Any()
    # A bare Model subclass used as a container element becomes a Nested field.
    from .model import Model, Nested

    if isinstance(t, type) and issubclass(t, Model):
        return Nested(t)
    raise TypeError(f"cannot infer a Slate field from {t!r}")
