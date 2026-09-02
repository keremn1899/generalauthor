from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from research.taskview_orientation.fixture import (
    FROZEN_DB_PATH,
    FROZEN_ROOT,
    LEDGER_PATH,
    SOURCE_ROOT,
    VIEW_ID,
    build_task_view,
    copy_frozen_task_view,
    semantic_rows,
)
from research.taskview_orientation.freeze import sha256_file, source_manifest
from research.taskview_orientation.runner import EpisodeRunner, scripted_session_factory
from research.taskview_orientation.runtime_sdk import CursorSdkParticipantSession
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import FrozenSpanClassifier
from research.taskview_orientation.tools import EpisodeTools
from research.taskview_orientation.v01_manifest import (
    ORIGINAL_MANIFEST_PATH,
    V01_MANIFEST_PATH,
    V01_SIDECAR_PATH,
)
from research.taskview_orientation.v01_authorize import (
    AUTHORIZED_MANIFEST_PATH,
    AUTHORIZED_SIDECAR_PATH,
    LINEAGE_NOTE_PATH,
)
from research.taskview_orientation.v01_runtime_manifest import RUNTIME_MANIFEST_PATH
from research.taskview_orientation.v01_preflight import run_preflight
from research.taskview_orientation.telemetry import TelemetryRecorder
from taskview import TaskViewError


def _json(name: str):
    return json.loads((FROZEN_ROOT / name).read_text(encoding="utf-8"))


