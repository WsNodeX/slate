"""End-to-end demonstration of Slate's declarative models.

Run with::

    python examples/demo.py
"""

from slate import (
    Model,
    Str,
    Int,
    Float,
    Bool,
    List,
    Email,
    Optional,
    validator,
    model_validator,
)


class Account(Model):
    username = Str(min_len=3, max_len=20, pattern=r"^[a-zA-Z0-9_]+$")
    age = Int(ge=13, le=120)
    email = Email()
    nickname = Optional(Str(max_len=30))
    newsletter = Bool()

    @validator("username")
    def lower_username(cls, value):
        # field validators may transform the coerced value
        return value.lower()

    @model_validator
    def check_teen_consent(cls, values):
        if values.get("age", 0) < 16 and values.get("newsletter"):
            raise ValueError("users under 16 cannot subscribe to the newsletter")


def main():
    payload = {
        "username": "Ada_Lovelace",
        "age": 36,
        "email": "ada@example.com",
        "newsletter": True,
    }
    result = Account.validate(payload)
    if result.valid:
        user = result.value
        print("Parsed account:", user.dump())
    else:
        for err in result.errors:
            loc = err.path or "<root>"
            print(f"  error at {loc}: {err.message}")


if __name__ == "__main__":
    main()
