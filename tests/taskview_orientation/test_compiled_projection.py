from __future__ import annotations

import shutil

import pytest

from research.taskview_orientation.compiled_projection import (
    CHECKOUT_CONTRACT_PATH,
    CHECKOUT_VERIFIED_BY,
    CONDITIONS,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    PARTICIPANT_INFERENCE_AUTHORIZED,
    SEED,
    SUBSUMED_RELATIONS,
)
from research.taskview_orientation.compiled_projection.campaign import (
    LiveInferenceBlocked,
    run_campaign,
)
from research.taskview_orientation.compiled_projection.delivery import (
    initial_delivery_bytes,
    system_prompt_suffix,
)
from research.taskview_orientation.compiled_projection.entitlement import (
    episode_matrix,
    generate_block_order,
    load_block_order,
)
from research.taskview_orientation.compiled_projection.metrics import (
    reassembly_after_delivery,
)
from research.taskview_orientation.compiled_projection.preflight import run_preflight
from research.taskview_orientation.compiled_projection.projection import (
    compile_state,
    leaks_implementation_answers,
    presentation_for,
)
from research.taskview_orientation.compiled_projection.surface import wrap_surface
from research.taskview_orientation.fixture import SOURCE_ROOT, copy_frozen_task_view, semantic_rows
from research.taskview_orientation.runtime import MODEL as RUNTIME_MODEL
from research.taskview_orientation.runner import PHASE4_REPLACEMENT
from research.taskview_orientation.surface import ExperimentTaskViewSurface


def test_preregistered_block_order_matches_frozen_seed():
    frozen = load_block_order()
    assert frozen["seed"] == SEED
    assert generate_block_order() == frozen["blocks"]
    matrix = episode_matrix()
    assert len(matrix) == 6
    assert {item["condition"] for item in matrix} == set(CONDITIONS)
    assert all(item["arm"] == "TASKVIEW" for item in matrix)
    assert [item["condition"] for item in matrix[:2]] == frozen["blocks"]["1"]


def test_participant_is_composer_25_not_fast():
    assert MODEL == "composer-2.5"
    assert RUNTIME_MODEL == "composer-2.5"
    assert MODEL_FAST_FORBIDDEN == "composer-2.5-fast"
    assert PARTICIPANT_INFERENCE_AUTHORIZED is True


def test_live_inference_requires_authorized_manifest(monkeypatch, tmp_path):
    from research.taskview_orientation.compiled_projection import campaign as campaign_mod

    monkeypatch.setattr(campaign_mod, "AUTHORIZED_MANIFEST_PATH", tmp_path / "missing.json")
    with pytest.raises(LiveInferenceBlocked, match="authorized manifest is absent"):
        run_campaign(tmp_path / "results")


