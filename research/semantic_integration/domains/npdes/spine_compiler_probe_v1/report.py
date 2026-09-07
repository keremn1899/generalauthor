"""Sealed reports for Spine Compiler Probe v1."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.paths import FROZEN, REPORTS, RUNS


def _md_bool(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "n/a"


def write_reports(scored: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FROZEN / "triggerability.md", REPORTS / "triggerability_freeze.md")
    shutil.copy2(FROZEN / "construction_ir.md", REPORTS / "construction_ir.md")
    _trial_results(scored)
    _trigger_analysis(scored)
    _summary(scored)


def _trial_results(scored: dict) -> None:
    lines = [
        "# Trial results",
        "",
        "Labels: **MEASURED** unless marked OBSERVED or HYPOTHESIS.",
        "",
        f"Model: Composer 2.5. Structurally valid trials: {scored['n_structurally_valid']}/{scored['n_trials']}.",
        "",
        "| Trial | valid | iters | groups | instances | E1 | E4 distinctions | TDS | authority |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for trial in scored.get("trials") or []:
        lines.append(
            "| {trial} | {valid} | {iters} | {groups} | {inst} | {e1} | {e4}/9 | {tds} | {auth} |".format(
                trial=trial["trial"],
                valid=_md_bool(trial.get("structurally_valid")),
                iters=trial.get("n_iterations"),
                groups=trial.get("n_trigger_groups"),
                inst=trial.get("n_trigger_instances"),
                e1=f"{trial.get('e1_recall'):.2f}" if trial.get("e1_recall") is not None else "n/a",
                e4=trial.get("e4_n_true"),
                tds=(trial.get("tds") or {}).get("status"),
                auth=_md_bool((trial.get("authority") or {}).get("trigger")),
            )
        )
    lines.extend(["", "## Per-trial programs", ""])
    for trial in scored.get("trials") or []:
        summary = trial.get("program_summary") or {}
        lines.extend(
            [
                f"### {trial['trial']}",
                "",
                f"- referents {summary.get('n_referents')}, maps {summary.get('n_maps')}, "
                f"relations {summary.get('n_relations')}, requirements {summary.get('n_requirements')}",
                f"- relations: {', '.join(str(x) for x in (summary.get('relation_names') or [])[:24])}",
                f"- requirements: {', '.join(str(x) for x in (summary.get('requirement_ids') or [])[:24])}",
                f"- row counts: `{json.dumps(trial.get('relation_row_counts') or {})}`",
                "",
            ]
        )
    (REPORTS / "trial_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _trigger_analysis(scored: dict) -> None:
    lines = [
        "# Trigger analysis",
        "",
        "Primary E1 excludes PROSE_ORIGINATING. Grain warning: trigger groups are not P3 obligations and not B3 nominations.",
        "",
        f"Mean E1 recall: **{scored.get('e1_mean_recall'):.2f}** over 7 primary seams.",
        f"Mean trigger groups: **{scored.get('e2_mean_trigger_groups'):.1f}**; "
        f"mean instances: **{scored.get('e2_mean_trigger_instances'):.1f}**.",
        "",
        "## Special traces (hits / trials)",
        "",
        "| gold_id | hits |",
        "|---|---|",
    ]
    for gid, row in (scored.get("special_traces") or {}).items():
        lines.append(f"| {gid} | {row['hits']}/{row['n']} |")
    lines.extend(
        [
            "",
            "## E1 per primary seam per trial",
            "",
            "Primary set: STRUCTURE_TRIGGERABLE + SOURCE_METADATA_TRIGGERABLE.",
            "",
        ]
    )
    primary_ids = [
        "S-FARM-TDS-STAGE",
        "S-FARM-REPORT-ONLY",
        "S-AZTEC-WHEN-DISCHARGING",
        "S-AZTEC-REPORT-ONLY",
        "S-GCC-EVENT-DISCHARGE",
        "S-GCC-REPORT-ONLY",
        "S-SOURCE-AUTHORITY",
    ]
    header = "| seam | " + " | ".join(t["trial"] for t in scored.get("trials") or []) + " |"
    sep = "|" + "|".join(["---"] * (1 + len(scored.get("trials") or []))) + "|"
    lines.extend([header, sep])
    for gid in primary_ids:
        cells = []
        for trial in scored.get("trials") or []:
            hit = ((trial.get("per_seam") or {}).get(gid) or {}).get("hit")
            cells.append("Y" if hit else "n")
        lines.append("| " + gid + " | " + " | ".join(cells) + " |")
    lines.extend(["", "## E3 selectivity per trial", ""])
    for trial in scored.get("trials") or []:
        lines.append(
            f"- {trial['trial']}: {trial.get('e3_counts')} purpose-relevant rate "
            f"{trial.get('e3_purpose_relevant_rate')} irrelevant rate {trial.get('e3_irrelevant_rate')}"
        )
    lines.extend(["", "## E5 distinction stability", "", "```json", json.dumps(scored.get("e5"), indent=2), "```", ""])
    (REPORTS / "trigger_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary(scored: dict) -> None:
    baselines = scored.get("e2_baselines") or {}
    p3 = baselines.get("p3_obligation_counts") or {}
    trials = scored.get("trials") or []
    mean_e1 = scored.get("e1_mean_recall")
    mean_groups = scored.get("e2_mean_trigger_groups")
    mean_inst = scored.get("e2_mean_trigger_instances")
    n_valid = scored.get("n_structurally_valid")
    mean_iters = (sum(t.get("n_iterations") or 0 for t in trials) / len(trials)) if trials else None
    tds_hits = (scored.get("special_traces") or {}).get("S-FARM-TDS-STAGE", {})
    auth_hits = (scored.get("special_traces") or {}).get("S-SOURCE-AUTHORITY", {})
    rel_fracs = [t.get("e3_purpose_relevant_rate") for t in trials if t.get("e3_purpose_relevant_rate") is not None]
    mean_rel = sum(rel_fracs) / len(rel_fracs) if rel_fracs else None
    mean_e4 = scored.get("e4_mean_distinctions")
    label = scored.get("label")
    valid_trials = [t for t in trials if t.get("structurally_valid")]
    mean_e1_valid = (
        sum(t["e1_recall"] or 0 for t in valid_trials) / len(valid_trials) if valid_trials else None
    )
    when = (scored.get("special_traces") or {}).get("S-AZTEC-WHEN-DISCHARGING", {})
    gcc = (scored.get("special_traces") or {}).get("S-GCC-EVENT-DISCHARGE", {})
    answers = {
        1: (
            f"{n_valid}/{scored.get('n_trials')} trials produced a structurally valid program.json (MEASURED). "
            "T5 exhausted 3 compile/repair iterations on IR bind errors (`from needs >=2 relations`, then `expected relation.role`)."
        ),
        2: f"Mean compile/repair iterations used: {mean_iters} of max 3 (MEASURED). All five reported Composer 2.5 with 0 isolation leaks.",
        3: (
            "After a valid program, mapping, joins, cardinality, numeric/code checks, and trigger grouping are host-deterministic with no model "
            "(MEASURED by construction). T1/T2 materialized nonempty `candidate_limit` (1292 and 1004). "
            f"T3/T4 compiled but `candidate_limit` row count was 0 (MEASURED)."
        ),
        4: (
            f"Mean primary E1 recall {mean_e1:.2f} over 7 STRUCTURE/SOURCE_METADATA seams including T5=0 (MEASURED). "
            f"Mean over the 4 valid trials: {mean_e1_valid:.2f} (MEASURED, same scorer)."
        ),
        5: (
            f"Staged TDS trigger hits {tds_hits.get('hits')}/{tds_hits.get('n')} (MEASURED). "
            "T1/T2/T4: TRIGGER. T3: join produced 0 candidate rows so the dated TDS split was not evaluated. T5: no compile."
        ),
        6: (
            f"Source-authority trigger hits {auth_hits.get('hits')}/{auth_hits.get('n')} from document_inventory metadata only (MEASURED). "
            "T2 did not map `document_inventory.json`. No permit prose was in the workspace."
        ),
        7: f"Mean trigger groups {mean_groups:.1f} (MEASURED). Valid-only: T1=8 T2=8 T3=6 T4=5.",
        8: f"Mean trigger instances {mean_inst:.1f} (MEASURED). Valid-only range 138–2036.",
        9: (
            f"P3 obligation counts were {p3} (mean {baselines.get('p3_mean')}). "
            f"B3 was ~{baselines.get('b3_candidates_per_replicate_approx')} nominations/replicate. "
            "Unlike grains: P3 is per-row semantic obligations; B3 is passage nominations; here a trigger group is one "
            "(requirement, failure_kind, relation) bucket. Group counts (5–8) are far smaller than P3/B3 volumes; "
            "instance counts (hundreds–thousands) are the same order as P3 (MEASURED + unlike-grain warning)."
        ),
        10: (
            f"Mean purpose-relevant group fraction {mean_rel} among trials that emitted groups (OBSERVED; evaluator heuristic). "
            "Generic diagnostics that fire because a join is empty or a code is unknown are purpose-relevant in the weak sense "
            "that A/B/C cannot complete, but they are not seam-specific."
        ),
        11: (
            f"Mean E4 materialized distinction count {mean_e4}/9 (MEASURED with OBSERVED rule: uncompiled T5 = 0; "
            "derived joins with 0 rows do not count as candidate_links). "
            "T1/T2 low-to-moderate group counts sit on nonempty candidate spines (compression). "
            "T3/T4 low instance/group counts sit on failed candidate joins (under-modeling of correspondence), not a strong spine."
        ),
        12: (
            "Independently authored programs shared the Measurement/Limit/candidate_limit shape and applicable_limit ONE, "
            "but names, maps, and whether document inventory was included differed (OBSERVED). "
            f"E5: document_metadata stable={((scored.get('e5') or {}).get('distinctions') or {}).get('document_metadata')}; "
            "relation names not identical."
        ),
        13: (
            "Host agent: choose referents, column maps, join predicates, interval_contains, and purpose requirements (OBSERVED). "
            "Repair iterations were spent on IR schema (unary `from`, missing roles, bad where refs), not on gold."
        ),
        14: (
            "Deterministic runtime: CSV/JSON load, referent ids, binary joins, interval_contains, cardinality, "
            "require_numeric, require_interpreted_code, grouping (MEASURED by construction)."
        ),
        15: (
            "The evidence does **not** support replacing current P1–P4. T1 shows the shape can work; T3–T5 show "
            "correspondence and IR reliability are not yet constructor-grade (HYPOTHESIS: later probe, not a promotion)."
        ),
        16: f"Sealed label: **{label}**.",
    }
    lines = [
        "# Spine Compiler Probe v1",
        "",
        f"Sealed interpretation: **{label}**",
        "",
        "This is a research probe. It is not Constructor v3.2. TaskView/kernel, P3, P5, and sealed prose probes were not modified.",
        "",
        "## MEASURED headline",
        "",
        f"- structurally valid: {n_valid}/{scored.get('n_trials')}",
        f"- E1 mean recall: {mean_e1:.2f}",
        f"- E2 mean groups/instances: {mean_groups:.1f} / {mean_inst:.1f}",
        f"- E4 mean distinctions: {mean_e4}/9",
        f"- when-discharging hits: {when.get('hits')}/{when.get('n')}",
        f"- GCC event-discharge hits: {gcc.get('hits')}/{gcc.get('n')}",
        "",
        "## OBSERVED",
        "",
        "T1 is the existence proof: nonempty candidate_limit, TDS trigger, report-only via COMPARISON_OPERATOR_REQUIRED, "
        "source-authority via document cardinality, GCC event via uninterpreted NODI. "
        "T3/T4 authored similar requirements but their measurement–limit joins materialized 0 rows, so most primary seams "
        "could not fire. T5 never bound. `S-AZTEC-WHEN-DISCHARGING` was 0/5: DMR_COMMENT_TEXT `WHEN DISCHARGING.` was "
        "visible in permit_limits.csv and no trial required that field as an interpreted code.",
        "",
        "## HYPOTHESIS",
        "",
        "A programmed spine can compress attention relative to P3/B3 **when the join actually materializes**. "
        "Compile-repair on a tiny JSON IR is not yet a reliable substitute for multi-pass construction. "
        "Do not collapse P1–P4 on this evidence.",
        "",
        "## Required questions",
        "",
    ]
    for i in range(1, 17):
        lines.extend([f"### {i}", "", answers[i], ""])
    lines.extend(
        [
            "## What this does not license",
            "",
            "No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5 in this probe.",
            "",
        ]
    )
    (REPORTS / "spine_compiler_probe_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUNS / "answers.json").write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
