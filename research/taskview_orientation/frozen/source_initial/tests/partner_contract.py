from services.partner_gateway.protocol import encode_vendor_request


def test_signed_body_uses_frozen_vendor_shape() -> None:
    assert encode_vendor_request({"id": "o-1"}).startswith(b"signed_body=")

