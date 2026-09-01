import json


def export_event(event: dict) -> str:
    return json.dumps(event, sort_keys=True)

