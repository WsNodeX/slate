"""Tests for the command line interface."""

import json
import os
import tempfile
import unittest

from slate.cli import main


class TestCli(unittest.TestCase):
    def test_version(self):
        self.assertEqual(main(["version"]), 0)

    def test_demo(self):
        self.assertEqual(main(["demo"]), 0)

    def test_validate_ok(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"name": "ada", "age": 36}, fh)
            path = fh.name
        try:
            self.assertEqual(main(["validate", path]), 0)
        finally:
            os.unlink(path)

    def test_validate_bad_json(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("{not valid json")
            path = fh.name
        try:
            self.assertEqual(main(["validate", path]), 1)
        finally:
            os.unlink(path)

    def test_validate_no_nulls(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"a": 1, "b": None}, fh)
            path = fh.name
        try:
            self.assertEqual(main(["validate", path, "--no-nulls"]), 1)
        finally:
            os.unlink(path)

    def test_validate_missing_file(self):
        self.assertEqual(main(["validate", "/no/such/file.json"]), 2)


if __name__ == "__main__":
    unittest.main()
