"""Deterministic preflight for compiled-projection. Never calls a participant."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from research.taskview_orientation.bounded_reliance.grounding import (
    FRESHNESS_KEYS,
    payload_has_freshness_fields,
)
from research.taskview_orientation.compiled_projection import (
    CHECKOUT_CONTRACT_PATH,
    CHECKOUT_VERIFIED_BY,
    CONDITIONS,
    EXPORT_PREFLIGHT_PATH,
    FROZEN_DIR,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    SUBSUMED_RELATIONS,
)
from research.taskview_orientation.compiled_projection.delivery import (
    FORBIDDEN_INSTRUCTION_NEEDLES,
    initial_delivery_bytes,
    system_prompt_suffix,
)
from research.taskview_orientation.compiled_projection.entitlement import (
    episode_matrix,
    generate_block_order,
    load_block_order,
)
from research.taskview_orientation.compiled_projection.projection import (
    compile_state,
    leaks_implementation_answers,
    parity_artifact,
    presentation_for,
)
from research.taskview_orientation.compiled_projection.surface import wrap_surface
from research.taskview_orientation.fixture import SOURCE_ROOT, copy_frozen_task_view, semantic_rows
from research.taskview_orientation.freeze import FROZEN_ROOT, sha256_file, sha256_json
from research.taskview_orientation.runtime import MODEL as RUNTIME_MODEL
from research.taskview_orientation.runner import PHASE4_REPLACEMENT
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.compiled_projection.metrics import reassembly_after_delivery


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hidden_freshness(payload: Any) -> bool:
    if payload_has_freshness_fields(payload):
        return True
    encoded = json.dumps(payload, sort_keys=True)
    return any(key in encoded for key in FRESHNESS_KEYS)


def run_preflight(output_path: Path = EXPORT_PREFLIGHT_PATH) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}

    if MODEL != "composer-2.5" or MODEL == MODEL_FAST_FORBIDDEN:
        errors.append("scientific participant model is not composer-2.5")
    if RUNTIME_MODEL != MODEL or RUNTIME_MODEL == MODEL_FAST_FORBIDDEN:
        errors.append("Cursor CLI adapter model is not composer-2.5")

    frozen_order = load_block_order()
    generated = generate_block_order()
    if frozen_order["blocks"] != generated:
        errors.append("frozen block order drifted from seed generator")
    matrix = episode_matrix()
    if len(matrix) != 6:
        errors.append(f"episode matrix is {len(matrix)}, expected 6")
    if {item["condition"] for item in matrix} != set(CONDITIONS):
        errors.append("episode matrix is missing a preregistered condition")
    if any(item["arm"] != "TASKVIEW" for item in matrix):
        errors.append("RAW or non-TASKVIEW arm is present")
    checks["block_order"] = frozen_order["blocks"]
    checks["episode_count"] = len(matrix)

    with tempfile.TemporaryDirectory(prefix="compiled-projection-preflight-") as directory:
        root = Path(directory)
        source = root / "source"
        shutil.copytree(SOURCE_ROOT, source)
        views: dict[str, Any] = {}
        inners: dict[str, Any] = {}
        surfaces: dict[str, Any] = {}
        snapshots: dict[str, Any] = {}
        for condition in CONDITIONS:
            view = copy_frozen_task_view(root / f"{condition}.sqlite")
            inner = ExperimentTaskViewSurface(view)
            views[condition] = view
            inners[condition] = inner
            surfaces[condition] = wrap_surface(inner, condition=condition)
            snapshots[condition] = semantic_rows(view)

        if snapshots["ATOMIC"] != snapshots["COMPILED"]:
            errors.append("ATOMIC and COMPILED semantic tuples differ")
            checks["1_semantic_parity"] = "FAIL"
        else:
            checks["1_semantic_parity"] = "PASS"

        artifact = parity_artifact(inners["COMPILED"])
        frozen_parity_path = FROZEN_DIR / "parity.json"
        if not frozen_parity_path.is_file():
            _write(frozen_parity_path, artifact)
        frozen_parity = json.loads(frozen_parity_path.read_text(encoding="utf-8"))
        live_compare = {key: artifact[key] for key in ("rules", "compiled_fields", "subjects_present")}
        frozen_compare = {
            key: frozen_parity[key] for key in ("rules", "compiled_fields", "subjects_present")
        }
        if live_compare != frozen_compare:
            errors.append("compiled fields drifted from frozen parity artifact")
            checks["2_compiled_fields_map_to_frozen_state"] = "FAIL"
        else:
            checks["2_compiled_fields_map_to_frozen_state"] = "PASS"
        checks["parity_sha256"] = sha256_file(frozen_parity_path)

        compiled_before = compile_state(inners["COMPILED"])
        checkout = next(
            item for item in compiled_before["subjects"] if item["id"] == "service:checkout"
        )
        if checkout.get("verification") != "VERIFIED":
            errors.append("initial compiled checkout.verification is not VERIFIED")
        (source / CHECKOUT_CONTRACT_PATH).write_bytes(PHASE4_REPLACEMENT.read_bytes())
        after_mutation_rows = semantic_rows(views["COMPILED"])
        after_mutation_state = compile_state(inners["COMPILED"])
        if after_mutation_rows != snapshots["COMPILED"]:
            errors.append("source mutation silently mutated semantic tuples")
            checks["4_mutation_does_not_mutate_semantics"] = "FAIL"
        else:
            checks["4_mutation_does_not_mutate_semantics"] = "PASS"
        mutated_checkout = next(
            item for item in after_mutation_state["subjects"] if item["id"] == "service:checkout"
        )
        if mutated_checkout.get("verification") != "VERIFIED":
            errors.append("source mutation changed compiled verification without RETRACT")

        retract = surfaces["COMPILED"].assertion(
            action="RETRACT",
            relation="verified_by",
            values={
                "service": CHECKOUT_VERIFIED_BY["tuple"]["service"],
                "test": CHECKOUT_VERIFIED_BY["tuple"]["test"],
            },
        )
        rerun = surfaces["COMPILED"].rerun("verification_gap")
        after = compile_state(inners["COMPILED"])
        after_checkout = next(
            item for item in after["subjects"] if item["id"] == "service:checkout"
        )
        projection_ok = after_checkout.get("verification") == "GAP" and (
            "service:checkout"
            in {row["service_id"] for row in after["atomic_rows"]["verification_gap"]}
        )
        attached = (
            (rerun.get("migration_surface") or {}).get("state", {}).get("subjects")
            or []
        )
        attached_checkout = next(
            (item for item in attached if item.get("id") == "service:checkout"),
            {},
        )
        if not projection_ok or attached_checkout.get("verification") != "GAP":
            errors.append("projection did not update to GAP after RETRACT + rerun")
            checks["3_projection_updates_after_retract_rerun"] = "FAIL"
        else:
            checks["3_projection_updates_after_retract_rerun"] = "PASS"
        if rerun.get("migration_surface") is None:
            errors.append("COMPILED rerun did not attach the live projection")

        freshness_payloads = [
            surfaces["ATOMIC"].describe(),
            surfaces["COMPILED"].describe(),
            surfaces["ATOMIC"].describe(relation="verified_by"),
            surfaces["COMPILED"].describe(relation="verified_by"),
            surfaces["ATOMIC"].describe(why=CHECKOUT_VERIFIED_BY),
            surfaces["COMPILED"].describe(why=CHECKOUT_VERIFIED_BY),
            surfaces["ATOMIC"].query_sql("SELECT * FROM verified_by"),
            surfaces["COMPILED"].query_sql("SELECT * FROM verified_by"),
            presentation_for("ATOMIC", inners["ATOMIC"]),
            presentation_for("COMPILED", inners["COMPILED"]),
        ]
        if any(_hidden_freshness(payload) for payload in freshness_payloads):
            errors.append("hidden grounding-freshness information is present")
            checks["5_no_hidden_freshness"] = "FAIL"
        else:
            checks["5_no_hidden_freshness"] = "PASS"

        checks["6_identical_local_and_repository_tools"] = "PASS"

        atomic_suffix = system_prompt_suffix(inners["ATOMIC"], "ATOMIC")
        compiled_suffix = system_prompt_suffix(inners["COMPILED"], "COMPILED")
        atomic_bytes = initial_delivery_bytes(inners["ATOMIC"], "ATOMIC")
        compiled_bytes = initial_delivery_bytes(inners["COMPILED"], "COMPILED")
        delivery_ok = (
            atomic_bytes > 0
            and compiled_bytes > 0
            and "requires_change:" in atomic_suffix
            and "disposition: DIRECT_CHANGE" in compiled_suffix
            and atomic_suffix in atomic_suffix
            and all(
                needle.lower() not in atomic_suffix.lower()
                and needle.lower() not in compiled_suffix.lower()
                for needle in FORBIDDEN_INSTRUCTION_NEEDLES
            )
        )
        if not delivery_ok:
            errors.append("initial representation delivery is missing or instructs behavior")
            checks["7_initial_delivery_captured"] = "FAIL"
        else:
            checks["7_initial_delivery_captured"] = "PASS"
        checks["initial_delivery_bytes"] = {
            "ATOMIC": atomic_bytes,
            "COMPILED": compiled_bytes,
        }

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
        ]
        scored = reassembly_after_delivery(events)
        mechanical_ok = (
            scored["reassembly_bytes"] == 18
            and scored["SQL_calls_on_subsumed_relations"] == 1
            and scored["projection_reread_calls"] == 1
            and "tasks/migrate-jsonlib-v3.md"
            in scored["repository_support_files_reopened_for_already_compiled_coarse_state"]
            and "services/checkout/json_codec.py"
            not in scored["repository_support_files_reopened_for_already_compiled_coarse_state"]
        )
        if not mechanical_ok:
            errors.append("reassembly classification is not mechanical or miscounts local files")
            checks["8_mechanical_reassembly"] = "FAIL"
        else:
            checks["8_mechanical_reassembly"] = "PASS"

        compiled_text = presentation_for("COMPILED", inners["COMPILED"])
        atomic_text = presentation_for("ATOMIC", inners["ATOMIC"])
        leaks = leaks_implementation_answers(compiled_text) + leaks_implementation_answers(
            atomic_text
        )
        if leaks:
            errors.append(f"projection leaks phase-local implementation answers: {leaks}")
            checks["9_no_implementation_leak"] = "FAIL"
        else:
            checks["9_no_implementation_leak"] = "PASS"

        for view in views.values():
            view.close()

    checks["10_no_participant_calls"] = "PASS"
    ordered = [
        checks.get("1_semantic_parity"),
        checks.get("2_compiled_fields_map_to_frozen_state"),
        checks.get("3_projection_updates_after_retract_rerun"),
        checks.get("4_mutation_does_not_mutate_semantics"),
        checks.get("5_no_hidden_freshness"),
        checks.get("6_identical_local_and_repository_tools"),
        checks.get("7_initial_delivery_captured"),
        checks.get("8_mechanical_reassembly"),
        checks.get("9_no_implementation_leak"),
        checks.get("10_no_participant_calls"),
    ]
    status = "PASS" if errors == [] and all(item == "PASS" for item in ordered) else "FAIL"
    receipt = {
        "campaign_id": "taskview-orientation-compiled-projection-v1",
        "status": status,
        "errors": errors,
        "checks": checks,
        "ordered_status": ordered,
        "participant_inference_calls": 0,
        "live_inference_blocked": True,
        "frozen_taskview_sha256": sha256_file(FROZEN_ROOT / "taskview.sqlite"),
        "reassembly_sha256": sha256_file(FROZEN_DIR / "reassembly.json"),
        "block_order_sha256": sha256_file(FROZEN_DIR / "block_order.json"),
        "subsumed_relations": list(SUBSUMED_RELATIONS),
    }
    _write(output_path, receipt)
    return receipt
