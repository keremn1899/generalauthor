from __future__ import annotations

import json

import pytest

from research.taskview_orientation.freeze import sha256_file
from research.taskview_orientation.read_surface_replay import (
    EXPECTED_SQL_FACTS,
    SEALED_RESULTS_ROOT,
)
from research.taskview_orientation.read_surface_replay.candidates import replay_episode
from research.taskview_orientation.read_surface_replay.epistemic import evaluate_safety
from research.taskview_orientation.read_surface_replay.ledger import build_campaign_ledger
from research.taskview_orientation.read_surface_replay.serialize import (
    dumps,
    serializer_hash,
)
from research.taskview_orientation.read_surface_replay.sql_parse import (
    classify_sql_corpus,
    parse_sql,
)


SEAL = SEALED_RESULTS_ROOT / "campaign_seal.json"
PROGRESS = SEALED_RESULTS_ROOT / "campaign_progress.json"
requires_sealed_campaign = pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01-v4-searchfix/campaign_seal.json"
)


def test_sql_parse_shapes_and_escape():
    plain = parse_sql("SELECT * FROM requires_change")
    assert plain.shape == "PLAIN"
    assert plain.simple_kind == "enumeration"
    filtered = parse_sql("SELECT * FROM verified_by WHERE service_id = 'service:checkout'")
    assert filtered.shape == "FILTER"
    assert filtered.simple_kind == "equality_get"
    like = parse_sql("SELECT * FROM verified_by WHERE service_id LIKE '%checkout%'")
    assert like.shape == "FILTER"
    assert like.simple_kind == "select"
    ordered = parse_sql("SELECT * FROM verification_gap ORDER BY service_id")
    assert ordered.shape == "ORDER/LIMIT"
    limited = parse_sql("SELECT * FROM requires_change LIMIT 20")
    assert limited.shape == "ORDER/LIMIT"
    join = parse_sql("SELECT * FROM a JOIN b ON a.id = b.id")
    assert join.has_join
    assert join.sql_escape_required


def test_serializer_hash_is_frozen_and_utf8_pretty():
    digest = serializer_hash()
    assert digest["serializer_id"] == "taskview-read-surface-replay-serializers-v1"
    assert len(digest["config_sha256"]) == 64
    body = dumps({"rows": [{"service_id": "service:checkout"}], "row_count": 1})
    assert body.encode("utf-8")
    assert "\n  " in body
    assert body.index("rows") < body.index("row_count")


def test_epistemic_states_are_pairwise_distinguishable():
    report = evaluate_safety()
    assert report["all_safe"] is True
    for candidate, payload in report["candidates"].items():
        assert payload["safe"] is True, (candidate, payload["collisions"])
    assert report["candidates"]["F"]["conditional_invalidation_ok"] is True


@requires_sealed_campaign
def test_sealed_campaign_hashes_are_unchanged():
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    assert seal["status"] == "SEALED"
    assert seal["valid"] is True
    assert sha256_file(PROGRESS) == seal["campaign_progress_sha256"]
    for episode_id, digest in seal["episode_seals"].items():
        assert sha256_file(SEALED_RESULTS_ROOT / episode_id / "seal.json") == digest


@requires_sealed_campaign
def test_ledger_sql_facts_match_preregistered_111():
    ledger = build_campaign_ledger()
    comparable = {key: ledger.sql_facts[key] for key in EXPECTED_SQL_FACTS}
    assert comparable == EXPECTED_SQL_FACTS
    assert len(ledger.episodes) == 4
    assert all(episode.reconstruction_ok for episode in ledger.episodes)
    assert sum(episode.accesses and True for episode in ledger.episodes) == 4


@requires_sealed_campaign
def test_candidate_c_holds_sql_row_bytes_fixed_against_b():
    ledger = build_campaign_ledger()
    episode = ledger.episodes[0]
    b_items = replay_episode(episode, "B", "trajectory_preserving")
    c_items = replay_episode(episode, "C", "trajectory_preserving")
    b_rows = [item for item in b_items if item.kind == "rows"]
    c_rows = [item for item in c_items if item.kind == "rows"]
    assert [item.body for item in b_rows] == [item.body for item in c_rows]


@requires_sealed_campaign
def test_participant_inference_remains_zero_constant():
    from research.taskview_orientation.read_surface_replay.accounting import run_accounting

    ledger = build_campaign_ledger()
    result = run_accounting(ledger)
    assert result["participant_inference_calls"] == 0
