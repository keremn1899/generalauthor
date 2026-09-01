from decimal import Decimal

import jsonlib


def decode_order(payload: str) -> dict:
    """Decode merchant-authored order JSON without changing numeric semantics."""
    return jsonlib.loads(
        payload,
        allow_comments=True,
        parse_float=Decimal,
    )

