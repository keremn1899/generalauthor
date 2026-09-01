import json


def decode_search_document(payload: str) -> dict:
    return json.loads(payload)

