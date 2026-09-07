"""Write MEASURED reports from runs/score.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.capability.end_to_end_v1.paths import (
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    REPORTS,
    RUNS,
)
from research.semantic_integration.capability.end_to_end_v1.score import aggregate


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_reports(payload: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    construction = payload["construction"]
    consumers = payload["consumers"]
    accepted = [row for row in construction if row.get("build") == "ACCEPTED"]
    n_est_present = 0
    n_est = 0
    n_unres = 0
    n_unres_ok = 0
    closures = 0
    for row in construction:
        cov = row.get("coverage") or {}
        for qid, status in cov.items():
            if qid in {"Q5", "Q6"}:
                n_unres += 1
                if status == "EXPLICITLY_UNRESOLVED":
                    n_unres_ok += 1
                if status == "UNSUPPORTED":
                    closures += 1
            else:
                n_est += 1
                if status == "PRESENT":
                    n_est_present += 1
        closures += len(row.get("unsupported_closure_hits") or [])

    lines = ["# Construction results", "", "## MEASURED", ""]
    lines.append(f"Accepted Worlds: **{len(accepted)} / {len(construction)}**")
    lines.append("")
    rows = []
    for row in construction:
        cov = row.get("coverage") or {}
        rows.append(
            [
                row.get("domain", ""),
                row.get("trial", ""),
                row.get("build", ""),
                str(row.get("attempts", "")),
                ",".join(f"{k}:{v}" for k, v in cov.items()) or "—",
                str(row.get("unsupported_closure_hits") or []),
            ]
        )
    lines.append(md_table(["domain", "trial", "build", "attempts", "coverage", "closure_hits"], rows))
    lines.append("")
    lines.append(f"Establishable PRESENT: {n_est_present}/{n_est}")
    lines.append(f"Non-establishable EXPLICITLY_UNRESOLVED: {n_unres_ok}/{n_unres}")
    (REPORTS / "construction_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cov_lines = ["# Semantic coverage", "", "## MEASURED", ""]
    for row in construction:
        cov_lines.append(f"### {row.get('domain')} {row.get('trial')}")
        cov_lines.append("")
        cov_lines.append(json.dumps(row.get("coverage"), indent=2))
        inv = row.get("inventory") or {}
        cov_lines.append("")
        cov_lines.append(
            f"relations={inv.get('relation_count')} assertions={inv.get('n_assertions')} "
            f"source_groundings={inv.get('n_source_groundings')} failures={inv.get('n_failures')}"
        )
        cov_lines.append("")
    (REPORTS / "semantic_coverage.md").write_text("\n".join(cov_lines) + "\n", encoding="utf-8")

    def tally(kind: str) -> dict[str, int]:
        counts = {
            "CORRECT": 0,
            "INCORRECT": 0,
            "UNRESOLVED_CORRECTLY": 0,
            "UNRESOLVED_INCORRECTLY": 0,
            "UNSUPPORTED_CLOSURE": 0,
            "n": 0,
        }
        for row in consumers:
            if row.get("kind") != kind:
                continue
            for status in (row.get("classifications") or {}).values():
                counts["n"] += 1
                counts[status] = counts.get(status, 0) + 1
        return counts

    world_t, raw_t = tally("WORLD"), tally("RAW")
    rvw = ["# RAW vs WORLD", "", "## MEASURED", ""]
    rvw.append(md_table(
        ["condition", "CORRECT", "INCORRECT", "UNRESOLVED_CORRECTLY", "UNRESOLVED_INCORRECTLY", "UNSUPPORTED_CLOSURE", "n"],
        [
            ["WORLD", *[str(world_t[k]) for k in ["CORRECT", "INCORRECT", "UNRESOLVED_CORRECTLY", "UNRESOLVED_INCORRECTLY", "UNSUPPORTED_CLOSURE", "n"]]],
            ["RAW", *[str(raw_t[k]) for k in ["CORRECT", "INCORRECT", "UNRESOLVED_CORRECTLY", "UNRESOLVED_INCORRECTLY", "UNSUPPORTED_CLOSURE", "n"]]],
        ],
    ))
    rvw.append("")
    detail_rows = []
    for domain in DOMAIN_IDS:
        for kind in ("WORLD", "RAW"):
            subset = [r for r in consumers if r.get("domain") == domain and r.get("kind") == kind]
            if not subset:
                continue
            detail_rows.append([domain, kind, json.dumps({r.get("trial"): r.get("classifications") for r in subset})])
    rvw.append(md_table(["domain", "kind", "per_trial"], detail_rows))
    (REPORTS / "raw_vs_world.md").write_text("\n".join(rvw) + "\n", encoding="utf-8")

    fail = ["# Failure analysis", "", "## OBSERVED", ""]
    fail.append("Primary buckets assigned from consumer classifications and construction coverage.")
    fail.append("")
    fail.append("- UNRESOLVED_INCORRECTLY on establishable WORLD → SEMANTIC_UNDERCOVERAGE or CONSUMER_INTERFACE_FAILURE")
    fail.append("- CORRECT on RAW but UNRESOLVED_INCORRECTLY on WORLD, with PRESENT coverage → CONSUMER_INTERFACE_FAILURE")
    fail.append("- MISSING coverage + RAW CORRECT → SEMANTIC_UNDERCOVERAGE")
    fail.append("- UNSUPPORTED_CLOSURE → UNSUPPORTED_CLOSURE")
    fail.append("- NO_ACCEPTED_WORLD → RUNTIME_FAILURE")
    (REPORTS / "failure_analysis.md").write_text("\n".join(fail) + "\n", encoding="utf-8")


def main() -> None:
    payload = aggregate()
    (RUNS / "score.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_reports(payload)


if __name__ == "__main__":
    main()