def _tree_hash(root: Path) -> str:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        records.append(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def test_source_snapshot_and_phase4_hashes_are_frozen():
    expected = _json("source_manifest.json")
    actual = source_manifest()
    assert actual == expected
    manifest = _json("experiment_manifest.json")
    assert actual["file_count"] == 34
    assert 25 <= actual["file_count"] <= 35
    assert manifest["source_snapshot"]["tree_sha256"] == actual["tree_sha256"]
    assert manifest["phase4_replacement_sha256"] == sha256_file(
        FROZEN_ROOT / "phase4/tests/checkout_contract.py"
    )


def test_every_grounding_path_span_and_hash_resolves_for_raw():
    ledger = _json("grounding_ledger.json")
    assert ledger["record_count"] == 21
    assert ledger["all_raw_obtainable"] is True
    for record in ledger["records"]:
        assert record["raw_obtainable"] is True
        assert record["review_status"] == "PASS_TWO_METHODS"
        for evidence in record["evidence"]:
            source = SOURCE_ROOT / evidence["path"]
            assert source.is_file()
            assert sha256_file(source) == evidence["source_sha256"]
            lines = source.read_text(encoding="utf-8").splitlines()
            assert 1 <= evidence["start_line"] <= evidence["end_line"] <= len(lines)


def test_two_parity_methods_and_derived_review_pass():
    review = _json("parity_review.json")
    assert review["status"] == "PASS"
    assert [item["reviewer"] for item in review["independent_method_passes"]] == [
        "review-a-ledger-first",
        "review-b-source-first",
    ]
    assert all(item["status"] == "PASS" for item in review["independent_method_passes"])
    assert review["derived_review"]["status"] == "PASS"
    assert review["disagreements"] == []


def test_frozen_database_matches_a_fresh_ledger_build(tmp_path):
    fresh = build_task_view(tmp_path / "fresh.sqlite", ledger_path=LEDGER_PATH)
    frozen = copy_frozen_task_view(tmp_path / "frozen.sqlite")
    assert semantic_rows(fresh) == semantic_rows(frozen)
    assert fresh.describe()["view"] == frozen.describe()["view"]
    fresh.close()
    frozen.close()


def test_initial_gap_is_current_complete_and_exhaustively_empty(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    assert view.query("SELECT service_id FROM verification_gap") == []
    receipt = view.latest_completeness("verification_gap")
    assert receipt["status"] == "COMPLETE"
    assert receipt["universe_relation"] == "affected_service"
    assert view.completeness_state("verification_gap") == "CURRENT"
    assert view.absence_is_exhaustive("verification_gap") is True
    view.close()


def test_retraction_stales_gap_and_contract_rerun_restores_current_complete(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    surface = ExperimentTaskViewSurface(view)
    surface.assertion(
        action="RETRACT",
        relation="verified_by",
        values={"service": "service:checkout", "test": "test:checkout-contract"},
    )
    assert view.is_stale("verification_gap") is True
    assert view.completeness_state("verification_gap") == "STALE"
    assert view.absence_is_exhaustive("verification_gap") is False
    result = surface.rerun("verification_gap")
    assert result["completeness"]["status"] == "COMPLETE"
    assert result["completeness"]["universe"] == "affected_service"
    assert result["completeness"]["state"] == "CURRENT"
    assert surface.query_sql("SELECT service_id FROM verification_gap")["rows"] == [
        {"service_id": "service:checkout"}
    ]
    view.close()


@pytest.mark.parametrize("argument", ["status", "universe", "basis", "known_gaps"])
def test_participant_cannot_supply_completeness_claim(tmp_path, argument):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    surface = ExperimentTaskViewSurface(view)
    with pytest.raises(TaskViewError, match="fixture-owned"):
        surface.rerun("verification_gap", **{argument: "participant-value"})
    view.close()


def test_complete_rerun_rejects_an_incomplete_derived_universe(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    surface = ExperimentTaskViewSurface(view)
    view.retract_tuple("in_scope", {"subject": "service:checkout"})
    assert view.is_stale("affected_service") is True
    with pytest.raises(TaskViewError, match="universe.*not current and complete"):
        surface.rerun("verification_gap")
    view.close()


def test_taskview_only_leakage_input_contains_no_source_content_or_local_tokens():
    reviewer_input = _json("leakage_reviewer_input.json")
    audit = _json("leakage_audit.json")
    assert reviewer_input["source_contents_included"] is False
    assert audit["status"] == "PASS"
    assert audit["forbidden_local_tokens_found"] == []
    assert all(not field["reliably_recoverable"] for field in audit["local_fields"])


def test_corrected_prompts_preserve_orientation_and_phase5_temporal_order():
    prompts = _json("prompts.json")["phases"]
    phase2 = prompts[1]["prompt"]
    phase3 = prompts[2]["prompt"]
    phase5 = prompts[4]["prompt"]
    assert "reporting" not in phase2.casefold()
    assert "partner-gateway" not in phase3
    assert "external-worker" not in phase3
    assert "before introducing" in phase5
    assert "Do not insert" in phase5
    assert prompts[4]["answer_fields"][:2] == [
        "current_verification_gap",
        "proposed_replacement_verification",
    ]


def test_phase5_harness_rejects_hypothetical_verification_mutation(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    tools = EpisodeTools(
        source_root=SOURCE_ROOT,
        scratch_root=tmp_path / "scratch",
        telemetry=TelemetryRecorder(episode_id="test", arm="TASKVIEW", replicate=0),
        taskview=ExperimentTaskViewSurface(view),
    )
    tools.set_phase(5)
    with pytest.raises(TaskViewError, match="answer-only"):
        tools.assertion(
            action="ASSERT",
            relation="verified_by",
            values={"service": "service:checkout", "test": "test:checkout-contract"},
        )
    view.close()


def test_every_tool_method_emits_exactly_one_call_accounting_event(tmp_path):
    """Every EpisodeTools method must emit exactly one call-accounting event.

    The identity accounting adapter consumes the bridge request identity in
    live runs. This apparatus-level test separately preserves the historical
    fact that every method has one local marker: TOOL_CALL except for the
    frozen write_scratch method, whose sole marker is SCRATCH_WRITE.
    """
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    telemetry = TelemetryRecorder(episode_id="test", arm="TASKVIEW", replicate=0)
    tools = EpisodeTools(
        source_root=SOURCE_ROOT,
        scratch_root=tmp_path / "scratch",
        telemetry=telemetry,
        taskview=ExperimentTaskViewSurface(view),
    )
    tools.scratch_root.mkdir()
    tools.set_phase(1)

    tools.read_source("tasks/migrate-jsonlib-v3.md", 1, 2)
    tools.search_source("jsonlib", ".")
    tools.write_scratch("note.txt", "hello")
    tools.describe()
    tools.query_sql("SELECT service_id FROM affected_service")
    tools.assertion(
        action="RETRACT",
        relation="verified_by",
        values={"service": "service:checkout", "test": "test:checkout-contract"},
    )
    tools.rerun("verification_gap")

    accounting_types = frozenset({"TOOL_CALL", "SCRATCH_WRITE"})
    calls = [event for event in telemetry.events if event["event_type"] in accounting_types]
    assert [event["tool_name"] for event in calls] == [
        "read_source",
        "search_source",
        "write_scratch",
        "describe",
        "query_sql",
        "assertion",
        "rerun",
    ]
    view.close()


def test_primary_span_labels_are_frozen_and_non_overlapping():
    config = _json("span_classification.json")
    classifier = FrozenSpanClassifier(config)
    assert config["primary_frozen"] is True
    assert "never changes primary labels" in config["alternative_valid_local_policy"]
    for phase, phase_config in config["phases"].items():
        for span in phase_config["spans"]:
            source = (
                FROZEN_ROOT / "phase4" / span["path"]
                if span.get("source_version") == "phase4"
                else SOURCE_ROOT / span["path"]
            )
            assert source.is_file()
            lines = source.read_text(encoding="utf-8").splitlines()
            assert 1 <= span["start_line"] <= span["end_line"] <= len(lines)
            for line in range(span["start_line"], span["end_line"] + 1):
                assert classifier.classify_line(
                    phase=int(phase),
                    path=span["path"],
                    line=line,
                    source_version=span.get("source_version", "initial"),
                ) == span["label"]


def test_system_tables_remain_inaccessible(tmp_path):
    view = copy_frozen_task_view(tmp_path / "view.sqlite")
    surface = ExperimentTaskViewSurface(view)
    with pytest.raises(TaskViewError, match="query_sql rejected"):
        surface.query_sql("SELECT * FROM _tv_view")
    view.close()


def test_raw_and_taskview_runner_are_stateful_symmetric_and_fully_telemetered(tmp_path):
    runner = EpisodeRunner(session_factory=scripted_session_factory)
    raw = runner.run(arm="RAW", replicate=0, output_root=tmp_path / "raw")
    treatment = runner.run(
        arm="TASKVIEW", replicate=0, output_root=tmp_path / "taskview"
    )
    assert raw["turns"] == treatment["turns"] == 5
    assert all(score["all_fields_correct"] for score in raw["oracle_scores"])
    assert all(score["all_fields_correct"] for score in treatment["oracle_scores"])
    assert raw["phase4_replacement_sha256"] == treatment["phase4_replacement_sha256"]
    assert _tree_hash(tmp_path / "raw/source") == _tree_hash(tmp_path / "taskview/source")
    assert raw["participant_model_invoked"] is False
    assert treatment["participant_model_invoked"] is False

    for arm in ("raw", "taskview"):
        events = [
            json.loads(line)
            for line in (tmp_path / arm / "telemetry.jsonl").read_text().splitlines()
        ]
        starts = [event for event in events if event["event_type"] == "SESSION_START"]
        ends = [event for event in events if event["event_type"] == "SESSION_END"]
        mutations = [event for event in events if event["event_type"] == "HARNESS_MUTATION"]
        assert len(starts) == len(ends) == len(mutations) == 1
        assert starts[0]["session_id"] == ends[0]["session_id"]
        assert ends[0]["turns_committed"] == 5
        assert mutations[0]["boundary"] == "after_phase_3_commit_before_phase_4_prompt"
        assert mutations[0]["taskview_silently_repaired"] is False
        assert any(event["event_type"] == "SOURCE_READ" for event in events)
        assert all(
            "segments" in event and "model_visible_output_bytes" in event
            for event in events
            if event["event_type"] in {"SOURCE_READ", "SOURCE_SEARCH"}
        )

    assert raw["metrics"]["taskview_visible_bytes"] == 0
    assert treatment["metrics"]["taskview_visible_bytes"] > 0
    assert treatment["metrics"]["net_orientation_bytes"] == (
        treatment["metrics"]["O_post"]
        + treatment["metrics"]["taskview_post_bytes"]
    )
    for record in (raw, treatment):
        assert record["metrics"]["total_model_visible_bytes"] > 0
        assert record["metrics"]["source_read_calls"] > 0
        assert record["metrics"]["unique_files_read"]
        assert record["metrics"]["tool_calls_by_type"]
        assert record["metrics"]["participant_turn_wall_time_ms"] >= 0
    assert treatment["metrics"]["taskview_calls_by_operation"] == {
        "assertion": 1,
        "describe": 1,
        "query_sql": 5,
        "rerun": 1,
    }


def test_native_tool_schemas_are_identical_and_treatment_overhead_is_explicit():
    schemas = _json("tool_schemas.json")
    manifest = _json("experiment_manifest.json")
    assert manifest["tool_schema_hashes"]["native"] == manifest["tool_schema_hashes"]["raw_visible"]
    assert [tool["name"] for tool in schemas["native"]] == [
        "search_source",
        "read_source",
        "write_scratch",
    ]
    assert [tool["name"] for tool in schemas["taskview"]] == [
        "describe",
        "query_sql",
        "assertion",
        "rerun",
    ]
    assert _json("arm_contracts.json")["TASKVIEW"]["tool_descriptions_and_outputs_charged"] is True


def test_scripted_dry_run_receipt_exercises_both_arms_without_a_model():
    receipt = _json("dry_run_receipt.json")
    assert receipt["apparatus_only"] is True
    assert receipt["participant_model_invoked"] is False
    assert receipt["raw_taskview_sources_byte_identical"] is True
    for arm in ("RAW", "TASKVIEW"):
        assert receipt["arms"][arm]["turns"] == 5
        assert receipt["arms"][arm]["one_session"] is True
        assert receipt["arms"][arm]["phase4_mutation_count"] == 1
        assert receipt["arms"][arm]["all_oracle_fields_correct"] is True
    assert receipt["arms"]["RAW"]["metrics"]["taskview_visible_bytes"] == 0
    assert receipt["arms"]["TASKVIEW"]["metrics"]["taskview_visible_bytes"] > 0
    assert receipt["telemetry_examples"]["RAW"]
    assert receipt["telemetry_examples"]["TASKVIEW"]


def test_manifest_lineage_distinguishes_historical_v0_from_v01_repeat():
    original = _json("experiment_manifest.json")
    sealed_cursor = _json("experiment_manifest.next.json")
    v01 = json.loads(V01_MANIFEST_PATH.read_text(encoding="utf-8"))

    original_digest = sha256_file(ORIGINAL_MANIFEST_PATH)
    assert original_digest == "dad102dc40f5de4c780076d825e0f4100ff6a223413d1bd51060378017b64ae2"
    assert original["experiment_version"] == "taskview-orientation-v1"
    assert original["participant_execution_authorized"] is True
    assert original["apparatus_code_hashes"][
        "research/taskview_orientation/surface.py"
    ] == "c96c9befc821347398e93391773382c4db8d5f6dcb7750e2b24e76ccea6a6466"
    assert original["apparatus_code_hashes"][
        "research/taskview_orientation/tools.py"
    ] == "e492272d84ed6dd5754e3f32eed8006bd57f02f8a4d03ffd80280d2c712cd1cf"

    # The already-authorized Cursor v1 lineage is also historical and untouched.
    sealed_cursor_path = FROZEN_ROOT / "experiment_manifest.next.json"
    assert sha256_file(sealed_cursor_path) == "539432a26fd00bf8f311e5cecb91fc6335ca16c75526be168dfddc3c565ee14e"
    assert sealed_cursor["participant_execution_authorized"] is True

    v01_digest = sha256_file(V01_MANIFEST_PATH)
    assert v01_digest == "9d9adb6bf4a163ddf436392a4db3d9e24e9f527b02597684bedeb837fdf4ca61"
    assert V01_SIDECAR_PATH.read_text(encoding="utf-8").split()[0] == v01_digest
    assert v01["experiment_version"] == "taskview-orientation-v01-repeat"
    assert v01["status"] == "STAGE1_V01_REPEAT_AWAITING_FRESH_AUTHORIZATION"
    assert v01["participant_execution_authorized"] is False
    assert v01["fresh_authorization_required"] is True
    assert v01["lineage"]["parent_manifest_sha256"] == original_digest
    assert v01["lineage"]["historical_parent_immutable"] is True
    assert v01["surface_revision"]["surface_version"] == "0.1"
    assert v01["surface_revision"]["semantic_changes"] == []

    assert v01["all_frozen_input_hashes"] == original["all_frozen_input_hashes"]
    assert v01["source_snapshot"] == original["source_snapshot"]
    assert v01["phase4_replacement_sha256"] == original["phase4_replacement_sha256"]
    assert v01["prompt_hashes"] == original["prompt_hashes"]
    assert v01["oracle"] == original["oracle"]
    assert v01["span_classification"] == original["span_classification"]
    for relative, digest in v01["all_frozen_input_hashes"].items():
        assert sha256_file(FROZEN_ROOT / relative) == digest
    for section in ("taskview_runtime_hashes",):
        for relative, digest in v01[section].items():
            assert sha256_file(Path(relative)) == digest
    assert sha256_file(Path("research/taskview_orientation/runtime_sdk.py")) != (
        v01["runtime_code_hashes"]["research/taskview_orientation/runtime_sdk.py"]
    )


def test_v01_deterministic_preflight_passes_without_participant_calls():
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["participant_calls"] == 0
    assert result["surface_smoke"]["catalog_within_ceiling"] is True
    assert result["surface_smoke"]["completeness_guard"] == "PASS"
    assert result["telemetry_smoke"]["all_four_operations_seen"] is True
    assert result["telemetry_smoke"]["all_v01_describe_variants_seen"] is True


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01/campaign_invalid.json"
)
def test_v01_lineage_note_distinguishes_unavailable_attestation_from_retained_manifests():
    note = LINEAGE_NOTE_PATH.read_text(encoding="utf-8")
    assert "6e3f5498aaafa50da949857d3061525d2aa51afaa4e45a03b47b00af774c83e1" in note
    assert "attested historical reference only" in note
    assert "No fields are inferred" in note
    assert sha256_file(V01_MANIFEST_PATH) == (
        "9d9adb6bf4a163ddf436392a4db3d9e24e9f527b02597684bedeb837fdf4ca61"
    )
    assert sha256_file(RUNTIME_MANIFEST_PATH) == (
        "5a5126c2b044ac95fa1214413b9f371f9ff00b5a908f5e1fa90afbcfd83210cb"
    )
    assert AUTHORIZED_MANIFEST_PATH.exists()
    assert AUTHORIZED_SIDECAR_PATH.exists()
    assert sha256_file(AUTHORIZED_MANIFEST_PATH) == (
        AUTHORIZED_SIDECAR_PATH.read_text(encoding="utf-8").split()[0]
    )
    invalid = Path(
        "research/taskview_orientation/results/stage1-cursor-v01/campaign_invalid.json"
    )
    assert json.loads(invalid.read_text(encoding="utf-8"))["valid"] is False
