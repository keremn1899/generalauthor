"""Post-campaign report. Frozen continuation rule. No retuning."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _episode_row(root: Path, episode: dict[str, Any]) -> dict[str, Any]:
    record = _load(root / episode["episode_id"] / "record.json")
    scored = record["compiled_projection"]
    recon = scored["reassembly_after_delivery"]
    mech = scored["mechanism_outcomes"]
    local = mech["required_local_source_inspection_rate"]
    local_preserved = all(rate == 1.0 for rate in local.values() if rate is not None)
    return {
        "episode_id": episode["episode_id"],
        "block": record["block"],
        "condition": record["condition"],
        "session_id": record["session_id"],
        "reassembly_calls": recon["reassembly_calls"],
        "reassembly_bytes": recon["reassembly_bytes"],
        "distinct_subsumed_relations_reopened": recon["distinct_subsumed_relations_reopened"],
        "targeted_describe_calls_on_subsumed_relations": recon[
            "targeted_describe_calls_on_subsumed_relations"
        ],
        "SQL_calls_on_subsumed_relations": recon["SQL_calls_on_subsumed_relations"],
        "repository_support_files_reopened_for_already_compiled_coarse_state": recon[
            "repository_support_files_reopened_for_already_compiled_coarse_state"
        ],
        "projection_reread_calls": recon["projection_reread_calls"],
        "phases": recon["phases"],
        "initial_delivery_bytes": scored["initial_delivery_bytes"],
        "repository_orientation_bytes": mech["repository_orientation_bytes"],
        "taskview_visible_bytes": mech["taskview_visible_bytes"],
        "acquisition_inclusive_bytes": mech["acquisition_inclusive_bytes"],
        "catalog_describe_count": mech["catalog_describe_count"],
        "targeted_describe_count": mech["targeted_describe_count"],
        "sql_query_count": mech["sql_query_count"],
        "unique_taskview_relations_accessed": mech["unique_taskview_relations_accessed"],
        "unique_repository_files_read": mech["unique_repository_files_read"],
        "broad_repository_searches": mech["broad_repository_searches"],
        "required_local_source_inspection_rate": local,
        "local_inspection_preserved": local_preserved,
        "phase4_changed_checkout_source_inspected": mech[
            "phase4_changed_checkout_source_inspected"
        ],
        "false_known_absence_claims": mech["false_known_absence_claims"],
        "phase5_completeness_universe": mech["phase5_completeness_universe"],
        "phase5_whole_world_complete": mech["phase5_whole_world_complete"],
        "semantic_assertion_update": mech["semantic_assertion_update"],
        "verification_gap_rerun_behavior": mech["verification_gap_rerun_behavior"],
        "checkout_verified_by_retracted": mech["checkout_verified_by_retracted"],
        "participant_tool_errors": mech["participant_tool_errors"],
    }


def _continuation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_block: dict[int, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_block.setdefault(row["block"], {})[row["condition"]] = row
    matched = []
    reductions = []
    acquisition_compiled_lower = 0
    for block, conditions in sorted(by_block.items()):
        atomic = conditions["ATOMIC"]
        compiled = conditions["COMPILED"]
        atomic_bytes = atomic["reassembly_bytes"]
        compiled_bytes = compiled["reassembly_bytes"]
        lower = compiled_bytes < atomic_bytes
        if atomic_bytes > 0:
            reduction = (atomic_bytes - compiled_bytes) / atomic_bytes
        else:
            reduction = 0.0
        reductions.append(reduction)
        if compiled["acquisition_inclusive_bytes"] < atomic["acquisition_inclusive_bytes"]:
            acquisition_compiled_lower += 1
        matched.append(
            {
                "block": block,
                "ATOMIC": {
                    "reassembly_calls": atomic["reassembly_calls"],
                    "reassembly_bytes": atomic_bytes,
                    "acquisition_inclusive_bytes": atomic["acquisition_inclusive_bytes"],
                    "repository_orientation_bytes": atomic["repository_orientation_bytes"],
                    "taskview_visible_bytes": atomic["taskview_visible_bytes"],
                },
                "COMPILED": {
                    "reassembly_calls": compiled["reassembly_calls"],
                    "reassembly_bytes": compiled_bytes,
                    "acquisition_inclusive_bytes": compiled["acquisition_inclusive_bytes"],
                    "repository_orientation_bytes": compiled["repository_orientation_bytes"],
                    "taskview_visible_bytes": compiled["taskview_visible_bytes"],
                },
                "compiled_reassembly_bytes_lower": lower,
                "reassembly_byte_reduction": reduction,
            }
        )
    compiled_rows = [row for row in rows if row["condition"] == "COMPILED"]
    primary_direction = all(item["compiled_reassembly_bytes_lower"] for item in matched)
    median_reduction = median(reductions) if reductions else 0.0
    local_ok = all(row["local_inspection_preserved"] for row in compiled_rows)
    checkout_ok = all(row["phase4_changed_checkout_source_inspected"] for row in compiled_rows)
    absence_ok = not any(row["false_known_absence_claims"] for row in rows)
    whole_world_ok = not any(row["phase5_whole_world_complete"] is True for row in rows)
    maintenance_ok = all(
        row["checkout_verified_by_retracted"] and row["verification_gap_rerun_behavior"]
        for row in compiled_rows
    )
    supported = (
        len(matched) == 3
        and primary_direction
        and median_reduction >= 0.5
        and acquisition_compiled_lower >= 2
        and local_ok
        and checkout_ok
        and absence_ok
        and whole_world_ok
        and maintenance_ok
    )
    if not primary_direction or median_reduction < 0.5:
        decision = "COMPILED-GRANULARITY HYPOTHESIS NOT SUPPORTED"
    elif supported:
        decision = "SUPPORTED FOR CONTINUATION"
    else:
        decision = "COMPILED-GRANULARITY HYPOTHESIS NOT SUPPORTED"
    return {
        "matched_blocks": matched,
        "primary_3_of_3_compiled_lower_reassembly_bytes": primary_direction,
        "median_reassembly_byte_reduction": median_reduction,
        "compiled_lower_acquisition_inclusive_blocks": acquisition_compiled_lower,
        "local_inspection_preserved": local_ok,
        "compiled_phase4_checkout_inspected_3_of_3": checkout_ok,
        "no_false_known_absence": absence_ok,
        "no_invalid_whole_world_completeness": whole_world_ok,
        "phase4_semantic_maintenance_valid": maintenance_ok,
        "supported_for_continuation": supported,
        "decision": decision,
    }


def _interpretation(continuation: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    compiled = [row for row in rows if row["condition"] == "COMPILED"]
    atomic = [row for row in rows if row["condition"] == "ATOMIC"]
    unsafe = (not continuation["local_inspection_preserved"]) or (
        not continuation["compiled_phase4_checkout_inspected_3_of_3"]
    ) or (not continuation["no_false_known_absence"]) or (
        not continuation["no_invalid_whole_world_completeness"]
    )
    mean_repo_c = sum(row["repository_orientation_bytes"] for row in compiled) / 3
    mean_repo_a = sum(row["repository_orientation_bytes"] for row in atomic) / 3
    increased = all(
        item["COMPILED"]["reassembly_bytes"] > item["ATOMIC"]["reassembly_bytes"]
        for item in continuation["matched_blocks"]
    )
    if unsafe and continuation["primary_3_of_3_compiled_lower_reassembly_bytes"]:
        return "D"
    if increased:
        return "E"
    if continuation["primary_3_of_3_compiled_lower_reassembly_bytes"] and continuation[
        "median_reassembly_byte_reduction"
    ] >= 0.5:
        if mean_repo_c < 0.8 * mean_repo_a:
            return "A"
        return "B"
    return "C"


def analyze(root: Path) -> dict[str, Any]:
    progress = _load(root / "campaign_progress.json")
    if progress.get("status") != "SEALED" or progress.get("valid") is not True:
        raise RuntimeError("campaign is not valid and sealed")
    if len(progress.get("episodes_completed") or []) != 6:
        raise RuntimeError("campaign does not contain 6 sealed episodes")
    rows = [_episode_row(root, episode) for episode in progress["episodes_completed"]]
    apparatus: list[dict[str, Any]] = []
    resumed: Any = progress.get("resumed_from")
    seen: set[str] = set()
    while isinstance(resumed, dict):
        key = json.dumps(resumed.get("failure_episode"), sort_keys=True)
        if key in seen:
            break
        seen.add(key)
        if resumed.get("failure"):
            apparatus.append(
                {
                    "failure": resumed.get("failure"),
                    "failure_type": resumed.get("failure_type"),
                    "failure_episode": resumed.get("failure_episode"),
                }
            )
        resumed = resumed.get("resumed_from")
    continuation = _continuation(rows)
    case = _interpretation(continuation, rows)
    cases = {
        "A": "COMPILED sharply reduces TaskView relation reassembly and repository corroboration.",
        "B": "COMPILED sharply reduces TaskView relation reassembly but repository orientation remains at the existing TaskView floor.",
        "C": "COMPILED does not substantially reduce relation reassembly.",
        "D": "COMPILED reduces reassembly but suppresses required local inspection or creates unsafe/stale certainty.",
        "E": "COMPILED increases consumption.",
    }
    return {
        "campaign_id": progress["campaign_id"],
        "status": progress["status"],
        "valid": progress["valid"],
        "episode_count": len(rows),
        "participant_turn_count": 30,
        "apparatus_failures": len(apparatus),
        "apparatus_failure_records": apparatus,
        "retries_replays": len(apparatus),
        "within_episode_retry": bool(progress.get("within_episode_retry")),
        "episodes": rows,
        "continuation": continuation,
        "interpretation_case": case,
        "interpretation": cases[case],
        "decision": continuation["decision"],
        "historical_findings_unchanged": True,
        "economics_is_primary_success_criterion": False,
    }


def write_report(root: Path) -> dict[str, Any]:
    report = analyze(root)
    _write(root / "campaign_report.json", report)
    return report
