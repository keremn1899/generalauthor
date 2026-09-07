"""Evaluator-only gold from compiled Worlds. Never copied into host workspaces."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    EVALUATOR_ONLY,
    OUTPUTS,
    STATES,
)


def _rows(state_id: str) -> list[dict]:
    with (OUTPUTS / state_id / "monitoring_analysis.csv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def gold_for_state(state_id: str) -> dict:
    rows = _rows(state_id)
    holes = json.loads((STATES / state_id / "compile_meta.json").read_text())
    factual = [r for r in rows if r["monitoring_status"] == "UNRESOLVED_FACTUAL"]
    semantic_mon = [r for r in rows if r["monitoring_status"] == "UNRESOLVED_SEMANTIC"]
    nodi = [r for r in rows if r["nodi_code"] in {"C", "9"}]
    determinate = [r for r in rows if r["evidence_status"] == "DETERMINATE"]
    pass_fail = [r for r in rows if r["comparison_status"] in {"PASS", "FAIL"}]
    numeric_ok = [r for r in rows if r["comparison_status"] in {"EXCEEDANCE", "WITHIN_LIMIT"}]
    return {
        "state_id": state_id,
        "n_rows": len(rows),
        "n_determinate": len(determinate),
        "n_unresolved_factual_monitoring": len(factual),
        "n_unresolved_semantic_monitoring": len(semantic_mon),
        "n_nodi_c_or_9": len(nodi),
        "n_nodi_still_unresolved_semantic": sum(
            1 for r in nodi if "nodi_code_semantics" in (r.get("unresolved_reason") or "")
        ),
        "n_pass_fail_classified": len(pass_fail),
        "n_numeric_comparison_computed": len(numeric_ok),
        "evidence_status": dict(Counter(r["evidence_status"] for r in rows)),
        "q1": {
            "indeterminate_if": "evidence_status in {UNRESOLVED_SEMANTIC, UNRESOLVED_FACTUAL, NOT_ESTABLISHED}",
            "leading_prerequisites": [
                "nodi_code_semantics",
                "discharge_occurrence_in_period" if state_id != "state_a" else "conditional_discharge_dependent_monitoring",
                "monitoring_frequency_code",
                "pass_fail_reporting_semantics" if state_id != "state_c" else "wet_pass_fail remaining siblings",
            ],
        },
        "q2": {
            "computable_numeric": len(numeric_ok),
            "cannot_yet_exceedance": len(rows) - len(numeric_ok) - len(pass_fail),
        },
        "q3": {
            "discharge_occurrence_represented": state_id != "state_a",
            "n_factual_discharge_uncertainty": len(factual),
            "comment_meaning_still_opaque": len(semantic_mon),
        },
        "hole_groups": holes.get("n_hole_groups"),
        "hole_instances": holes.get("n_hole_instances"),
    }


def write_gold() -> dict:
    EVALUATOR_ONLY.mkdir(parents=True, exist_ok=True)
    payload = {state: gold_for_state(state) for state in ("state_a", "state_b", "state_c")}
    (EVALUATOR_ONLY / "gold.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (EVALUATOR_ONLY / "README.md").write_text(
        "Evaluator-only. Do not copy into host or isolated consumer workspaces.\n",
        encoding="utf-8",
    )
    return payload
