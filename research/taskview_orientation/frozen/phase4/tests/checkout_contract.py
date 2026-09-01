from services.checkout.json_codec import decode_order


def test_order_smoke_case() -> None:
    order = decode_order('{"id":"o-1","total":10.5}')
    assert order["id"] == "o-1"

