from jsonlib_v3 import Decoder


def decode_invoice(payload: str) -> dict:
    return Decoder(number_mode="float").decode(payload)

