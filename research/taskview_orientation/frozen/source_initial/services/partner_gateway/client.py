from services.partner_gateway.protocol import encode_vendor_request


def send_order(order: dict, transport) -> None:
    transport.post("/vendor/orders", body=encode_vendor_request(order))

