import json

from research.frontier_extension.execute_campaign import stream_events


def test_stream_events_ignores_timestamp_429_in_plain_event_text():
    raw = json.dumps({"type": "system", "subtype": "init", "timestamp": "2026-08-30T18:15:22.429Z"})
    _, _, quota, _ = stream_events(raw, "")
    assert quota is False


def test_stream_events_detects_explicit_status_429_error():
    raw = json.dumps({"type": "error", "status": 429, "message": "rate limit exceeded"})
    _, _, quota, _ = stream_events(raw, "")
    assert quota is True
