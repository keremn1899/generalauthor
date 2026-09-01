from decimal import Decimal

from services.checkout.json_codec import decode_order


def test_commented_decimal_order_is_preserved() -> None:
    order = decode_order('{/* merchant promotion */"id":"o-1","total":10.50}')
    assert order["id"] == "o-1"
    assert order["total"] == Decimal("10.50")

