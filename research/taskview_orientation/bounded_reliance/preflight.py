"""Deterministic preflight for bounded-reliance / grounding-freshness.

Any failed check blocks live inference. This module never calls a participant.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from research.taskview_orientation.bounded_reliance import (
    CHECKOUT_CONTRACT_PATH,
    CHECKOUT_VERIFIED_BY,
    CONDITIONS,
    EXPORT_PREFLIGHT_PATH,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    REPORTING_VERIFIED_BY,
    TASKVIEW_CONDITIONS,
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
    FRESHNESS_KEYS,
    payload_has_freshness_fields,
)
from research.taskview_orientation.bounded_reliance.surface import wrap_surface
from research.taskview_orientation.fixture import (
    DERIVATIONS,
    SOURCE_ROOT,
    copy_frozen_task_view,
    semantic_rows,
)
from research.taskview_orientation.freeze import FROZEN_ROOT, sha256_file, sha256_json
from research.taskview_orientation.runtime import MODEL as RUNTIME_MODEL
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.runner import PHASE4_REPLACEMENT


UNRELATED_SOURCE = "services/reporting/json_adapter.py"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _describe_why(surface: ExperimentTaskViewSurface, spec: dict[str, Any]) -> dict[str, Any]:
    return surface.describe(why=spec)


def _derived_rows(view) -> dict[str, list[dict[str, Any]]]:
    rows = semantic_rows(view)
    return {name: rows[name] for name in DERIVATIONS}


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
    if len(matrix) != 20:
        errors.append(f"episode matrix is {len(matrix)}, expected 20")
    if {item["condition"] for item in matrix} != set(CONDITIONS):
        errors.append("episode matrix is missing a preregistered condition")
    checks["block_order"] = frozen_order["blocks"]
    checks["episode_count"] = len(matrix)

    with tempfile.TemporaryDirectory(prefix="bounded-reliance-preflight-") as directory:
        root = Path(directory)
        source = root / "source"
        shutil.copytree(SOURCE_ROOT, source)
        surfaces: dict[str, Any] = {}
        views: dict[str, Any] = {}
        snapshots: dict[str, Any] = {}
        derived: dict[str, Any] = {}
        vocab: dict[str, list[str]] = {}
        contracts: dict[str, str] = {}
        for condition in TASKVIEW_CONDITIONS:
            view = copy_frozen_task_view(root / f"{condition}.sqlite")
            inner = ExperimentTaskViewSurface(view)
            surface = wrap_surface(inner, condition=condition, source_root=source)
            views[condition] = view
            surfaces[condition] = surface
            snapshots[condition] = semantic_rows(view)
            derived[condition] = _derived_rows(view)
            vocab[condition] = vocabulary_lines(inner)
            contracts[condition] = stable_contract_text(inner, condition)

        if len({sha256_json(snapshots[name]) for name in TASKVIEW_CONDITIONS}) != 1:
            errors.append("TaskView arms do not contain identical semantic tuples")
            checks["1_identical_semantic_tuples"] = "FAIL"
        else:
            checks["1_identical_semantic_tuples"] = "PASS"

        if len({sha256_json(derived[name]) for name in TASKVIEW_CONDITIONS}) != 1:
            errors.append("TaskView arms do not contain identical derived relation results")
            checks["2_identical_derived_results"] = "FAIL"
        else:
            checks["2_identical_derived_results"] = "PASS"

        if len({json.dumps(vocab[name]) for name in TASKVIEW_CONDITIONS}) != 1:
            errors.append("stable vocabulary differs across TaskView arms")
            checks["3_stable_contract_except_experimental"] = "FAIL"
        else:
            t00_extra = experimental_sections("T00")
            t10_extra = experimental_sections("T10")
            t01_extra = experimental_sections("T01")
            t11_extra = experimental_sections("T11")
            contract_ok = (
                t00_extra == []
                and t10_extra != t01_extra
                and "CURRENT means consistent" in "\n".join(t10_extra)
                and "grounding_state FRESH" in "\n".join(t01_extra)
                and "relevant grounding is FRESH" in "\n".join(t11_extra)
                and "Source inspection remains available" in "\n".join(t10_extra)
                and "permission, not an instruction" in "\n".join(t10_extra).lower()
                and contracts["T00"] != contracts["T10"]
                and contracts["T00"] != contracts["T01"]
            )
            checks["3_stable_contract_except_experimental"] = "PASS" if contract_ok else "FAIL"
            if not contract_ok:
                errors.append("experimental contract fields are not isolated correctly")

        before_hash = sha256_file(source / CHECKOUT_CONTRACT_PATH)
        before_snapshot = snapshots["T00"]
        checkout_before = {
            condition: _describe_why(surfaces[condition], CHECKOUT_VERIFIED_BY)
            for condition in TASKVIEW_CONDITIONS
        }
        reporting_before = {
            condition: _describe_why(surfaces[condition], REPORTING_VERIFIED_BY)
            for condition in TASKVIEW_CONDITIONS
        }
        (source / CHECKOUT_CONTRACT_PATH).write_bytes(PHASE4_REPLACEMENT.read_bytes())
        after_hash = sha256_file(source / CHECKOUT_CONTRACT_PATH)
        if before_hash == after_hash:
            errors.append("phase-4 replacement did not change the checkout contract digest")

        after_snapshots = {condition: semantic_rows(views[condition]) for condition in TASKVIEW_CONDITIONS}
        if any(after_snapshots[condition] != before_snapshot for condition in TASKVIEW_CONDITIONS):
            errors.append("source mutation modified semantic tuples")
            checks["4_mutation_preserves_semantic_tuples"] = "FAIL"
        else:
            checks["4_mutation_preserves_semantic_tuples"] = "PASS"

        checkout_after = {
            condition: _describe_why(surfaces[condition], CHECKOUT_VERIFIED_BY)
            for condition in TASKVIEW_CONDITIONS
        }
        freshness_ok = True
        for condition in ("T01", "T11"):
            state = checkout_after[condition]["why"].get("grounding_state")
            if state != "CHANGED":
                freshness_ok = False
                errors.append(f"{condition} checkout grounding after mutation is {state!r}, not CHANGED")
        checks["5_relevant_grounding_changed"] = "PASS" if freshness_ok else "FAIL"

        hidden = False
        for condition in ("T00", "T10"):
            probes = [
                surfaces[condition].describe(),
                surfaces[condition].describe(relation="verified_by"),
                checkout_after[condition],
                surfaces[condition].query_sql("SELECT * FROM verified_by"),
                checkout_before[condition],
            ]
            if any(_hidden_freshness(payload) for payload in probes):
                hidden = True
                errors.append(f"{condition} delivered a hidden grounding-freshness signal")
        checks["6_no_hidden_grounding_signal"] = "FAIL" if hidden else "PASS"

        unrelated_path = source / UNRELATED_SOURCE
        original_unrelated = unrelated_path.read_bytes()
        (source / CHECKOUT_CONTRACT_PATH).write_bytes(
            (SOURCE_ROOT / CHECKOUT_CONTRACT_PATH).read_bytes()
        )
        restored_checkout = _describe_why(surfaces["T01"], CHECKOUT_VERIFIED_BY)
        restored_reporting = _describe_why(surfaces["T01"], REPORTING_VERIFIED_BY)
        unrelated_path.write_bytes(original_unrelated + b"\n# unrelated digest change\n")
        checkout_after_unrelated = _describe_why(surfaces["T01"], CHECKOUT_VERIFIED_BY)
        reporting_after_unrelated = _describe_why(surfaces["T01"], REPORTING_VERIFIED_BY)
        isolation_ok = (
            restored_checkout["why"].get("grounding_state") == "FRESH"
            and restored_reporting["why"].get("grounding_state") == "FRESH"
            and checkout_after_unrelated["why"].get("grounding_state") == "FRESH"
            and reporting_after_unrelated["why"].get("grounding_state") == "CHANGED"
        )
        checks["7_unrelated_source_change_isolates_grounding"] = (
            "PASS" if isolation_ok else "FAIL"
        )
        if not isolation_ok:
            errors.append("unrelated source change invalidated unrelated grounding")
        unrelated_path.write_bytes(original_unrelated)
        (source / CHECKOUT_CONTRACT_PATH).write_bytes(PHASE4_REPLACEMENT.read_bytes())

        retract = surfaces["T00"].assertion(
            action="RETRACT",
            relation="verified_by",
            values=CHECKOUT_VERIFIED_BY["tuple"],
        )
        stale = surfaces["T00"].describe(relation="verification_gap")
        stale_ok = (
            retract.get("removed") is True
            and stale["relation"]["state"] == "STALE"
            and stale["relation"]["completeness"]["state"] == "STALE"
        )
        checks["8_retract_marks_verification_gap_stale"] = "PASS" if stale_ok else "FAIL"
        if not stale_ok:
            errors.append("RETRACT did not mark verification_gap stale")

        rerun = surfaces["T00"].rerun("verification_gap")
        rows = surfaces["T00"].query_sql(
            "SELECT service_id FROM verification_gap ORDER BY service_id"
        )["rows"]
        rerun_ok = rows == [{"service_id": "service:checkout"}]
        checks["9_rerun_verification_gap_is_checkout"] = "PASS" if rerun_ok else "FAIL"
        if not rerun_ok:
            errors.append(f"rerun(verification_gap) produced {rows!r}")

        universe = rerun["completeness"]["universe"]
        scoped = universe == "affected_service"
        checks["10_completeness_scoped_to_affected_service"] = "PASS" if scoped else "FAIL"
        if not scoped:
            errors.append(f"completeness universe is {universe!r}")

        production = {
            row["service_id"]
            for row in views["T00"].query("SELECT service_id FROM production_service")
        }
        affected = {
            row["service_id"]
            for row in views["T00"].query("SELECT service_id FROM affected_service")
        }
        catalog = surfaces["T00"].describe()
        gap_receipts = [
            item for item in catalog["completeness"] if item["target"] == "verification_gap"
        ]
        whole_world_blocked = (
            affected < production
            and universe != "production_service"
            and all(item.get("universe") == "affected_service" for item in gap_receipts)
        )
        checks["11_local_receipt_does_not_license_whole_world"] = (
            "PASS" if whole_world_blocked else "FAIL"
        )
        if not whole_world_blocked:
            errors.append("local completeness receipt appears to license whole-world absence")

        # Equivalent semantic actions on remaining arms after the T00 retract+rerun.
        final_state = semantic_rows(views["T00"])
        equivalent = True
        for condition in ("T10", "T01", "T11"):
            surfaces[condition].assertion(
                action="RETRACT",
                relation="verified_by",
                values=CHECKOUT_VERIFIED_BY["tuple"],
            )
            surfaces[condition].rerun("verification_gap")
            if semantic_rows(views[condition]) != final_state:
                equivalent = False
        checks["12_equivalent_actions_identical_final_state"] = (
            "PASS" if equivalent else "FAIL"
        )
        if not equivalent:
            errors.append("equivalent semantic actions produced divergent TaskView state")

        mutation_did_not_retract = all(
            any(
                row.get("service_id") == "service:checkout"
                or row.get("service") == "service:checkout"
                for row in snapshots[condition]["verified_by"]
            )
            for condition in TASKVIEW_CONDITIONS
        )
        checks["mutation_does_not_retract_or_rerun"] = (
            "PASS" if mutation_did_not_retract else "FAIL"
        )
        if not mutation_did_not_retract:
            errors.append("source mutation itself removed verified_by rows")

        sql_before = surfaces["T01"].query_sql("SELECT * FROM verified_by")
        if _hidden_freshness(sql_before):
            errors.append("SQL row payloads contain grounding-freshness fields")

        for view in views.values():
            view.close()

        checks["checkout_digest_before"] = before_hash
        checks["checkout_digest_after"] = after_hash
        checks["checkout_grounding_before_t01"] = checkout_before["T01"]["why"].get(
            "grounding_state"
        )
        checks["checkout_grounding_after_t01"] = checkout_after["T01"]["why"].get(
            "grounding_state"
        )
        checks["reporting_grounding_before_t01"] = reporting_before["T01"]["why"].get(
            "grounding_state"
        )

    ordered_status = [
        checks["1_identical_semantic_tuples"],
        checks["2_identical_derived_results"],
        checks["3_stable_contract_except_experimental"],
        checks["4_mutation_preserves_semantic_tuples"],
        checks["5_relevant_grounding_changed"],
        checks["6_no_hidden_grounding_signal"],
        checks["7_unrelated_source_change_isolates_grounding"],
        checks["8_retract_marks_verification_gap_stale"],
        checks["9_rerun_verification_gap_is_checkout"],
        checks["10_completeness_scoped_to_affected_service"],
        checks["11_local_receipt_does_not_license_whole_world"],
        checks["12_equivalent_actions_identical_final_state"],
    ]
    status = "PASS" if not errors and all(item == "PASS" for item in ordered_status) else "FAIL"
    result = {
        "campaign_id": "taskview-orientation-bounded-reliance-v1",
        "status": status,
        "errors": errors,
        "participant_inference_calls": 0,
        "live_inference_blocked": True,
        "checks": checks,
        "ordered_status": ordered_status,
        "entitlement_sha256": sha256_file(
            Path(__file__).resolve().parent / "frozen" / "entitlement.json"
        ),
        "block_order_sha256": sha256_file(
            Path(__file__).resolve().parent / "frozen" / "block_order.json"
        ),
        "frozen_taskview_sha256": sha256_file(FROZEN_ROOT / "taskview.sqlite"),
        "model": MODEL,
        "model_fast_forbidden": MODEL_FAST_FORBIDDEN,
    }
    _write(output_path, result)
    return result


def main() -> None:
    print(json.dumps(run_preflight(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
