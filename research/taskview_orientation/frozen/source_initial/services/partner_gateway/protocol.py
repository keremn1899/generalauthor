import jsonlib


def encode_vendor_request(order: dict) -> bytes:
    signed_body = jsonlib.dumps(order, sort_keys=True).encode("utf-8")
    return b"signed_body=" + signed_body


WIRE_FIELD_REQUIRING_V2_BYTES = "signed_body"

