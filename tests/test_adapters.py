"""Tests for TypeAdapter and the errors / results API."""

import unittest

from slate import TypeAdapter, Int, Str, List
from slate.errors import (
    ValidationResult,
    ValidationError,
    ErrorDetail,
    MISSING,
)


class TestTypeAdapter(unittest.TestCase):
    def test_int(self):
        a = TypeAdapter(int)
        self.assertEqual(a.parse("42"), 42)
        self.assertFalse(a.validate("x").valid)

    def test_str(self):
        a = TypeAdapter(Str(min_len=2))
        self.assertEqual(a.parse("hi"), "hi")
        self.assertFalse(a.validate("x").valid)

    def test_list_inferred(self):
        a = TypeAdapter(List(int))
        self.assertEqual(a.parse(["1", "2"]), [1, 2])

    def test_parse_raises(self):
        a = TypeAdapter(Int())
        with self.assertRaises(ValidationError):
            a.parse("nope")


class TestValidationResult(unittest.TestCase):
    def test_valid(self):
        r = ValidationResult(value=5)
        self.assertTrue(r.valid)

    def test_invalid(self):
        r = ValidationResult(errors=[ErrorDetail("x", "bad", "type")])
        self.assertFalse(r.valid)
        with self.assertRaises(ValidationError):
            r.raise_for_errors()

    def test_equality(self):
        r1 = ValidationResult(value=1, errors=[])
        r2 = ValidationResult(value=1)
        self.assertEqual(r1, r2)


class TestErrorDetail(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(
            ErrorDetail("a", "msg", "type"), ErrorDetail("a", "msg", "type")
        )

    def test_missing_sentinel_distinct(self):
        self.assertIsNot(MISSING, None)


if __name__ == "__main__":
    unittest.main()
