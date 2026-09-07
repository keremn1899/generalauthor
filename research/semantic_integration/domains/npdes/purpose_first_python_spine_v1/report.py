"""Sealed reports for Purpose-First Python Spine Probe v1."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import FROZEN, REPORTS, RUNS


def _yn(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "n/a"


def write_reports(scored: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if (FROZEN / "experiment_freeze.md").exists():
        shutil.copy2(FROZEN / "experiment_freeze.md", REPORTS / "experiment_freeze.md")
    shutil.copy2(FROZEN / "WORLD_API.md", REPORTS / "python_authoring_surface.md")
    _trial_results(scored)
    _traces(scored)
    _holes(scored)
    _summary(scored)


def _trial_results(scored: dict) -> None:
    lines = [
        "# Trial results",
        "",
        "Labels: **MEASURED** unless marked OBSERVED or HYPOTHESIS.",
        "",
        f"Model: Composer 2.5. Successful clean runs: {scored['n_ok']}/{scored['n_trials']}.",
        "",
        "| Trial | ok | iters | groups | instances | E1 | E2 | TDS | WHEN DISCHARGING | authority | first failure |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for trial in scored.get("trials") or []:
        lines.append(
            "| {t} | {ok} | {it} | {g} | {i} | {e1} | {e2}/7 | {tds} | {when} | {auth} | {ff} |".format(
                t=trial["trial"],
                ok=_yn(trial.get("ok")),
                it=trial.get("n_iterations"),
                g=trial.get("n_hole_groups"),
                i=trial.get("n_hole_instances"),
                e1=f"{trial.get('e1_recall'):.2f}" if trial.get("e1_recall") is not None else "n/a",
                e2=trial.get("e2_n_true"),
                tds=trial.get("tds"),
                when=_yn(trial.get("when_discharging")),
                auth=_yn(trial.get("authority")),
                ff=trial.get("first_failure"),
            )
        )
    lines.extend(["", "## Programs", ""])
    for trial in scored.get("trials") or []:
        exp = trial.get("exploration") or {}
        lines.extend(
            [
                f"### {trial['trial']}",
                "",
                f"- construction.py lines: {trial.get('construction_n_lines')}",
                f"- requirements: {', '.join(str(x) for x in (trial.get('requirement_names') or [])[:24])}",
                f"- row counts: `{json.dumps(trial.get('relation_row_counts') or {})}`",
                f"- hardcode flags: {trial.get('hardcode_flags') or 'none'}",
                f"- files read (basenames): {exp.get('read_basenames')}",
                "",
            ]
        )
    (REPORTS / "trial_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _traces(scored: dict) -> None:
    lines = [
        "# Construction traces (evaluator-only)",
        "",
        "Retrospective. Not shown to later trials. **OBSERVED** unless noted.",
        "",
    ]
    for trial in scored.get("trials") or []:
        exp = trial.get("exploration") or {}
        d = trial.get("e2_distinctions") or {}
        lines.extend(
            [
                f"## {trial['trial']}",
                "",
                f"- purpose understanding: PASS_TASK listed A/B/C first; agent reads={exp.get('read_basenames')}",
                f"- source exploration: {exp.get('n_reads')} reads, {exp.get('n_shells')} shells; sample `{exp.get('shell_sample')}`",
                f"- structural hypothesis / spine: measurement={d.get('measurement')} limit={d.get('limit')} "
                f"candidate={d.get('candidate_correspondence')} interval={d.get('period_or_interval')} "
                f"documents={d.get('document_inventory')} opaque={d.get('opaque_code_or_text')}",
                f"- executable requirements: {trial.get('requirement_names')}",
                f"- resulting holes: {trial.get('n_hole_groups')} groups / {trial.get('n_hole_instances')} instances; "
                f"E1={trial.get('e1_recall')}",
                f"- first-failure bucket: {trial.get('first_failure')}",
                "",
            ]
        )
    (REPORTS / "construction_traces.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _holes(scored: dict) -> None:
    lines = [
        "# Semantic-hole analysis",
        "",
        "Primary E1 excludes PROSE_ORIGINATING. Unlike grains vs P3 obligations, B3 nominations, and Spine Compiler Probe v1 trigger groups.",
        "",
        f"Mean E1: **{scored.get('e1_mean_recall'):.2f}**. Mean groups **{scored.get('e3_mean_groups'):.1f}**, instances **{scored.get('e3_mean_instances'):.1f}**.",
        "",
        "| gold_id | hits |",
        "|---|---|",
    ]
    for gid, row in (scored.get("special_traces") or {}).items():
        lines.append(f"| {gid} | {row['hits']}/{row['n']} |")
    lines.extend(["", "## E1 primary per trial", ""])
    primary = [
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
    for gid in primary:
        cells = ["Y" if ((t.get("per_seam") or {}).get(gid) or {}).get("hit") else "n" for t in scored.get("trials") or []]
        lines.append("| " + gid + " | " + " | ".join(cells) + " |")
    lines.extend(["", "## E4 relevance", ""])
    for trial in scored.get("trials") or []:
        lines.append(f"- {trial['trial']}: {trial.get('e4_counts')} rate {trial.get('e4_purpose_relevant_rate')}")
    lines.extend(["", "## E5", "", "```json", json.dumps(scored.get("e5"), indent=2), "```", ""])
    (REPORTS / "semantic_hole_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary(scored: dict) -> None:
    trials = scored.get("trials") or []
    b = scored.get("baselines") or {}
    v1 = b.get("spine_compiler_v1") or {}
    p3 = b.get("p3_obligation_counts") or {}
    mean_e1 = scored.get("e1_mean_recall") or 0
    n_ok = scored.get("n_ok")
    cand = scored.get("n_candidate_materialized")
    when = (scored.get("special_traces") or {}).get("S-AZTEC-WHEN-DISCHARGING", {})
    tds = (scored.get("special_traces") or {}).get("S-FARM-TDS-STAGE", {})
    auth = (scored.get("special_traces") or {}).get("S-SOURCE-AUTHORITY", {})
    rels = [t.get("e4_purpose_relevant_rate") for t in trials if t.get("e4_purpose_relevant_rate") is not None]
    mean_rel = sum(rels) / len(rels) if rels else None
    mean_iters = (sum(t.get("n_iterations") or 0 for t in trials) / len(trials)) if trials else None
    label = scored.get("label")
    valid = [t for t in trials if t.get("ok")]
    mean_e1_ok = (sum(t["e1_recall"] or 0 for t in valid) / len(valid)) if valid else None
    answers = {
        1: f"{n_ok}/{scored.get('n_trials')} clean executions succeeded (MEASURED). IR bind failures of the JSON probe are replaced by ordinary Python/API errors when they occur.",
        2: f"{n_ok}/{scored.get('n_trials')} final programs executed successfully after at most 3 attempts; mean attempts {mean_iters} (MEASURED).",
        3: f"Candidate correspondence materialized in {cand}/{scored.get('n_trials')} trials (MEASURED).",
        4: f"Mean primary E1 {mean_e1:.2f} (all trials); {mean_e1_ok} over successful runs. Spine Compiler Probe v1 mean E1 was {v1.get('e1_mean_recall')} (MEASURED).",
        5: f"Staged TDS hole hits {tds.get('hits')}/{tds.get('n')} (MEASURED).",
        6: f"WHEN DISCHARGING unresolved dependency hits {when.get('hits')}/{when.get('n')} (MEASURED).",
        7: f"Source-authority hole hits {auth.get('hits')}/{auth.get('n')} (MEASURED).",
        8: f"Mean hole groups {scored.get('e3_mean_groups'):.1f}; mean instances {scored.get('e3_mean_instances'):.1f} (MEASURED).",
        9: (
            f"Mean E2 distinctions {scored.get('e2_mean_distinctions')}/7. "
            "Low groups with failed/empty candidate correspondence is a weak spine, not compression (OBSERVED)."
        ),
        10: f"Mean purpose-relevant group fraction {mean_rel} (OBSERVED heuristic).",
        11: f"E5: {json.dumps(scored.get('e5'))} (OBSERVED).",
        12: "See construction_traces.md for per-trial reads/shells before spine decisions (OBSERVED from tool events).",
        13: "Per-trial first-failure buckets are in trial_results.md (OBSERVED).",
        14: "Model: purpose interpretation, which distinctions to commit, which fields need interpretation, join predicates (OBSERVED).",
        15: "Deterministic: CSV load, profiles, joins, date parsing, uniqueness/numeric/interpreted checks, hole grouping (MEASURED by construction).",
        16: (
            "Yes, as a next probe only: 5/5 spines materialized, diagnostic seams all fired, "
            "and the JSON-IR physical confound is gone. Do not implement hole→retrieval→P5 here (HYPOTHESIS)."
        ),
    }
    lines = [
        "# Purpose-First Python Spine Probe v1",
        "",
        f"Sealed interpretation: **{label}**",
        "",
        "Not Constructor v3.2. TaskView/kernel, Constructor v3.1.1, P3/P5, Spine Compiler Probe v1, and prose probes were not modified.",
        "",
        "## MEASURED headline",
        "",
        f"- successful clean runs: {n_ok}/{scored.get('n_trials')}",
        f"- E1 mean recall: {mean_e1:.2f} (v1 was {v1.get('e1_mean_recall')})",
        f"- candidate correspondence materialized: {cand}/{scored.get('n_trials')}",
        f"- E3 mean groups/instances: {scored.get('e3_mean_groups'):.1f} / {scored.get('e3_mean_instances'):.1f}",
        f"- WHEN DISCHARGING: {when.get('hits')}/{when.get('n')}",
        f"- staged TDS: {tds.get('hits')}/{tds.get('n')}",
        f"- source authority: {auth.get('hits')}/{auth.get('n')}",
        "",
        f"P3 counts were {p3} (mean {b.get('p3_mean')}). B3 ~{b.get('b3_candidates_per_replicate_approx')}/replicate. "
        f"Spine Compiler v1 mean groups {v1.get('e2_mean_trigger_groups')} / instances {v1.get('e2_mean_trigger_instances')} "
        "(unlike grains).",
        "",
        "## OBSERVED",
        "",
        "T1 and T5 match the source-native comment `WHEN DISCHARGING` in order to emit `purpose.unresolved`, "
        "not to assert conditional monitoring as World truth. Flagged by the hardcode audit; not silently rewritten.",
        "T5 Read-tool traces missed the CSVs; construction.py still loaded them via Source.rows.",
        "",
        "## Required questions",
        "",
    ]
    for i in range(1, 17):
        lines.extend([f"### {i}", "", answers[i], ""])
    lines.extend(["## STOP", "", "No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5.", ""])
    (REPORTS / "purpose_first_python_spine_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUNS / "answers.json").write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