def test_compiled_contains_no_atomic_unavailable_information(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    inner = ExperimentTaskViewSurface(view)
    state = compile_state(inner)
    rows = semantic_rows(view)
    checkout = next(item for item in state["subjects"] if item["id"] == "service:checkout")
    reporting = next(item for item in state["subjects"] if item["id"] == "service:reporting")
    partner = next(item for item in state["subjects"] if item["id"] == "service:partner-gateway")
    worker = next(item for item in state["subjects"] if item["id"] == "service:external-worker")
    assert checkout["disposition"] == "DIRECT_CHANGE"
    assert {"service_id": "service:checkout"} in rows["requires_change"]
    assert reporting["disposition"] == "PROTECTED"
    assert reporting["protected_by"] == "adapter:reporting-json-v3"
    assert partner["disposition"] == "EXCLUDED_BOUNDARY"
    assert worker["disposition"] == "UNRESOLVED_SCOPE"
    assert checkout["verification"] == "VERIFIED"
    assert state["scope_receipt"]["whole_world"] == "NOT_COMPLETE"
    assert leaks_implementation_answers(presentation_for("COMPILED", inner)) == []
    view.close()


def test_mutation_does_not_change_projection_until_retract(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE_ROOT, source)
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    inner = ExperimentTaskViewSurface(view)
    compiled = wrap_surface(inner, condition="COMPILED")
    before = compile_state(inner)
    (source / CHECKOUT_CONTRACT_PATH).write_bytes(PHASE4_REPLACEMENT.read_bytes())
    assert compile_state(inner) == before
    compiled.assertion(
        action="RETRACT",
        relation="verified_by",
        values={
            "service": CHECKOUT_VERIFIED_BY["tuple"]["service"],
            "test": CHECKOUT_VERIFIED_BY["tuple"]["test"],
        },
    )
    compiled.rerun("verification_gap")
    after = compile_state(inner)
    checkout = next(item for item in after["subjects"] if item["id"] == "service:checkout")
    assert checkout["verification"] == "GAP"
    assert {"service_id": "service:checkout"} in after["atomic_rows"]["verification_gap"]
    view.close()


def test_atomic_and_compiled_share_tools_and_delivery_is_counted(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    inner = ExperimentTaskViewSurface(view)
    atomic = wrap_surface(inner, condition="ATOMIC")
    compiled = wrap_surface(
        ExperimentTaskViewSurface(copy_frozen_task_view(tmp_path / "compiled.sqlite")),
        condition="COMPILED",
    )
    assert atomic.query_sql("SELECT service_id FROM requires_change")["rows"] == [
        {"service_id": "service:checkout"}
    ]
    assert compiled.query_sql("SELECT service_id FROM requires_change")["rows"] == [
        {"service_id": "service:checkout"}
    ]
    atomic_text = system_prompt_suffix(inner, "ATOMIC")
    compiled_text = system_prompt_suffix(inner, "COMPILED")
    assert "requires_change:" in atomic_text
    assert "disposition: DIRECT_CHANGE" in compiled_text
    assert initial_delivery_bytes(inner, "ATOMIC") > 0
    assert initial_delivery_bytes(inner, "COMPILED") > 0
    assert "trust TaskView" not in atomic_text
    assert "minimize" not in compiled_text.lower()
    view.close()


def test_reassembly_is_mechanical_and_excludes_required_local_and_projection_reread():
    events = [
        {
            "sequence": 1,
            "phase": 1,
            "event_type": "TASKVIEW_TOOL",
            "taskview_operation": "query_sql",
            "tool_arguments": {"sql": "SELECT * FROM requires_change"},
            "model_visible_output_bytes": 11,
        },
        {
            "sequence": 2,
            "phase": 1,
            "event_type": "TASKVIEW_TOOL",
            "taskview_operation": "describe",
            "tool_arguments": {"relation": "migration_surface"},
            "model_visible_output_bytes": 99,
        },
        {
            "sequence": 3,
            "phase": 1,
            "event_type": "SOURCE_READ",
            "source_path": "services/checkout/json_codec.py",
            "model_visible_output_bytes": 50,
        },
        {
            "sequence": 4,
            "phase": 1,
            "event_type": "SOURCE_READ",
            "source_path": "tasks/migrate-jsonlib-v3.md",
            "model_visible_output_bytes": 7,
        },
        {
            "sequence": 5,
            "phase": 4,
            "event_type": "TASKVIEW_TOOL",
            "taskview_operation": "query_sql",
            "tool_arguments": {"sql": "SELECT * FROM verified_by"},
            "model_visible_output_bytes": 40,
        },
    ]
    scored = reassembly_after_delivery(events)
    assert scored["reassembly_bytes"] == 18
    assert scored["projection_reread_calls"] == 1
    assert scored["SQL_calls_on_subsumed_relations"] == 1
    assert set(SUBSUMED_RELATIONS)


def test_preflight_passes_without_participant_calls(tmp_path):
    receipt = run_preflight(tmp_path / "preflight.json")
    assert receipt["status"] == "PASS"
    assert receipt["errors"] == []
    assert receipt["participant_inference_calls"] == 0
    assert receipt["ordered_status"] == ["PASS"] * 10
