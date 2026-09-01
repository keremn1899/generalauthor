from services.checkout.json_codec import decode_order


def read_order(raw_payload: str) -> tuple[str, object]:
    order = decode_order(raw_payload)
    return order["id"], order["total"]

