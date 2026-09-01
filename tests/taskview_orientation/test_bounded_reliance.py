from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from research.taskview_orientation.bounded_reliance import (
    CAMPAIGN_ID,
    CHECKOUT_CONTRACT_PATH,
    CHECKOUT_VERIFIED_BY,
    CONDITIONS,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    PARTICIPANT_INFERENCE_AUTHORIZED,
    REPORTING_VERIFIED_BY,
    SEED,
    TASKVIEW_CONDITIONS,
)
from research.taskview_orientation.bounded_reliance.campaign import (
    LiveInferenceBlocked,
)
from research.taskview_orientation.bounded_reliance.contracts import (
    experimental_sections,
    stable_contract_text,
    vocabulary_lines,
)
from research.taskview_orientation.bounded_reliance.entitlement import (
    episode_matrix,
    generate_block_order,
    load_block_order,
)
from research.taskview_orientation.bounded_reliance.grounding import (
    CHANGED,
    FRESH,
    payload_has_freshness_fields,
    receipt_for_reference,
)
from research.taskview_orientation.bounded_reliance.metrics import (
    reconstruction_after_entitlement,
    sql_relations,
)
from research.taskview_orientation.bounded_reliance.preflight import run_preflight
from research.taskview_orientation.bounded_reliance.surface import wrap_surface
from research.taskview_orientation.fixture import SOURCE_ROOT, copy_frozen_task_view
from research.taskview_orientation.runtime import MODEL as RUNTIME_MODEL
from research.taskview_orientation.runner import (
    PHASE4_REPLACEMENT,
    EpisodeRunner,
    scripted_session_factory,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface


def test_preregistered_block_order_matches_frozen_seed():
    frozen = load_block_order()
    assert frozen["seed"] == SEED
    assert generate_block_order() == frozen["blocks"]
    matrix = episode_matrix()
    assert len(matrix) == 20
    assert [item["condition"] for item in matrix[:5]] == frozen["blocks"]["1"]
    assert {item["condition"] for item in matrix} == set(CONDITIONS)
    assert sum(item["arm"] == "RAW" for item in matrix) == 4
    assert sum(item["arm"] == "TASKVIEW" for item in matrix) == 16


def test_participant_is_composer_25_not_fast():
    assert MODEL == "composer-2.5"
    assert RUNTIME_MODEL == "composer-2.5"
    assert MODEL_FAST_FORBIDDEN == "composer-2.5-fast"
    assert "fast" not in MODEL
    assert PARTICIPANT_INFERENCE_AUTHORIZED is True


def test_grounding_receipts_are_file_digests_and_do_not_retract(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE_ROOT, source)
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    inner = ExperimentTaskViewSurface(view)
    t01 = wrap_surface(inner, condition="T01", source_root=source)
    t00 = wrap_surface(
        ExperimentTaskViewSurface(copy_frozen_task_view(tmp_path / "t00.sqlite")),
        condition="T00",
        source_root=source,
    )
    before = t01.describe(why=CHECKOUT_VERIFIED_BY)
    assert before["why"]["grounding_state"] == FRESH
    assert not payload_has_freshness_fields(t00.describe(why=CHECKOUT_VERIFIED_BY))
    sql_before = t01.query_sql("SELECT * FROM verified_by")
    (source / CHECKOUT_CONTRACT_PATH).write_bytes(PHASE4_REPLACEMENT.read_bytes())
    after = t01.describe(why=CHECKOUT_VERIFIED_BY)
    reporting = t01.describe(why=REPORTING_VERIFIED_BY)
    assert after["why"]["grounding_state"] == CHANGED
    assert reporting["why"]["grounding_state"] == FRESH
    assert t01.query_sql("SELECT * FROM verified_by") == sql_before
    assert not payload_has_freshness_fields(sql_before)
    t00_after = t00.describe(why=CHECKOUT_VERIFIED_BY)
    assert not payload_has_freshness_fields(t00_after)
    view.close()


def test_unrelated_file_change_does_not_invalidate_checkout_grounding(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE_ROOT, source)
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    surface = wrap_surface(
        ExperimentTaskViewSurface(view), condition="T11", source_root=source
    )
    adapter = source / "services/reporting/json_adapter.py"
    adapter.write_bytes(adapter.read_bytes() + b"\n# unrelated\n")
    checkout = surface.describe(why=CHECKOUT_VERIFIED_BY)
    reporting = surface.describe(why=REPORTING_VERIFIED_BY)
    assert checkout["why"]["grounding_state"] == FRESH
    assert reporting["why"]["grounding_state"] == CHANGED
    view.close()


def test_stable_vocabulary_identical_except_experimental_sections(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    inner = ExperimentTaskViewSurface(view)
    vocab = vocabulary_lines(inner)
    texts = {
        condition: stable_contract_text(inner, condition)
        for condition in TASKVIEW_CONDITIONS
    }
    assert experimental_sections("T00") == []
    assert "CURRENT means consistent" in texts["T10"]
    assert "grounding_state FRESH" in texts["T01"]
    assert "relevant grounding is FRESH" in texts["T11"]
    assert "Source inspection remains available" in texts["T10"]
    for condition in TASKVIEW_CONDITIONS:
        for line in vocab:
            assert line in texts[condition]
    view.close()


def test_reconstruction_after_entitlement_is_mechanical():
    events = [
        {
            "sequence": 1,
            "phase": 1,
            "event_type": "TASKVIEW_TOOL",
            "taskview_operation": "query_sql",
            "tool_arguments": {"sql": "SELECT service_id FROM requires_change"},
            "model_visible_output_bytes": 10,
        },
        {
            "sequence": 2,
            "phase": 1,
            "event_type": "TASKVIEW_TOOL",
            "taskview_operation": "describe",
            "tool_arguments": {"relation": None, "why": None},
            "model_visible_output_bytes": 50,
        },
        {
            "sequence": 3,
            "phase": 1,
            "event_type": "SOURCE_READ",
            "source_path": "tasks/migrate-jsonlib-v3.md",
            "tool_arguments": {"path": "tasks/migrate-jsonlib-v3.md"},
            "model_visible_output_bytes": 20,
        },
        {
            "sequence": 4,
            "phase": 1,
            "event_type": "SOURCE_READ",
            "source_path": "services/checkout/json_codec.py",
            "tool_arguments": {"path": "services/checkout/json_codec.py"},
            "model_visible_output_bytes": 99,
        },
    ]
    result = reconstruction_after_entitlement(events)
    phase1 = result["phases"]["1"]
    assert phase1["t_entitled_sequence"] == 1
    assert phase1["reproof_calls"] == 2
    assert phase1["reproof_bytes"] == 70
    assert "catalog" in phase1["reproof_distinct_relations"]
    assert "tasks/migrate-jsonlib-v3.md" in phase1["reproof_repository_files"]
    assert "services/checkout/json_codec.py" not in phase1["reproof_repository_files"]


def test_sql_relations_include_joins():
    assert sql_relations(
        "SELECT a.service_id, p.adapter_id FROM affected_service a "
        "JOIN protected_by p ON p.service_id = a.service_id"
    ) == {"affected_service", "protected_by"}


def test_scripted_t01_episode_preserves_v01_oracle_and_does_not_call_a_model(tmp_path):
    runner = EpisodeRunner(session_factory=scripted_session_factory)
    record = runner.run(
        arm="TASKVIEW",
        replicate=0,
        output_root=tmp_path / "t01",
        condition="T01",
        system_prompt_suffix="experimental suffix",
    )
    assert record["condition"] == "T01"
    assert record["participant_model_invoked"] is False
    assert all(score["all_fields_correct"] for score in record["oracle_scores"])


def test_live_campaign_requires_authorized_manifest(tmp_path, monkeypatch):
    from research.taskview_orientation.bounded_reliance import campaign as campaign_mod

    monkeypatch.setattr(campaign_mod, "AUTHORIZED_MANIFEST_PATH", tmp_path / "missing.json")
    with pytest.raises(LiveInferenceBlocked, match="authorized manifest is absent"):
        campaign_mod._load_manifest()


def test_deterministic_preflight_passes_without_participant_calls(tmp_path):
    result = run_preflight(tmp_path / "preflight.json")
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["participant_inference_calls"] == 0
    assert result["live_inference_blocked"] is True
    assert result["ordered_status"] == ["PASS"] * 12
    assert result["campaign_id"] == CAMPAIGN_ID


def test_receipt_for_missing_file_is_unknown(tmp_path):
    receipt = receipt_for_reference("source://missing.py#L1-L2@sha256:abc", tmp_path)
    assert receipt["grounding_state"] == "UNKNOWN"
