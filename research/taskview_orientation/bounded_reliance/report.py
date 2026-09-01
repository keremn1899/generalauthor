"""Post-campaign report for the frozen bounded-reliance metric. No retuning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONDITIONS = ("R", "T00", "T10", "T01", "T11")
TASKVIEW_CONTRASTS = (
    ("T10", "T00"),
    ("T01", "T00"),
    ("T11", "T00"),
    ("T11", "T10"),
    ("T11", "T01"),
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _episode_row(root: Path, episode: dict[str, Any]) -> dict[str, Any]:
    record = _load(root / episode["episode_id"] / "record.json")
    scored = record["bounded_reliance"]
    recon = scored["reconstruction_after_entitlement"]
    mech = scored["mechanism_outcomes"]
    falsifiers = mech["phase4_falsifiers"]
    local_correct = all(
        item.get("all_fields_correct")
        for item in mech["semantically_adjudicated_local_correctness"]
    )
    completeness = mech["currentness_completeness_correctness"]
    return {
        "episode_id": episode["episode_id"],
        "block": record["block"],
        "condition": record["condition"],
        "arm": record["arm"],
        "session_id": record["session_id"],
        "reproof_calls": recon["episode_reproof_calls"],
        "reproof_bytes": recon["episode_reproof_bytes"],
        "reproof_relations": sorted(
            {
                name
                for phase in recon["phases"].values()
                for name in phase["reproof_distinct_relations"]
            }
        ),
        "reproof_repository_files": sorted(
            {
                name
                for phase in recon["phases"].values()
                for name in phase["reproof_repository_files"]
            }
        ),
        "phases": recon["phases"],
        "catalog_describe_count": mech["catalog_describe_count"],
        "targeted_describe_count": mech["targeted_describe_count"],
        "sql_query_count": mech["sql_query_count"],
        "relation_breadth": mech["relation_breadth"],
        "repository_orientation_bytes": mech["repository_orientation_bytes"],
        "taskview_visible_bytes": mech["taskview_visible_bytes"],
        "acquisition_inclusive_bytes": mech["acquisition_inclusive_bytes"],
        "local_source_inspection_rate": mech["local_source_inspection_rate"],
        "semantic_local_correctness": local_correct,
        "oracle_scores": record["oracle_scores"],
        "currentness_completeness_correctness": completeness,
        "phase4_changed_source_inspection": mech["phase4_changed_source_inspection"],
        "grounding_response": {
            "saw_checkout_grounding_why": falsifiers["saw_checkout_grounding_why"],
            "received_changed_grounding": falsifiers["received_changed_grounding"],
            "checkout_verification_invalidated_in_answer": falsifiers[
                "checkout_verification_invalidated_in_answer"
            ],
            "treat_old_verification_as_justified_after_changed": falsifiers[
                "treat_old_verification_as_justified_after_changed"
            ],
            "treat_changed_as_automatic_falsehood": falsifiers[
                "treat_changed_as_automatic_falsehood"
            ],
            "t10_authority_without_freshness": falsifiers["t10_authority_without_freshness"],
        },
        "semantic_assertion_update": mech["assert_retract_behavior"],
        "rerun_behavior": mech["derived_state_rerun_behavior"],
        "false_known_absence_claims": mech["false_known_absence_claims"],
        "participant_tool_errors": mech["participant_tool_errors"],
        "execution_checks": record.get("execution_checks"),
        "O_post": scored["economics_reported_not_primary"]["O_post"],
        "net_orientation_bytes": scored["economics_reported_not_primary"][
            "net_orientation_bytes"
        ],
    }


def _delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "reproof_calls",
        "reproof_bytes",
        "catalog_describe_count",
        "targeted_describe_count",
        "sql_query_count",
        "repository_orientation_bytes",
        "taskview_visible_bytes",
        "acquisition_inclusive_bytes",
        "participant_tool_errors",
        "O_post",
    )
    out = {key: left[key] - right[key] for key in keys if left.get(key) is not None and right.get(key) is not None}
    out["relation_breadth_delta"] = len(left["relation_breadth"]) - len(right["relation_breadth"])
    out["semantic_local_correctness"] = {
        "left": left["semantic_local_correctness"],
        "right": right["semantic_local_correctness"],
    }
    out["phase4_changed_source_inspection"] = {
        "left": left["phase4_changed_source_inspection"],
        "right": right["phase4_changed_source_inspection"],
    }
    out["false_known_absence_claims"] = {
        "left": left["false_known_absence_claims"],
        "right": right["false_known_absence_claims"],
    }
    return out


def analyze(root: Path) -> dict[str, Any]:
    progress = _load(root / "campaign_progress.json")
    if progress.get("status") != "SEALED" or progress.get("valid") is not True:
        raise RuntimeError("campaign is not valid and sealed")
    if len(progress.get("episodes_completed") or []) != 20:
        raise RuntimeError("campaign does not contain 20 sealed episodes")
    rows = [_episode_row(root, episode) for episode in progress["episodes_completed"]]
    by_block: dict[int, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_block.setdefault(row["block"], {})[row["condition"]] = row
    contrasts: dict[str, Any] = {}
    for left_name, right_name in TASKVIEW_CONTRASTS:
        paired = []
        for block, conditions in sorted(by_block.items()):
            if left_name in conditions and right_name in conditions:
                paired.append(
                    {
                        "block": block,
                        "delta": _delta(conditions[left_name], conditions[right_name]),
                    }
                )
        if paired:
            numeric_keys = [
                key
                for key in paired[0]["delta"]
                if isinstance(paired[0]["delta"][key], (int, float))
            ]
            contrasts[f"{left_name}-{right_name}"] = {
                "pairs": paired,
                "mean": {
                    key: sum(item["delta"][key] for item in paired) / len(paired)
                    for key in numeric_keys
                },
            }
    by_condition: dict[str, list[dict[str, Any]]] = {name: [] for name in CONDITIONS}
    for row in rows:
        by_condition[row["condition"]].append(row)

    def _mean(condition: str, field: str) -> float | None:
        values = [item[field] for item in by_condition[condition] if item.get(field) is not None]
        if not values:
            return None
        return sum(values) / len(values)

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

    return {
        "campaign_id": progress["campaign_id"],
        "status": progress["status"],
        "valid": progress["valid"],
        "episode_count": len(rows),
        "participant_turn_count": 100,
        "apparatus_failures": len(apparatus),
        "apparatus_failure_records": apparatus,
        "retries_replays": len(apparatus),
        "within_episode_retry": bool(progress.get("within_episode_retry")),
        "episodes": rows,
        "condition_means": {
            condition: {
                "reproof_calls": _mean(condition, "reproof_calls"),
                "reproof_bytes": _mean(condition, "reproof_bytes"),
                "catalog_describe_count": _mean(condition, "catalog_describe_count"),
                "targeted_describe_count": _mean(condition, "targeted_describe_count"),
                "sql_query_count": _mean(condition, "sql_query_count"),
                "repository_orientation_bytes": _mean(condition, "repository_orientation_bytes"),
                "taskview_visible_bytes": _mean(condition, "taskview_visible_bytes"),
                "acquisition_inclusive_bytes": _mean(condition, "acquisition_inclusive_bytes"),
                "phase4_changed_source_inspection": sum(
                    1 for item in by_condition[condition] if item["phase4_changed_source_inspection"]
                ),
                "semantic_local_correctness": sum(
                    1 for item in by_condition[condition] if item["semantic_local_correctness"]
                ),
                "false_known_absence_claims": sum(
                    1 for item in by_condition[condition] if item["false_known_absence_claims"]
                ),
                "t10_authority_without_freshness": sum(
                    1
                    for item in by_condition[condition]
                    if item["grounding_response"]["t10_authority_without_freshness"]
                ),
                "participant_tool_errors": _mean(condition, "participant_tool_errors"),
            }
            for condition in CONDITIONS
        },
        "matched_contrasts": contrasts,
        "historical_findings_unchanged": {
            "taskview_repository_orientation_suppression": "supported descriptively",
            "historical_frozen_mechanism_criterion": "FAIL",
            "historical_net_economics": "FAIL",
            "demonstrated_local_semantic_harm": "none established",
        },
        "economics_is_primary_success_criterion": False,
        "t11_not_successful_merely_for_fewer_bytes": True,
    }


def write_report(root: Path) -> dict[str, Any]:
    report = analyze(root)
    _write(root / "campaign_report.json", report)
    return report
