"""Seal refinement/admission reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.paths import REPORTS, RUNS
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.score import (
    choose_label,
    score,
)


def write(name: str, body: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def jdump(obj) -> str:
    return json.dumps(obj, indent=2, default=str)


def refinement_md(summary: dict) -> str:
    lines = ["# Refinement results", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        if c.get("obligation_id") == "document_authority":
            continue
        ref = c.get("refinement") or {}
        parent = c.get("parent") or {}
        kids = ref.get("children") or []
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append(f"parent_status={parent.get('parent_status')} independently_admitted={parent.get('independently_admitted')} independently_unresolved={parent.get('independently_unresolved')}")
        lines.append(f"n_children={len(kids) if isinstance(kids, list) else kids} mechanically_computable={ref.get('mechanically_computable')} partition_complete={ref.get('partition_complete')}")
        if isinstance(kids, list):
            for k in kids:
                if not isinstance(k, dict):
                    continue
                lines.append(
                    f"- `{k.get('child_id')}` n={k.get('affected_count')} disp={k.get('disposition')} admit={k.get('admission_status')} epi={k.get('epistemic_basis')}"
                )
                lines.append(f"  partition: {k.get('occurrence_partition_rule')}")
        lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            f"TDS/non-TDS recovery: {jdump(summary.get('tds_split'))}",
            f"fragmented={summary.get('fragmented_cells')}",
            "",
            "## HYPOTHESIS",
            "",
            "A refined parent is superseded by children; it is not independently UNRESOLVED.",
        ]
    )
    return "\n".join(lines)


def parent_child_md(summary: dict) -> str:
    lines = [
        "# Parent/child states",
        "",
        "## MEASURED",
        "",
        "| cell | parent_status | independently_admitted | independently_unresolved | drift |",
        "| --- | --- | --- | --- | --- |",
    ]
    drifts = set(summary.get("protocol_drifts") or [])
    for c in summary.get("cells") or []:
        key = f"{c.get('trial')}:{c.get('obligation_id')}"
        p = c.get("parent") or {}
        lines.append(
            f"| {key} | {p.get('parent_status')} | {p.get('independently_admitted')} | {p.get('independently_unresolved')} | {key in drifts} |"
        )
    lines.extend(
        [
            "",
            "## OBSERVED",
            "",
            f"protocol_drifts={summary.get('protocol_drifts')}",
            "",
            "## HYPOTHESIS",
            "",
            "Target: parent=REFINED, independently admitted=false, independently unresolved=false when heterogeneity is the only reason the parent cannot receive one answer.",
        ]
    )
    return "\n".join(lines)


def document_md(summary: dict) -> str:
    lines = ["# Document admission results", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        if c.get("obligation_id") != "document_authority":
            continue
        lines.append(f"### {c.get('trial')}")
        lines.append("")
        lines.append("```json")
        lines.append(jdump(c.get("admission") or {})[:8000])
        lines.append("```")
        lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            f"broader_admissions={summary.get('broader_admissions')}",
            f"local_underused={summary.get('local_underused')}",
            "",
            "## HYPOTHESIS",
            "",
            "Local source-established observations may be admitted. Broader inferred precedence remains UNVERIFIED_PROPOSAL unless licensed.",
        ]
    )
    return "\n".join(lines)


def deltas_md(summary: dict) -> str:
    lines = ["# Disposable deltas", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        for dry in c.get("dry_runs") or []:
            d = dry.get("delta") or {}
            lines.append(f"### {c.get('trial')} {c.get('obligation_id')} / {dry.get('child_id')} ok={dry.get('ok')}")
            lines.append("")
            if dry.get("errors"):
                lines.append(f"errors: {dry.get('errors')}")
            lines.append(f"holes groups {d.get('n_hole_groups')} instances {d.get('n_hole_instances')}")
            lines.append(f"count changes `{json.dumps(d.get('relation_count_changes'))}`")
            lines.append(f"requirements + {d.get('requirements_added')} - {d.get('requirements_removed')}")
            lines.append(f"hole req - {d.get('hole_requirements_removed')}")
            lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            f"failed_dry_runs={summary.get('failed_dry_runs')}",
            f"leakage_flags={jdump(summary.get('leakage_flags') or {})}",
            "",
            "## HYPOTHESIS",
            "",
            "Apply failures are mechanical, not semantic-resolution failures. TDS child must not drop WHEN DISCHARGING / pass-fail families.",
        ]
    )
    return "\n".join(lines)


def failure_md(summary: dict) -> str:
    return "\n".join(
        [
            "# Failure analysis",
            "",
            "## MEASURED",
            "",
            f"- protocol_drifts={summary.get('protocol_drifts')}",
            f"- fragmented={summary.get('fragmented_cells')}",
            f"- unsupported_child_closures={summary.get('unsupported_child_closures')}",
            f"- broader_admissions={summary.get('broader_admissions')}",
            f"- local_underused={summary.get('local_underused')}",
            f"- failed_dry_runs={summary.get('failed_dry_runs')}",
            f"- leakage={jdump(summary.get('leakage_flags') or {})}",
            f"- mutated_durable={summary.get('mutated_durable')}",
            "",
            "## OBSERVED",
            "",
            "Do not conflate disposable apply crashes with parent/child protocol drift.",
            "Do not treat a refined parent as independently UNRESOLVED merely because children differ.",
            "",
            "## HYPOTHESIS",
            "",
            "H1: parent becomes REFINED when heterogeneity is demonstrated. H2: local SOURCE_ESTABLISHED and MODEL_GENERALIZATION can share a relation family with different admission.",
        ]
    )


def master_md(summary: dict, label: str) -> str:
    compact = summary.get("compactness") or []
    n_occ_geo = next((r.get("parent_occurrences") for r in compact if "geometric_mean" in str(r.get("cell"))), None)
    lines = [
        "# Semantic Refinement & Admission Microprobe v1",
        "",
        f"Sealed interpretation: **{label}**",
        "",
        "Follow-up to Obligation-Driven Targeted Semantic Resolution Probe v1. Draft spine T5. Composer 2.5 only.",
        "GOLD and expected.json were not shown to the host. Not constructor promotion. Research metadata only (`REFINED` is not a kernel primitive).",
        "",
        "## Required answers",
        "",
        "### 1. When evidence reveals heterogeneous semantics, does the host mark the parent as REFINED rather than UNRESOLVED?",
        "",
        f"MEASURED parent_statuses={jdump(summary.get('parent_statuses'))}",
        f"protocol_drifts={summary.get('protocol_drifts')}",
        "",
        "### 2. Are child obligations reusable semantic questions rather than source-row special cases?",
        "",
        f"MEASURED compactness={jdump(compact)}",
        f"fragmented={summary.get('fragmented_cells')}",
        "",
        "### 3. Are partitions mechanically reconstructible?",
        "",
        "See refinement_results.md `mechanically_computable` per cell.",
        "",
        "### 4. Does geometric-mean refinement consistently recover TDS vs non-TDS?",
        "",
        f"MEASURED tds_split={jdump(summary.get('tds_split'))} recovered={summary.get('n_tds_recovered')}/3",
        "",
        "### 5. Does empty-numeric-limit refinement stay compact?",
        "",
        "See compactness rows for empty_numeric_limit. Flag OCCURRENCE_LEVEL_FRAGMENTATION only if unique-row children.",
        "",
        "### 6. Can individual children resolve while sibling children remain unresolved?",
        "",
        "See child disposition/admission mix in refinement_results.md (residual UNRESOLVED is allowed).",
        "",
        "### 7. Does disposable propagation affect only the intended child population?",
        "",
        f"leakage={jdump(summary.get('leakage_flags') or {})} failed_dry={summary.get('failed_dry_runs')}",
        "",
        "### 8. Are there any parent/child admission contradictions?",
        "",
        f"MEASURED protocol_drifts={summary.get('protocol_drifts')} unsupported_child_closures={summary.get('unsupported_child_closures')}",
        "",
        "### 9–12. Document-role local vs general",
        "",
        "See document_admission_results.md.",
        f"broader_admissions={summary.get('broader_admissions')} local_underused={summary.get('local_underused')}",
        "",
        "### 13. Unsupported broader closures?",
        "",
        f"MEASURED {summary.get('broader_admissions') or []}",
        "",
        "### 14–15. Frontier compilation and scope vs admission",
        "",
        f"Interpretation: **{label}**. H1/H2 are supported only if refined parents are superseded and local vs general admission stays distinct.",
        "",
        "## Interpretation",
        "",
        f"**{label}**",
        "",
        "## STOP",
        "",
        "No constructor/kernel change. REFINED is research metadata only. No semantic-family taxonomy. No retrieval-architecture change. No UI. No P5. No fifth domain. No real-user study.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    summary = score()
    label = choose_label(summary)
    slim = {k: v for k, v in summary.items() if k != "cells"}
    (RUNS / "score.json").write_text(json.dumps({"label": label, **slim}, indent=2, default=str) + "\n", encoding="utf-8")
    write("refinement_results.md", refinement_md(summary))
    write("parent_child_states.md", parent_child_md(summary))
    write("document_admission_results.md", document_md(summary))
    write("disposable_deltas.md", deltas_md(summary))
    write("failure_analysis.md", failure_md(summary))
    write("semantic_refinement_admission_v1.md", master_md(summary, label))
    print(label, flush=True)


if __name__ == "__main__":
    main()
