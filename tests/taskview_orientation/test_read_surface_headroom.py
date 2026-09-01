from __future__ import annotations

from research.taskview_orientation.read_surface_replay.candidates import replay_episode
from research.taskview_orientation.read_surface_replay.headroom import (
    BREAK_EVEN_SEARCH,
    MIN_MATCH_CHARS,
    ORACLE_REQUIRED_RELATIONS,
    HeadroomPolicy,
    classify_relation_describe,
    compact_epistemic_body,
    contributing_relations,
    load_phase_answers,
    replay_b_headroom,
    run_headroom,
    sql_supported_by_answer,
)
from research.taskview_orientation.read_surface_replay.ledger import build_campaign_ledger
from research.taskview_orientation.read_surface_replay.serialize import dumps


def test_answer_support_matches_short_oracle_names_in_r3_phase1():
    ledger = build_campaign_ledger()
    episode = next(item for item in ledger.episodes if item.replicate == 3)
    contributing = contributing_relations(episode)
    assert "requires_change" in contributing[1]
    answers = load_phase_answers(episode)
    assert "checkout" in dumps(answers[1]).lower() or "checkout" in str(answers[1]).lower()


def test_shared_identifier_overinclusion_is_mechanical_not_intent():
    ledger = build_campaign_ledger()
    episode = next(item for item in ledger.episodes if item.replicate == 1)
    contributing = contributing_relations(episode)
    # checkout appears in several relations; answer-support is not "rows needed".
    assert "requires_change" in contributing[1]
    assert MIN_MATCH_CHARS == 4


def test_base_current_describe_is_contract_redundant_derived_is_not():
    ledger = build_campaign_ledger()
    found = {"contract_redundant": False, "epistemic_bearing": False}
    for episode in ledger.episodes:
        for access in episode.accesses:
            if access.operation != "describe" or access.describe_kind != "relation":
                continue
            bucket = classify_relation_describe(access)
            if bucket in found:
                found[bucket] = True
            if bucket == "epistemic_bearing":
                body = compact_epistemic_body(access)
                assert "roles" not in body
                assert "meaning" not in body
                assert "description" not in body
                assert '"inputs"' not in body
                assert '"relation"' in body
    assert found["contract_redundant"]
    assert found["epistemic_bearing"]


def test_observed_headroom_matches_trajectory_preserving_b():
    ledger = build_campaign_ledger()
    report = run_headroom(ledger)
    assert report["observed_b_totals_match"] is True
    assert report["participant_inference_calls"] == 0
    for episode, anatomy in zip(ledger.episodes, report["anatomies"]):
        items = replay_episode(episode, "B", "trajectory_preserving")
        assert anatomy["observed_acq"] == sum(item.total for item in items)
        observed = replay_b_headroom(
            episode,
            HeadroomPolicy(
                describe="full", sql="full", speculative_keep=1.0, conservative=False
            ),
        )
        assert sum(item.total for item in observed) == anatomy["observed_acq"]


def test_r4_fixed_overhead_exceeds_budget():
    ledger = build_campaign_ledger()
    report = run_headroom(ledger)
    r4 = next(item for item in report["anatomies"] if item["replicate"] == 4)
    assert r4["fixed_overhead_exceeds_budget"] is True
    floor = report["scenarios"]["fixed_overhead_only"]
    assert floor["R4"] > 0
    be = next(item for item in report["break_even"] if item["replicate"] == 4)
    assert be["possible"] is False


def test_break_even_search_order_is_frozen():
    assert BREAK_EVEN_SEARCH[0] == "drop_contract_redundant_describe"
    assert BREAK_EVEN_SEARCH[-1] == "fixed_overhead_only"
    assert 1 in ORACLE_REQUIRED_RELATIONS
    assert "requires_change" in ORACLE_REQUIRED_RELATIONS[1]


def test_sql_supported_by_answer_ignores_citations_only():
    class _SQL:
        relation = "requires_change"

    class _Access:
        sql = _SQL()
        is_error = False
        returned_rows = [{"service_id": "service:checkout"}]

    from research.taskview_orientation.read_surface_replay.headroom import answer_blob

    blob_without = answer_blob({"direct_change_services": ["checkout"], "citations": []})
    blob_citations_only = answer_blob(
        {"citations": [["services/checkout/json_codec.py", 6, 12]]}
    )
    assert sql_supported_by_answer(_Access(), blob_without) is True
    assert sql_supported_by_answer(_Access(), blob_citations_only) is False
