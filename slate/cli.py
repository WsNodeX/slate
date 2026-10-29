"""Command line interface for Slate.

Usage:::

    slate demo                     # run a built-in demonstration
    slate validate file.json       # lint a JSON document
    slate validate file.json --no-nulls
    slate version
"""

import argparse
import json
import sys

from . import __version__
from .errors import ValidationError
from .model import Model
from .types import Str, Int, Float, Bool, Email
from .collections import List


def _run_demo():
    print("Slate — validation demo\n")

    class User(Model):
        name = Str(min_len=1, max_len=50, strip=True)
        age = Int(ge=0, le=150)
        email = Email()
        active = Bool()
        roles = List(Str(), min_len=1)

    good = {
        "name": "  Ada Lovelace  ",
        "age": 36,
        "email": "ada@example.com",
        "active": "yes",
        "roles": ["admin", "author"],
    }
    bad = {
        "name": "",
        "age": -5,
        "email": "not-an-email",
        "active": 2,
        "roles": ["admin", 7],
    }

    r1 = User.validate(good)
    print("Valid payload  ->", r1.value.dump() if r1.valid else "FAILED")
    r2 = User.validate(bad)
    print("Invalid payload -> valid =", r2.valid)
    for err in r2.errors:
        loc = err.path or "<root>"
        print(f"   - {loc}: {err.message}  [{err.code}]")
    return 0


def _run_validate(path, no_nulls):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        print(f"error: file not found: {path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}")
        return 1

    if not isinstance(data, dict):
        print("error: top-level JSON must be an object")
        return 1
    if no_nulls:
        null_keys = [k for k, v in data.items() if v is None]
        if null_keys:
            print("error: null values found for keys: " + ", ".join(null_keys))
            return 1
    print(f"OK: valid JSON object with {len(data)} keys")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="slate", description="Slate data validation toolkit"
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("demo", help="run a built-in demonstration")
    p_validate = sub.add_parser("validate", help="validate / lint a JSON file")
    p_validate.add_argument("file", help="path to a JSON file")
    p_validate.add_argument(
        "--no-nulls", action="store_true", help="reject any null value"
    )
    sub.add_parser("version", help="print the installed version")

    args = parser.parse_args(argv)

    if args.cmd == "demo" or args.cmd is None:
        return _run_demo()
    if args.cmd == "validate":
        return _run_validate(args.file, args.no_nulls)
    if args.cmd == "version":
        print(__version__)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
