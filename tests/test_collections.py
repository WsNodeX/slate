"""Tests for composite field types."""

import unittest

from slate import Str, Int, Float, List, Dict, Tuple, Optional, Union, Any
from slate.errors import MISSING


class TestList(unittest.TestCase):
    def test_basic(self):
        r = List(Int()).validate([1, "2", 3])
        self.assertTrue(r.valid)
        self.assertEqual(r.value, [1, 2, 3])

    def test_type_error(self):
        r = List(Int()).validate("not a list")
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "type")

    def test_nested_errors_location(self):
        r = List(Int()).validate([1, "x", 3])
        self.assertFalse(r.valid)
        paths = {e.path for e in r.errors}
        self.assertIn("[1]", paths)

    def test_min_max_len(self):
        f = List(Int(), min_len=1, max_len=2)
        self.assertFalse(f.validate([]).valid)
        self.assertFalse(f.validate([1, 2, 3]).valid)

    def test_unique(self):
        f = List(Int(), unique=True)
        self.assertTrue(f.validate([1, 2, 3]).valid)
        self.assertFalse(f.validate([1, 1, 2]).valid)

    def test_unique_unhashable(self):
        f = List(Dict(Str(), Int()), unique=True)
        self.assertTrue(f.validate([{"a": 1}, {"b": 2}]).valid)
        self.assertFalse(f.validate([{"a": 1}, {"a": 1}]).valid)

    def test_inferred_item(self):
        r = List(str).validate(["a", "b"])
        self.assertEqual(r.value, ["a", "b"])


class TestDict(unittest.TestCase):
    def test_basic(self):
        r = Dict(Str(), Int()).validate({"a": 1, "b": "2"})
        self.assertTrue(r.valid)
        self.assertEqual(r.value, {"a": 1, "b": 2})

    def test_value_error(self):
        r = Dict(Str(), Int()).validate({"a": "x"})
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].path, ".a")

    def test_type(self):
        self.assertFalse(Dict().validate([1, 2]).valid)


class TestTuple(unittest.TestCase):
    def test_fixed(self):
        r = Tuple(Int(), Str()).validate([1, "x"])
        self.assertTrue(r.valid)
        self.assertEqual(r.value, (1, "x"))

    def test_wrong_length(self):
        r = Tuple(Int(), Str()).validate([1])
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "length")

    def test_inner_error(self):
        r = Tuple(Int(), Int()).validate([1, "x"])
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].path, "[1]")


class TestOptional(unittest.TestCase):
    def test_none(self):
        self.assertTrue(Optional(Int()).validate(None).valid)

    def test_missing(self):
        self.assertTrue(Optional(Int()).validate(MISSING).valid)

    def test_value_validated(self):
        r = Optional(Int()).validate("42")
        self.assertEqual(r.value, 42)

    def test_value_invalid(self):
        self.assertFalse(Optional(Int()).validate("x").valid)


class TestUnion(unittest.TestCase):
    def test_first_match(self):
        r = Union(Int(), Str()).validate(5)
        self.assertEqual(r.value, 5)

    def test_second_match(self):
        r = Union(Int(), Str()).validate("hi")
        self.assertEqual(r.value, "hi")

    def test_no_match(self):
        r = Union(Int(), Str()).validate(3.5)
        self.assertFalse(r.valid)
        self.assertEqual(r.errors[0].code, "union")


if __name__ == "__main__":
    unittest.main()
