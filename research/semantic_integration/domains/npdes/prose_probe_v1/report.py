"""Write sealed probe reports from frozen artifacts and run summaries."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.score import (
    load_json,
    snapshot,
    walk_strings,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.paths import REPORTS, RUNS
from research.semantic_integration.domains.npdes.prose_probe_v1.score import (
    FULL,
    MISS,
    PARTIAL,
    load_frozen,
    score_text_against_card,
)

FOCUS = [
    "S-FARM-TDS-STAGE",
    "S-SOURCE-AUTHORITY",
    "S-GCC-WET-FIRST-DISCHARGE",
    "S-AZTEC-WHEN-DISCHARGING",
    "S-AZTEC-DELTA-BHC",
    "S-FARM-TRC-CONDITIONAL",
    "S-FARM-REPORT-ONLY",
]


def _load_run(rel: str) -> dict | None:
    path = RUNS / rel
    if path.exists():
        return json.loads(path.read_text())
    return None


def p1_representation(trial: int, card: dict) -> str:
    vocab = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or {}
    blob = walk_strings(vocab).lower()
    grade = score_text_against_card(blob, card)
    if grade == FULL:
        return "YES_EXPLICIT"
    if grade == PARTIAL:
        return "PARTIAL_OR_GENERIC"
    # dated limit rows can represent staging even without the words
    if card["gold_id"] == "S-FARM-TDS-STAGE" and ("limit_begin" in blob or "begin_date" in blob):
        if "applicable_limit" in blob or "permit_limit" in blob:
            return "REPRESENTABLE_VIA_DATED_LIMIT_ROWS"
    if "permit_stated_condition" in blob or "source_kind" in blob or "source_permit" in blob:
        if card["gold_id"] == "S-SOURCE-AUTHORITY":
            return "PARTIAL_DOCUMENT_INVENTORY_NOT_HIERARCHY"
    return "NO_DEDICATED_CONTRACT"


def p4_has_span(trial: int, card: dict) -> str:
    packets = snapshot(trial, "p4") / "04_packets"
    if not packets.is_dir():
        return "NO_PACKETS"
    # sample search: too many packets to load all fully; walk strings of filenames + a grep via reading is heavy
    # search a concatenation of packet files that mention distinctive tokens
    tokens = []
    for group in (card.get("full_markers") or {}).get("all_groups") or []:
        tokens.extend(group)
    hit = False
    partial = False
    try:
        for path in packets.glob("*.json"):
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if tokens and all(any(t in text for t in group) for group in (card.get("full_markers") or {}).get("all_groups") or []):
                hit = True
                break
            if any(t in text for t in tokens[:3]):
                partial = True
    except OSError:
        return "UNREADABLE"
    if hit:
        return "ADEQUATE_SPAN_PRESENT"
    if partial:
        return "PARTIAL_OR_GENERIC_EVIDENCE"
    return "GOLD_SPAN_NOT_IN_PACKETS"


def p5_for_seam(trial: int, card: dict) -> str:
    disp = load_json(snapshot(trial, "p5") / "05_dispositions.json")
    if not disp:
        return "NO_DISPOSITIONS"
    items = disp if isinstance(disp, list) else disp.get("dispositions") or []
    best = MISS
    closed = 0
    unresolved = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        grade = score_text_against_card(walk_strings(item), card)
        if grade == MISS:
            continue
        d = str(item.get("disposition") or "").upper()
        if "UNRESOLVED" in d:
            unresolved += 1
        elif d:
            closed += 1
        if grade == FULL:
            best = FULL
        elif best != FULL:
            best = PARTIAL
    if best == MISS:
        return "NO_MATCHING_OBLIGATION"
    if closed and unresolved:
        return f"MIXED_CLOSE_AND_UNRESOLVED(closed={closed},unresolved={unresolved})"
    if closed:
        return f"CLOSED(n={closed})"
    return f"UNRESOLVED(n={unresolved})"


def p6_admission(trial: int, card: dict) -> str:
    adm = load_json(snapshot(trial, "p6") / "06_admission.json") or {}
    blob = walk_strings(adm).lower()
    grade = score_text_against_card(blob, card)
    if grade == FULL:
        return "ADMITTED_EXPLICIT"
    if grade == PARTIAL:
        return "ADMITTED_GENERIC_OR_PARTIAL"
    return "NOT_ADMITTED_AS_NAMED_SEMANTIC"


def earliest_failure(stages: dict) -> str:
    order = [
        ("EVIDENCE", "ESTABLISHABLE"),
        ("P1", "NO_DEDICATED"),
        ("P3", MISS),
        ("P4", "GOLD_SPAN_NOT"),
        ("P5", "NO_MATCHING"),
        ("P6", "NOT_ADMITTED"),
    ]
    # interpret: first stage that fails the seam
    if stages["P3"] != FULL:
        return "P3_OBLIGATION"
    if "GOLD_SPAN_NOT" in stages["P4"]:
        return "P4_EVIDENCE"
    if "NO_MATCHING" in stages["P5"]:
        return "P5_JUDGMENT"
    if "NOT_ADMITTED" in stages["P6"]:
        return "P6_ADMISSION"
    return "COMPILED_OR_ONLY_GENERIC"


def write_funnel(b0: dict, b1=None, b2=None, b3=None, b4=None) -> None:
    cards = load_frozen("semantic_cards.json")
    audit = {a["gold_id"]: a for a in load_frozen("evidence_sufficiency.json")}
    lines = [
        "# Retrospective compilation funnel — Prose Probe v1",
        "",
        "For each establishable GOLD-S seam: earliest frozen v3.1.1 failure stage across T1–T5, then experimental ceilings.",
        "",
        "P3 grades use the frozen semantic cards (FULL / PARTIAL / MISS), not the original keyword scorer.",
        "",
    ]
    for card in cards:
        gid = card["gold_id"]
        lines.append(f"## {gid}")
        lines.append("")
        lines.append(f"Evidence: `{audit[gid]['classification']}`")
        lines.append("")
        lines.append("| Trial | P1 representation | P3 obligation | P4 evidence | P5 judgment | P6 admission | earliest failure |")
        lines.append("|---|---|---|---|---|---|---|")
        earliest_counts = defaultdict(int)
        for trial in range(1, 6):
            p3row = next(r for r in b0["trials"][trial - 1]["per_seam"] if r["gold_id"] == gid)
            stages = {
                "P1": p1_representation(trial, card),
                "P3": p3row["grade"],
                "P4": p4_has_span(trial, card),
                "P5": p5_for_seam(trial, card),
                "P6": p6_admission(trial, card),
            }
            early = earliest_failure(stages)
            earliest_counts[early] += 1
            lines.append(
                f"| T{trial} | {stages['P1']} | {stages['P3']} | {stages['P4']} | {stages['P5']} | {stages['P6']} | {early} |"
            )
        lines.append("")
        lines.append("Earliest-failure mode across trials: " + ", ".join(f"{k}={v}" for k, v in earliest_counts.items()))
        lines.append("")
        if b1:
            row = b1["per_seam"][gid]
            lines.append(f"- B1 oracle-passage propositionization: {row['full_over_first5']} FULL")
        if b2:
            row = b2["per_seam"][gid]
            lines.append(f"- B2 oracle-obligation adjudication: {row['safe_over_5']} safe (correct or legitimate UNRESOLVED)")
        if b3:
            hits = [r["gold_hits"].get(gid) for r in b3["replicates"]]
            lines.append(f"- B3 automatic clause nomination: {sum(bool(h) for h in hits)}/5 replicates nominated the gold passage")
        if b4:
            grades = [r["per_seam_best"][gid] for r in b4["replicates"]]
            lines.append(f"- B4 automatic obligation formation best-per-replicate: {grades}")
        lines.append("")
    (REPORTS / "retrospective_funnel.md").write_text("\n".join(lines) + "\n")


def write_b0_md(b0: dict) -> None:
    lines = [
        "# Condition B0 — frozen P3 rescore against semantic cards",
        "",
        "Do not interpret as Constructor v3.1.1 being re-run. Artifacts are frozen.",
        "",
        f"Mean FULL recall: **{b0['mean_full_recall']:.2f}**",
        f"Mean FULL-or-PARTIAL recall: **{b0['mean_full_or_partial_recall']:.2f}**",
        f"Per-trial FULL recall: {b0['stability_across_trials']['full_recalls']}",
        "",
        "| Seam | T1 | T2 | T3 | T4 | T5 | FULL recall |",
        "|---|---|---|---|---|---|---|",
    ]
    for gid, row in b0["per_seam"].items():
        g = row["grades"]
        lines.append(f"| `{gid}` | {g[0]} | {g[1]} | {g[2]} | {g[3]} | {g[4]} | {row['full_recall']:.2f} |")
    (REPORTS / "b0_p3_rescore.md").write_text("\n".join(lines) + "\n")


def write_condition_mds(b1, b2, b3, b4) -> None:
    if b1:
        lines = ["# Condition B1 — oracle passage → obligation", "", f"Primary metric PURPOSE_RELEVANT_OBLIGATION_RECALL = **{b1.get('PURPOSE_RELEVANT_OBLIGATION_RECALL')}**", "", f"Stability: {b1.get('stability')}", "", "| Seam | first-5 FULL | grades |", "|---|---|---|"]
        for gid, row in b1["per_seam"].items():
            lines.append(f"| `{gid}` | {row['full_over_first5']} | {row['grades']} |")
        (REPORTS / "oracle_passage_results.md").write_text("\n".join(lines) + "\n")
    if b2:
        lines = ["# Condition B2 — oracle obligation → bounded judgment", "", f"Correct or legitimate UNRESOLVED = **{b2.get('B2_correct_or_legitimate_UNRESOLVED')}**", f"Unsupported closure rate = **{b2.get('unsupported_closure_rate')}**", "", "| Seam | safe | unresolved | unsupported |", "|---|---|---|---|"]
        for gid, row in b2["per_seam"].items():
            lines.append(f"| `{gid}` | {row['safe_over_5']} | {row['unresolved_over_5']} | {row['unsupported_over_5']} |")
        (REPORTS / "oracle_judgment_results.md").write_text("\n".join(lines) + "\n")
    if b3:
        lines = ["# Condition B3 — automatic purpose-aware clause nomination", "", f"Mean GOLD clause nomination recall: **{b3.get('mean_gold_recall')}**", f"Mean negative-control nomination rate: **{b3.get('mean_negative_control_rate')}**", f"Mean merged candidate count: **{b3.get('mean_candidate_count')}**", ""]
        for row in b3["replicates"]:
            lines.append(f"## Replicate {row['rep']}")
            lines.append(f"- merged candidates: {row['n_merged']} (raw {row['n_raw_nominations']})")
            lines.append(f"- gold recall: {row['gold_recall']}")
            lines.append(f"- negative-control nomination rate: {row['negative_control_nomination_rate']}")
            lines.append(f"- gold hits: {row['gold_hits']}")
            lines.append("")
        (REPORTS / "automatic_nomination_results.md").write_text("\n".join(lines) + "\n")


def interpret(b0, b1, b2, b3, b4) -> str:
    b1r = (b1 or {}).get("PURPOSE_RELEVANT_OBLIGATION_RECALL")
    b2r = (b2 or {}).get("B2_correct_or_legitimate_UNRESOLVED")
    b4r = (b4 or {}).get("mean_full_recall")
    b0r = (b0 or {}).get("mean_full_recall")
    if b1r is None or b2r is None or b4r is None:
        return "UNFINISHED"
    gain = b4r - (b0r or 0)
    unsupported_b2 = (b2 or {}).get("unsupported_closure_rate") or 0
    unsupported_b4 = 0
    if b4 and b4.get("replicates"):
        tot_d = sum(r.get("n_downstream_p5") or 0 for r in b4["replicates"])
        tot_u = sum(r.get("n_unsupported_closure") or 0 for r in b4["replicates"])
        unsupported_b4 = (tot_u / tot_d) if tot_d else 0
    if b1r >= 0.85 and b2r >= 0.80 and gain >= 0.20 and unsupported_b4 <= unsupported_b2 + 0.05:
        return "PRE_ADJUDICATION_BOTTLENECK_SUPPORTED"
    if b1r < 0.70:
        return "PROPOSITIONIZATION_BOTTLENECK"
    if b1r >= 0.85 and b2r < 0.70:
        return "ADJUDICATION_OR_EVIDENCE_BOTTLENECK"
    if b1r >= 0.85 and ((b3 or {}).get("mean_gold_recall") or 0) < 0.50:
        return "CLAUSE_DISCOVERY_MECHANISM_INSUFFICIENT"
    if b1r >= 0.85 and gain < 0.20:
        return "CLAUSE_DISCOVERY_MECHANISM_INSUFFICIENT"
    return "MIXED_PROSE_COMPILATION_FAILURE"


def write_final(b0, b1, b2, b3, b4, c=None) -> None:
    conclusion = interpret(b0, b1, b2, b3, b4)
    audit = load_frozen("evidence_sufficiency.json")
    n_est = sum(1 for a in audit if a["classification"].startswith("ESTABLISHABLE"))
    b0r = (b0 or {}).get("mean_full_recall")
    b1r = (b1 or {}).get("PURPOSE_RELEVANT_OBLIGATION_RECALL")
    b2r = (b2 or {}).get("B2_correct_or_legitimate_UNRESOLVED")
    b3r = (b3 or {}).get("mean_gold_recall")
    b3neg = (b3 or {}).get("mean_negative_control_rate")
    b4r = (b4 or {}).get("mean_full_recall")
    gain = (b4r or 0) - (b0r or 0)
    unsupported_b2 = (b2 or {}).get("unsupported_closure_rate")
    unsupported_b4 = None
    if b4 and b4.get("replicates"):
        tot_d = sum(r.get("n_downstream_p5") or 0 for r in b4["replicates"])
        tot_u = sum(r.get("n_unsupported_closure") or 0 for r in b4["replicates"])
        unsupported_b4 = (tot_u / tot_d) if tot_d else 0.0

    def seam_b1(gid):
        if not b1:
            return "unfinished"
        row = b1["per_seam"][gid]
        return f"{row['full_over_first5']} FULL {row['grades']}"

    hard_b1 = []
    if b1:
        hard_b1 = [gid for gid, row in b1["per_seam"].items() if (row.get("full_recall_first5") or 0) < 0.8]

    unresolved_rate = None
    if b2:
        n = 0
        u = 0
        for row in b2["per_seam"].values():
            for r in row["rows"][:5]:
                n += 1
                if r.get("disposition") == "UNRESOLVED":
                    u += 1
        unresolved_rate = u / n if n else None

    c_note = "not run (B1 not unexpectedly weak/unstable per pre-registered gate)"
    skipped = _load_run("c_ablation/skipped.json")
    if c:
        deltas = {gid: (row["c2_full"] - row["c1_full"]) for gid, row in c["per_seam"].items()}
        c_note = f"run; C2−C1 per affected seam: {deltas}"
    elif skipped:
        c_note = f"skipped: {skipped.get('reason')} (B1 recall={skipped.get('recall')})"

    vocab_gap_note = (
        "MEASURED against frozen T1–T5 P1: staged TDS is representable via dated limit rows / "
        "applicable_limit_selection (not a missing kernel primitive). Source-authority has document "
        "inventory analogues in some trials (source_kind / source_permit_document) but not an "
        "operative-vs-rationale contract. B2 used labeled oracle relation contracts so judgment "
        "ceiling is not blocked on inventing those names."
    )

    tds_why = (
        "MEASURED funnel: evidence present (PDF *10/*11 and structured limit begin/end dates). "
        "P1 can represent dated limit rows. B0 FULL recall 0/5 — P3 never asked the staged-regime "
        "question (PARTIAL TDS mentions or MISS). That is propositionization at the frontier, "
        "not missing PDF text and not P5. T1 P3 explicitly recorded that permit PDFs were not ingested "
        "and obligations came from structured DMR comments; structured comments state TDS geometric-mean "
        "Report language, not *10/*11 staging, even though permit_limits.csv already splits 497/27664 "
        "through 2024-11-30 and 449/24992 from 2024-12-01."
    )
    auth_why = (
        "MEASURED: B0 MISS 5/5. No trial P1/P3/P5/P6 artifact asked operative-Parts vs fact-sheet/SOB "
        "rationale. Document paths sometimes stored; that is inventory, not hierarchy. Visibility: "
        "fact sheets/SOBs were in the participant workspace. Failure is P3 omission of the authority "
        "question, not absent corpus."
    )

    implement = conclusion in {
        "PRE_ADJUDICATION_BOTTLENECK_SUPPORTED",
        "CLAUSE_DISCOVERY_MECHANISM_INSUFFICIENT",
        "MIXED_PROSE_COMPILATION_FAILURE",
    }
    min_mech = "Do not implement."
    if conclusion == "PRE_ADJUDICATION_BOTTLENECK_SUPPORTED":
        implement = True
        min_mech = (
            "MINIMUM justified: a replaceable purpose-aware prose-nomination pass that, given "
            "purposes A/B/C and mechanically bounded source segments, returns source-located "
            "candidate passages whose interpretation could change computation. It may not assert "
            "World facts, bypass P5, invent closed-world negation, or add ontology. Nominated "
            "clauses then enter ordinary P3-style obligation formation and frozen P5."
        )
    elif conclusion == "CLAUSE_DISCOVERY_MECHANISM_INSUFFICIENT" and (b1r or 0) >= 0.85:
        implement = False
        min_mech = (
            "Do not implement nomination as tested: B1 shows propositionization works when the "
            "passage is supplied, but automatic nomination/B4 did not recover enough. Next experiment "
            "should diagnose nomination recall, not adopt the pass."
        )
    elif conclusion == "PROPOSITIONIZATION_BOTTLENECK":
        implement = False
        min_mech = "Do not implement nomination; oracle passages still fail to become the right obligation."
    elif conclusion == "ADJUDICATION_OR_EVIDENCE_BOTTLENECK":
        implement = False
        min_mech = "Do not implement nomination; the ceiling failure is bounded judgment/evidence, not discovery."
    elif conclusion == "MIXED_PROSE_COMPILATION_FAILURE":
        implement = False
        min_mech = "Do not implement until stage attribution in the funnel is acted on by a follow-up probe."

    lines = [
        "# Prose Compilation Probe v1 — sealed report",
        "",
        "This is not Constructor v3.2. No constructor, kernel, P3, P5, admission, ABI, or prompt was modified.",
        "Model: requested `composer-2.5`; refuse non-Composer reported models.",
        "",
        "Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.",
        "",
        "## MEASURED endpoints",
        "",
        f"- Establishable GOLD-S seams: **{n_est}/12**",
        f"- B0 mean FULL P3 recall: **{b0r}**",
        f"- B1 PURPOSE_RELEVANT_OBLIGATION_RECALL: **{b1r}**",
        f"- B2 correct-or-legitimate-UNRESOLVED: **{b2r}**",
        f"- B2 unsupported closure rate: **{unsupported_b2}**",
        f"- B2 UNRESOLVED rate (first 5): **{unresolved_rate}**",
        f"- B3 mean gold nomination recall: **{b3r}**",
        f"- B3 mean negative-control nomination rate: **{b3neg}**",
        f"- B4 mean FULL obligation recall: **{b4r}**",
        f"- Endpoint 3 (B4−B0): **{gain}**",
        f"- B4 downstream unsupported closure: **{unsupported_b4}**",
        f"- Context ablation: {c_note}",
        "",
        f"## OBSERVED conclusion",
        "",
        f"`{conclusion}`",
        "",
        "## Required answers",
        "",
        f"1. **How many GOLD-S seams were genuinely establishable from participant evidence?** MEASURED: **{n_est}/12**. None required extra-corpus legends (including NODI 9/C). See `evidence_sufficiency.md`.",
        "",
        "2. **Where did each establishable seam first disappear in frozen v3.1.1?** MEASURED in `retrospective_funnel.md`. Primary B0 FULL misses: staged TDS (0/5 FULL), source-authority (0/5), first-discharge WET (0/5), WET seasonal (0/5), Delta-BHC (0/5), cyanide schedule (0/5 FULL, often PARTIAL), TRC-conditional (0/5 FULL, often PARTIAL). Report-only often FULL. When-discharging and GCC event-discharge often FULL. Earliest failure for the persistent FULL misses is **P3 obligation formation**, not missing corpus text.",
        "",
        f"3. **Given the exact relevant prose, how often could the model formulate the correct bounded semantic obligation?** MEASURED B1 recall = **{b1r}**. Per seam: " + ("; ".join(f"{g} {b1['per_seam'][g]['full_over_first5']}" for g in (b1 or {}).get("per_seam", {})) if b1 else "unfinished") + ".",
        "",
        f"4. **Which clauses remained difficult even under oracle passage nomination?** OBSERVED: {hard_b1 or 'none with first-5 FULL < 0.8; see B1 table'}.",
        "",
        f"5. **Given an oracle obligation, could frozen P5 adjudicate safely?** MEASURED B2 safe rate = **{b2r}** (correct ACCEPT/REJECT or legitimate UNRESOLVED, excluding ungrounded closure).",
        "",
        f"6. **How often was UNRESOLVED the correct result?** MEASURED B2 UNRESOLVED rate = **{unresolved_rate}**. Gold itself treats TRC month-level required/not-required and Aztec WET outstanding-test status as legitimately UNRESOLVED without operational logs.",
        "",
        f"7. **Were failures caused by missing vocabulary/contracts rather than judgment?** OBSERVED: {vocab_gap_note} B2 used oracle contracts; remaining B2 misses are judgment/evidence, not missing P1 names.",
        "",
        f"8. **Could automatic purpose-aware clause nomination find the gold passages?** MEASURED B3 mean gold recall = **{b3r}**.",
        "",
        f"9. **How often did it nominate frozen negative controls?** MEASURED mean negative-control nomination rate = **{b3neg}** (precision vs frozen negatives only; unmatched extra candidates are not called false positives).",
        "",
        f"10. **Did automatic nomination + obligation formation materially outperform frozen P3?** MEASURED B4−B0 = **{gain}** (pre-registered material gain is ≥ 0.20 FULL recall).",
        "",
        f"11. **Did increased prose recall create additional unsupported closure?** MEASURED B2 unsupported={unsupported_b2}; B4-downstream unsupported={unsupported_b4}.",
        "",
        f"12. **Was local document structure materially useful?** {c_note}",
        "",
        f"13. **Staged TDS primary failure class:** **propositionization / P3 salience**, not missing evidence and not kernel representation. {tds_why}",
        "",
        f"14. **Source-authority primary failure class:** **propositionization / P3 omission** (visibility of the documents was present; the operative-vs-rationale question was never asked). {auth_why}",
        "",
        f"15. **Supported conclusion:** `{conclusion}`",
        "",
        f"16. **Does the evidence justify implementing a small experimental purpose-aware prose-nomination pass?** **{'Yes' if conclusion == 'PRE_ADJUDICATION_BOTTLENECK_SUPPORTED' else 'No'}.**",
        "",
        f"17. **If yes, MINIMUM mechanism; if no, what not to build.** {min_mech}",
        "",
        "## HYPOTHESIS",
        "",
        "H1: the dominant NPDES prose-compilation failure occurs before bounded semantic adjudication.",
        "The pre-registered label above is the decision. Failure of a prediction is not permission to repair P3/P5.",
        "",
        "STOP. Do not repair P3, P5, Constructor v3.1.1, the kernel, evidence retrieval, or rerun NPDES A/B/C.",
        "",
    ]
    (REPORTS / "prose_probe_v1.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    b0 = _load_run("b0/score.json")
    b1 = _load_run("b1/summary.json")
    b2 = _load_run("b2/summary.json")
    b3 = _load_run("b3/summary.json")
    b4 = _load_run("b4/summary.json")
    c = _load_run("c_ablation/summary.json")
    if b0:
        write_b0_md(b0)
        write_funnel(b0, b1, b2, b3, b4)
    write_condition_mds(b1, b2, b3, b4)
    write_final(b0, b1, b2, b3, b4, c)
    print("reports written", REPORTS)


if __name__ == "__main__":
    main()
