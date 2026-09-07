"""Row-level and summary diffs between adjacent World states."""

from __future__ import annotations

import csv
import json
from pathlib import Path

COMPARE_FIELDS = (
    "comparison_status",
    "monitoring_status",
    "evidence_status",
    "unresolved_reason",
    "pass_fail_reported",
    "monitoring_condition",
)


def load_rows(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return {row["application_key"]: row for row in csv.DictReader(fh)}


def diff_states(before_csv: Path, after_csv: Path, before_id: str, after_id: str) -> dict:
    before = load_rows(before_csv)
    after = load_rows(after_csv)
    keys = sorted(set(before) | set(after))
    changed = []
    for key in keys:
        b = before.get(key)
        a = after.get(key)
        if b is None or a is None:
            changed.append(
                {
                    "application_key": key,
                    "change": "added" if b is None else "removed",
                    "before_state": json.dumps(b or {}, sort_keys=True),
                    "after_state": json.dumps(a or {}, sort_keys=True),
                    "reason": "row_presence",
                    "semantic_relation": "",
                    "grounding_pointer": "",
                }
            )
            continue
        deltas = [f for f in COMPARE_FIELDS if b.get(f) != a.get(f)]
        if not deltas:
            continue
        reason = ",".join(deltas)
        relation = ""
        if b.get("monitoring_status") != a.get("monitoring_status"):
            relation = "monitoring_requirement_fy2025 / discharge_occurrence_in_period"
        if b.get("comparison_status") != a.get("comparison_status") or b.get("pass_fail_reported") != a.get(
            "pass_fail_reported"
        ):
            relation = (relation + "; " if relation else "") + "pass_fail_outcome_reporting"
        changed.append(
            {
                "application_key": key,
                "facility": a.get("facility"),
                "parameter": a.get("parameter"),
                "monitoring_period": a.get("monitoring_period"),
                "change": "field_delta",
                "fields_changed": reason,
                "before_comparison": b.get("comparison_status"),
                "after_comparison": a.get("comparison_status"),
                "before_monitoring": b.get("monitoring_status"),
                "after_monitoring": a.get("monitoring_status"),
                "before_evidence": b.get("evidence_status"),
                "after_evidence": a.get("evidence_status"),
                "before_unresolved": b.get("unresolved_reason"),
                "after_unresolved": a.get("unresolved_reason"),
                "semantic_relation": relation,
                "grounding_pointer": "",
                "before_state": before_id,
                "after_state": after_id,
            }
        )
    summary = {
        "before": before_id,
        "after": after_id,
        "n_before": len(before),
        "n_after": len(after),
        "n_changed": len(changed),
        "n_unchanged": len(keys) - len(changed),
        "newly_determinate": sum(
            1
            for row in changed
            if row.get("change") == "field_delta"
            and row.get("before_evidence") != "DETERMINATE"
            and row.get("after_evidence") == "DETERMINATE"
        ),
        "semantic_to_factual": sum(
            1
            for row in changed
            if row.get("before_monitoring") == "UNRESOLVED_SEMANTIC"
            and row.get("after_monitoring") == "UNRESOLVED_FACTUAL"
        ),
        "pass_fail_classified": sum(
            1
            for row in changed
            if row.get("after_comparison") in {"PASS", "FAIL"}
            and row.get("before_comparison") not in {"PASS", "FAIL"}
        ),
    }
    return {"summary": summary, "rows": changed}


def write_diff(payload: dict, csv_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["rows"]
    fieldnames = list(rows[0].keys()) if rows else ["application_key", "change"]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    s = payload["summary"]
    md = [
        f"# {s['before']} → {s['after']}",
        "",
        f"- rows before: {s['n_before']}",
        f"- rows after: {s['n_after']}",
        f"- changed: {s['n_changed']}",
        f"- unchanged: {s['n_unchanged']}",
        f"- newly determinate: {s['newly_determinate']}",
        f"- semantic→factual monitoring: {s['semantic_to_factual']}",
        f"- newly PASS/FAIL classified: {s['pass_fail_classified']}",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")
