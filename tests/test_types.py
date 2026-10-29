"""Tests for scalar field types."""

import unittest
from datetime import datetime

from slate import (
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
)
from slate.errors import ValidationResult


class TestStr(unittest.TestCase):
    def test_basic(self):
        r = Str().validate("hello")
        self.assertTrue(r.valid)
        self.assertEqual(r.value, "hello")

    def test_type_error(self):
        r = Str().validate(123)
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "type")

    def test_min_max_len(self):
        f = Str(min_len=2, max_len=4)
        self.assertTrue(f.validate("ab").valid)
        self.assertFalse(f.validate("a").valid)
        self.assertFalse(f.validate("abcde").valid)

    def test_pattern(self):
        f = Str(pattern=r"^\d{3}$")
        self.assertTrue(f.validate("123").valid)
        self.assertFalse(f.validate("12").valid)

    def test_transforms(self):
        f = Str(strip=True, lower=True)
        r = f.validate("  HeLLo  ")
        self.assertEqual(r.value, "hello")

    def test_bytes(self):
        r = Str().validate(b"hi")
        self.assertEqual(r.value, "hi")

    def test_default(self):
        r = Str(default="x").validate(object())  # missing sentinel
        from slate.errors import MISSING

        r = Str(default="x").validate(MISSING)
        self.assertTrue(r.valid)
        self.assertEqual(r.value, "x")


class TestInt(unittest.TestCase):
    def test_int(self):
        self.assertEqual(Int().validate(5).value, 5)

    def test_coerce_string(self):
        self.assertEqual(Int().validate("  -7 ").value, -7)

    def test_coerce_float_integral(self):
        self.assertEqual(Int().validate(7.0).value, 7)

    def test_float_fractional_error(self):
        r = Int().validate(7.5)
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "type")

    def test_bool_rejected(self):
        r = Int().validate(True)
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "type")

    def test_ranges(self):
        f = Int(ge=0, le=10, gt=None, lt=None)
        self.assertTrue(f.validate(0).valid)
        self.assertFalse(f.validate(-1).valid)
        self.assertFalse(f.validate(11).valid)

    def test_multiple_of(self):
        f = Int(multiple_of=3)
        self.assertTrue(f.validate(9).valid)
        self.assertFalse(f.validate(10).valid)

    def test_required(self):
        from slate.errors import MISSING

        r = Int().validate(MISSING)
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "required")


class TestFloat(unittest.TestCase):
    def test_coerce(self):
        self.assertEqual(Float().validate("3.5").value, 3.5)
        self.assertEqual(Float().validate(2).value, 2.0)

    def test_range(self):
        f = Float(gt=0, le=1)
        self.assertTrue(f.validate(0.5).valid)
        self.assertFalse(f.validate(2).valid)

    def test_bool_rejected(self):
        self.assertFalse(Float().validate(False).valid)


class TestBool(unittest.TestCase):
    def test_values(self):
        self.assertTrue(Bool().validate(True).value)
        self.assertFalse(Bool().validate(False).value)

    def test_coerce_strings(self):
        self.assertTrue(Bool().validate("yes").value)
        self.assertFalse(Bool().validate("NO").value)
        self.assertTrue(Bool().validate("1").value)

    def test_reject_other(self):
        self.assertFalse(Bool().validate(5).valid)
        self.assertFalse(Bool().validate("maybe").valid)


class TestConst(unittest.TestCase):
    def test_match(self):
        self.assertTrue(Const("v1").validate("v1").valid)

    def test_mismatch(self):
        r = Const("v1").validate("v2")
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "const")


class TestAnyNil(unittest.TestCase):
    def test_any(self):
        self.assertTrue(Any().validate({"x": 1}).valid)

    def test_nil(self):
        self.assertTrue(Nil().validate(None).valid)
        self.assertFalse(Nil().validate(0).valid)


class TestEnum(unittest.TestCase):
    def test_list(self):
        f = Enum([1, 2, 3])
        self.assertEqual(f.validate(2).value, 2)
        self.assertFalse(f.validate(4).valid)

    def test_enum_class(self):
        from enum import Enum as PyEnum

        class Color(PyEnum):
            RED = "red"
            BLUE = "blue"

        f = Enum(Color)
        self.assertEqual(f.validate("red").value, "red")
        self.assertEqual(f.validate("BLUE").value, "blue")
        self.assertFalse(f.validate("green").valid)


class TestDateTime(unittest.TestCase):
    def test_string(self):
        r = DateTime().validate("2023-01-01T12:30:00")
        self.assertTrue(r.valid)
        self.assertIsInstance(r.value, datetime)

    def test_date_only(self):
        r = DateTime().validate("2023-01-01")
        self.assertTrue(r.valid)

    def test_object(self):
        d = datetime(2020, 5, 5, 9, 0, 0)
        self.assertEqual(DateTime().validate(d).value, d)

    def test_bad(self):
        self.assertFalse(DateTime().validate("nope").valid)


class TestEmail(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(Email().validate("a@b.com").valid)

    def test_invalid(self):
        self.assertFalse(Email().validate("a@b").valid)


if __name__ == "__main__":
    unittest.main()
