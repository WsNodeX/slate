"""Print a Slate model's schema as JSON.

Useful when you want to expose the contract of a model to other systems
(documentation, code generation, UI forms).

Run with::

    python tools/schema_dump.py
"""

import json

from slate import Model, Str, Int, Float, Bool, List, Optional, Email


class Profile(Model):
    username = Str(min_len=3, max_len=20)
    age = Int(ge=0, le=150)
    email = Email()
    height = Optional(Float(ge=0))
    tags = List(Str(), min_len=0)


def main():
    print(json.dumps(Profile.schema(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
