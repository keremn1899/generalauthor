from __future__ import annotations

from research.taskview_orientation.read_surface_replay.epistemic import (
    REQUIRED_LABELS,
    evaluate_safety,
)


def test_required_negative_vocabulary_is_covered():
    report = evaluate_safety()
    labels = {case["label"] for case in report["cases"].values()}
    assert set(REQUIRED_LABELS) <= labels | {"NO_MATCH_OBSERVED"}
    # INCOMPLETE empty is NO_MATCH_OBSERVED, not known absence.
    assert report["cases"]["current_complete_empty"]["label"] == "KNOWN_ABSENT_WITHIN_NAMED_UNIVERSE"
    assert report["cases"]["current_incomplete"]["label"] == "NO_MATCH_OBSERVED"
    assert report["cases"]["stale_complete_receipt"]["label"] == "STALE"
    assert report["cases"]["never_run"]["label"] == "NOT_YET_ESTABLISHED"
    assert report["cases"]["failed"]["label"] == "NOT_YET_ESTABLISHED"
    assert report["cases"]["outside_universe"]["label"] == "OUTSIDE_DECLARED_UNIVERSE"
    assert report["cases"]["membership_unknown"]["label"] == "UNIVERSE_MEMBERSHIP_UNKNOWN"


def test_conditional_read_does_not_collapse_stale_and_current():
    report = evaluate_safety()
    assert report["candidates"]["F"]["conditional_invalidation_ok"] is True
    collisions = [
        item
        for item in report["collisions"]
        if {item["left"], item["right"]} == {"stale_complete_receipt", "current_complete_empty"}
    ]
    assert collisions == []
