"""Composite field types: ``List``, ``Dict``, ``Tuple``, ``Optional``, ``Union``.

Each composite delegates the validation of its children to sub-fields and then
aggregates their :class:`ValidationResult` objects, preserving a JSON-path style
location for every nested error.
"""

from .errors import _CoercionError, ErrorDetail, ValidationResult, _hashable
from .types import Field, _infer_type, Any


class List(Field):
    """An ordered sequence of items validated by ``item``."""

    def __init__(self, item, *, min_len=None, max_len=None, unique=False, **kw):
        super().__init__(**kw)
        self.item = item if isinstance(item, Field) else _infer_type(item)
        self.min_len = min_len
        self.max_len = max_len
        self.unique = unique

    def _coerce(self, value):
        if isinstance(value, (list, tuple)):
            return list(value)
        return _CoercionError("not a valid list", "type")

    def validate(self, value, path=""):
        res = Field.validate(self, value, path)
        if not res.valid:
            return res
        items = res.value
        out = []
        errors = []
        for i, it in enumerate(items):
            r = self.item.validate(it, path=f"{path}[{i}]")
            if r.valid:
                out.append(r.value)
            else:
                errors.extend(r.errors)

        if self.min_len is not None and len(items) < self.min_len:
            errors.append(
                ErrorDetail(
                    path,
                    f"length {len(items)} is less than minimum {self.min_len}",
                    "min_length",
                )
            )
        if self.max_len is not None and len(items) > self.max_len:
            errors.append(
                ErrorDetail(
                    path,
                    f"length {len(items)} is greater than maximum {self.max_len}",
                    "max_length",
                )
            )
        if self.unique:
            seen = set()
            for it in items:
                h = _hashable(it)
                if h in seen:
                    errors.append(
                        ErrorDetail(path, "items must be unique", "unique")
                    )
                    break
                seen.add(h)

        if errors:
            return ValidationResult(errors=errors)
        return ValidationResult(value=out)


class Dict(Field):
    """A mapping with independently typed keys and values."""

    def __init__(self, key_type=Any(), value_type=Any(), **kw):
        super().__init__(**kw)
        self.key_type = key_type if isinstance(key_type, Field) else _infer_type(
            key_type
        )
        self.value_type = (
            value_type if isinstance(value_type, Field) else _infer_type(value_type)
        )

    def _coerce(self, value):
        if isinstance(value, dict):
            return value
        return _CoercionError("not a valid mapping", "type")

    def validate(self, value, path=""):
        res = Field.validate(self, value, path)
        if not res.valid:
            return res
        out = {}
        errors = []
        for k, v in res.value.items():
            kp = f"{path}.{k}" if isinstance(k, str) else f"{path}[{k}]"
            rk = self.key_type.validate(k, path=kp)
            rv = self.value_type.validate(v, path=kp)
            if rk.valid and rv.valid:
                out[rk.value] = rv.value
            else:
                errors.extend(rk.errors)
                errors.extend(rv.errors)
        if errors:
            return ValidationResult(errors=errors)
        return ValidationResult(value=out)


class Tuple(Field):
    """A fixed-length, positionally typed tuple."""

    def __init__(self, *item_types, **kw):
        super().__init__(**kw)
        self.items = [
            t if isinstance(t, Field) else _infer_type(t) for t in item_types
        ]

    def _coerce(self, value):
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return _CoercionError("not a valid tuple", "type")

    def validate(self, value, path=""):
        res = Field.validate(self, value, path)
        if not res.valid:
            return res
        t = res.value
        if len(t) != len(self.items):
            return ValidationResult(
                errors=[
                    ErrorDetail(
                        path,
                        f"expected {len(self.items)} items, got {len(t)}",
                        "length",
                    )
                ]
            )
        out = []
        errors = []
        for i, (it, typ) in enumerate(zip(t, self.items)):
            r = typ.validate(it, path=f"{path}[{i}]")
            if r.valid:
                out.append(r.value)
            else:
                errors.extend(r.errors)
        if errors:
            return ValidationResult(errors=errors)
        return ValidationResult(value=tuple(out))


class Optional(Field):
    """Wraps a field so that ``None`` and a missing key are both accepted."""

    def __init__(self, inner, **kw):
        kw.setdefault("required", False)
        super().__init__(**kw)
        self.inner = inner if isinstance(inner, Field) else _infer_type(inner)

    def validate(self, value, path=""):
        if _is_missing(value) or value is None:
            return ValidationResult(value=None)
        return self.inner.validate(value, path)


def _is_missing(value):
    from .errors import MISSING

    return value is MISSING


class Union(Field):
    """Tries each candidate type in order and accepts the first match."""

    def __init__(self, *types, **kw):
        super().__init__(**kw)
        self.types = [
            t if isinstance(t, Field) else _infer_type(t) for t in types
        ]

    def validate(self, value, path=""):
        for t in self.types:
            r = t.validate(value, path)
            if r.valid:
                return r
        return ValidationResult(
            errors=[
                ErrorDetail(
                    path,
                    f"value does not match any of {len(self.types)} types",
                    "union",
                )
            ]
        )
