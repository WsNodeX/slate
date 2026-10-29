"""Tests for declarative models, validators and nesting."""

import unittest

from slate import (
    Model,
    Str,
    Int,
    Bool,
    Email,
    List,
    Optional,
    Nested,
    validator,
    model_validator,
)
from slate.errors import MISSING, ValidationError


class TestBasicModel(unittest.TestCase):
    def test_valid(self):
        class User(Model):
            name = Str(min_len=1)
            age = Int(ge=0)

        r = User.validate({"name": "Ada", "age": 36})
        self.assertTrue(r.valid)
        self.assertEqual(r.value.name, "Ada")
        self.assertEqual(r.value.age, 36)

    def test_missing_required(self):
        class User(Model):
            name = Str()
            age = Int()

        r = User.validate({"name": "Ada"})
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "required")
        self.assertEqual(r.errors[0].path, "age")

    def test_collect_all_errors(self):
        class User(Model):
            name = Str(min_len=2)
            age = Int(ge=0)

        r = User.validate({"name": "a", "age": -1})
        self.assertEqual(len(r.errors), 2)

    def test_default(self):
        class Cfg(Model):
            host = Str(default="localhost")
            port = Int(default=8080)

        r = Cfg.validate({})
        self.assertTrue(r.valid)
        self.assertEqual(r.value.host, "localhost")
        self.assertEqual(r.value.port, 8080)

    def test_alias(self):
        class Cfg(Model):
            user_name = Str(alias="userName")

        r = Cfg.validate({"userName": "ada"})
        self.assertTrue(r.valid)
        self.assertEqual(r.value.user_name, "ada")

    def test_non_mapping(self):
        class M(Model):
            x = Int()

        r = M.validate([1, 2])
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "type")


class TestValidators(unittest.TestCase):
    def test_field_validator_transform(self):
        class M(Model):
            name = Str()

            @validator("name")
            def upper(cls, value):
                return value.upper()

        r = M.validate({"name": "ada"})
        self.assertEqual(r.value.name, "ADA")

    def test_field_validator_error(self):
        class M(Model):
            age = Int()

            @validator("age")
            def adult(cls, value):
                if value < 18:
                    raise ValueError("must be an adult")
                return value

        r = M.validate({"age": 10})
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "validator")

    def test_model_validator(self):
        class Signup(Model):
            password = Str(min_len=1)
            confirm = Str(min_len=1)

            @model_validator
            def match(cls, values):
                if values.get("password") != values.get("confirm"):
                    raise ValueError("passwords do not match")

        self.assertTrue(Signup.validate(
            {"password": "x", "confirm": "x"}
        ).valid)
        bad = Signup.validate({"password": "x", "confirm": "y"})
        self.assertFalse(bad.valid)
        self.assertEqual(bad.errors[0].code, "model_validator")


class TestNesting(unittest.TestCase):
    def test_nested(self):
        class Address(Model):
            city = Str()
            zip = Str()

        class Person(Model):
            name = Str()
            address = Nested(Address)

        r = Person.validate(
            {"name": "Ada", "address": {"city": "London", "zip": "EC1"}}
        )
        self.assertTrue(r.valid)
        self.assertEqual(r.value.address.city, "London")

    def test_nested_error_location(self):
        class Address(Model):
            city = Str(min_len=2)

        class Person(Model):
            address = Nested(Address)

        r = Person.validate({"address": {"city": "x"}})
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].path, "address.city")

    def test_list_of_nested(self):
        class Tag(Model):
            key = Str()
            val = Int()

        class Doc(Model):
            tags = List(Nested(Tag))

        r = Doc.validate({"tags": [{"key": "a", "val": 1}, {"key": "b", "val": 2}]})
        self.assertTrue(r.valid)
        self.assertEqual(r.value.tags[1].val, 2)

    def test_optional_nested_missing(self):
        class Inner(Model):
            x = Int()

        class Outer(Model):
            inner = Optional(Nested(Inner))

        r = Outer.validate({})
        self.assertTrue(r.valid)
        self.assertIsNone(r.value.inner)


class TestSerialisation(unittest.TestCase):
    def test_dump(self):
        class M(Model):
            name = Str()
            age = Int()

        r = M.validate({"name": "Ada", "age": 36})
        self.assertEqual(r.value.dump(), {"name": "Ada", "age": 36})

    def test_schema(self):
        class M(Model):
            name = Str(min_len=1)

        schema = M.schema()
        self.assertIn("name", schema)
        self.assertEqual(schema["name"]["type"], "Str")

    def test_parse_raises(self):
        class M(Model):
            age = Int(ge=0)

        with self.assertRaises(ValidationError):
            M.parse({"age": -1})


class TestInheritance(unittest.TestCase):
    def test_subclass_fields_merged(self):
        class Base(Model):
            id = Int()

        class Derived(Base):
            name = Str()

        r = Derived.validate({"id": 1, "name": "x"})
        self.assertTrue(r.valid)
        self.assertEqual(r.value.id, 1)
        self.assertEqual(r.value.name, "x")


if __name__ == "__main__":
    unittest.main()
