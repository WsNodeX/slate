"""Declarative models: define a schema as a class, validate dicts against it.

A ``Model`` subclass collects every :class:`Field` declared as a class attribute
into an ordered ``_fields`` map (the field is removed from the class namespace so
it never collides with instance state).  Two kinds of validators can be attached
with decorators:

* ``@validator('field')`` — runs after a single field has been coerced/checked;
* ``@model_validator`` — runs after *all* fields, receives the dict of coerced
  values and can enforce cross-field invariants.
"""

from .errors import MISSING, ErrorDetail, ValidationError, ValidationResult
from .types import Field


class _Validator:
    """Descriptor produced by :func:`validator` / :func:`model_validator`."""

    __slots__ = ("field", "is_model", "func")

    def __init__(self, field=None, is_model=False):
        self.field = field
        self.is_model = is_model
        self.func = None

    def __call__(self, func):
        self.func = func
        return self


def validator(field_name):
    """Decorate a method that post-processes / checks ``field_name``."""
    return _Validator(field=field_name)


def model_validator(maybe_func=None):
    """Decorate a method that enforces a cross-field invariant.

    Usable both as ``@model_validator`` and ``@model_validator()``.
    """
    if callable(maybe_func):
        marker = _Validator(is_model=True)
        marker(maybe_func)
        return marker
    return _Validator(is_model=True)


class ModelMeta(type):
    """Collects fields and validators from a class and its bases."""

    def __new__(mcs, name, bases, ns):
        fields = {}
        field_validators = {}
        model_validators = []

        for base in bases:
            fields.update(getattr(base, "_fields", {}))
            field_validators.update(getattr(base, "_field_validators", {}))
            model_validators.extend(getattr(base, "_model_validators", []))

        for key, val in list(ns.items()):
            if isinstance(val, Field):
                val.name = key
                fields[key] = val
            elif isinstance(val, _Validator):
                if val.is_model:
                    model_validators.append(val.func)
                else:
                    field_validators[val.field] = val.func

        for key in [k for k in ns if isinstance(ns[k], Field)]:
            del ns[key]

        ns["_fields"] = fields
        ns["_field_validators"] = field_validators
        ns["_model_validators"] = model_validators
        return super().__new__(mcs, name, bases, ns)


class Nested(Field):
    """Embed another :class:`Model` as a field (validates a nested mapping)."""

    def __init__(self, model, **kw):
        super().__init__(**kw)
        if not (isinstance(model, type) and issubclass(model, Model)):
            raise TypeError("Nested expects a Model subclass")
        self.model = model

    def validate(self, value, path=""):
        res = Field.validate(self, value, path)
        if not res.valid:
            return res
        if res.value is None:
            return res
        inner = self.model.validate(res.value)
        if inner.valid:
            return ValidationResult(value=inner.value)
        errors = []
        for err in inner.errors:
            loc = f"{path}.{err.path}" if err.path else path
            errors.append(ErrorDetail(loc, err.message, err.code))
        return ValidationResult(errors=errors)


class Model(metaclass=ModelMeta):
    """Base class for declarative validation models."""

    def __init__(self, **kwargs):
        for field in self._fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    @classmethod
    def validate(cls, data):
        """Validate ``data`` (a mapping) and return a :class:`ValidationResult`.

        Never raises — inspect ``result.valid`` and ``result.errors``.
        """
        if not isinstance(data, dict):
            return ValidationResult(
                errors=[ErrorDetail("", "input must be a mapping", "type")]
            )

        result = {}
        errors = []
        for fname, field in cls._fields.items():
            raw = data.get(fname, MISSING)
            if raw is MISSING and field.alias:
                raw = data.get(field.alias, MISSING)
            r = field.validate(raw, path=fname)
            if r.valid:
                result[fname] = r.value
            else:
                errors.extend(r.errors)

        for fname, func in cls._field_validators.items():
            if fname in result:
                try:
                    result[fname] = func(cls, result[fname])
                except (ValueError, ValidationError) as exc:
                    errors.append(ErrorDetail(fname, str(exc), "validator"))

        for func in cls._model_validators:
            try:
                func(cls, result)
            except (ValueError, ValidationError) as exc:
                errors.append(ErrorDetail("", str(exc), "model_validator"))

        if errors:
            return ValidationResult(errors=errors)
        return ValidationResult(value=cls._build(result))

    @classmethod
    def parse(cls, data):
        """Validate and return a model instance, raising on failure."""
        result = cls.validate(data)
        result.raise_for_errors()
        return result.value

    @classmethod
    def _build(cls, values):
        obj = cls.__new__(cls)
        obj.__init__(**values)
        return obj

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def dump(self):
        """Return a plain ``dict`` of coerced, serialisable values."""
        return {field: _dump_value(getattr(self, field, None)) for field in self._fields}

    @classmethod
    def schema(cls):
        """Return a JSON-serialisable description of the model's fields."""
        return {field: f.describe() for field, f in cls._fields.items()}


def _dump_value(value):
    if isinstance(value, Model):
        return value.dump()
    if isinstance(value, dict):
        return {k: _dump_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_dump_value(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value
