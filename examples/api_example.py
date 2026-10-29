"""Validate a realistic "create order" JSON API request with Slate.

This shows how a backend service can treat Slate as a data-contract layer in
front of its handlers: validate once, then trust the typed ``result.value``.

Run with::

    python examples/api_example.py
"""

import json

from slate import (
    Model,
    Str,
    Int,
    Float,
    List,
    Dict,
    Enum,
    TypeAdapter,
)


class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"


class LineItem(Model):
    sku = Str(min_len=4, max_len=16, pattern=r"^[A-Z0-9-]+$")
    quantity = Int(gt=0, le=999)
    unit_price = Float(ge=0)


class CreateOrder(Model):
    customer_id = Str(min_len=1)
    currency = Str(min_len=3, max_len=3, pattern=r"^[A-Z]{3}$")
    items = List(LineItem, min_len=1, max_len=50)
    metadata = Dict(Str(), Str(), required=False)


# A single value can be validated without a model via TypeAdapter.
amount_adapter = TypeAdapter(Float(ge=0))


def handle(raw_json):
    data = json.loads(raw_json)
    result = CreateOrder.validate(data)
    if not result.valid:
        return {"error": [e.message for e in result.errors]}, 422
    order = result.value
    total = sum(item.quantity * item.unit_price for item in order.items)
    if not amount_adapter.validate(total).valid:
        return {"error": "order total out of range"}, 422
    return {
        "customer": order.customer_id,
        "currency": order.currency,
        "lines": len(order.items),
        "total": round(total, 2),
    }, 201


def main():
    raw = json.dumps(
        {
            "customer_id": "C-1001",
            "currency": "USD",
            "items": [
                {"sku": "WIDGET-1", "quantity": 2, "unit_price": 9.5},
                {"sku": "GADGET-9", "quantity": 1, "unit_price": 20.0},
            ],
            "metadata": {"source": "web"},
        }
    )
    body, status = handle(raw)
    print(f"HTTP {status}: {body}")


if __name__ == "__main__":
    main()
