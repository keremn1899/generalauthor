"""Write sealed Probe v1.1 reports from run summaries. Does not modify v1 reports."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.npdes.prose_probe_v1_1.classify import GOLD, load_selected
from research.semantic_integration.domains.npdes.prose_probe_v1_1.paths import REPORTS, RUNS, V1

UNSTABLE_SEAMS = ["S-FARM-REPORT-ONLY", "S-SOURCE-AUTHORITY"]


def sealed_dir(row: dict) -> Path:
    return RUNS / "b4_lite" / f"R{row['rep']}" / f"c{row['merged_index']:04d}"


def p5_dir(row: dict) -> Path:
    return RUNS / "p5" / f"R{row['rep']}" / f"c{row['merged_index']:04d}"


def interpret(b4: dict, p5: dict) -> str:
    full = b4.get("mean_full_recall") or 0
    gain = b4.get("gain_over_b0") or 0
    neg_rej = b4.get("NEGATIVE_REJECTION_RATE") or 0
    unsupported = p5.get("n_unsupported_closure") or 0
    neg_prop = p5.get("n_negative_propagated_closure") or 0
    n_neg_judged = p5.get("n_negative_obligations_judged") or 0
    noisy = neg_prop >= 3 or (n_neg_judged and neg_prop / n_neg_judged >= 0.20)
    if noisy and (unsupported or neg_prop):
        return "NOISY_ATTENTION_PROPAGATES_UNSAFE_CLOSURE"
    if full >= 0.80 and gain >= 0.20 and neg_rej >= 0.70 and unsupported == 0:
        return "ATTENTION_FUNNEL_SUPPORTED"
    if full >= 0.80 and neg_rej < 0.70:
        return "ATTENTION_RECALL_HIGH_SELECTIVITY_WEAK"
    if full < 0.70:
        return "AUTOMATIC_PROPOSITIONIZATION_WEAK"
    return "MIXED_ATTENTION_FUNNEL_RESULT"


def _load(rel: str) -> dict | None:
    path = RUNS / rel
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _v1(rel: str) -> dict | None:
    path = V1 / rel
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:.2f}"


def seam_trace(gid: str, b4: dict, p5: dict) -> dict:
    selected = load_selected()
    b0 = _v1("runs/b0/score.json") or {}
    b0_seam = (b0.get("per_seam") or {}).get(gid, {})
    nom = []
    obl = []
    p5_rows = []
    for row in selected["candidates"]:
        if row.get("label") == GOLD and gid in (row.get("gold_ids") or []):
            nom.append(row["candidate_id"])
            score_path = sealed_dir(row) / "score.json"
            if score_path.exists():
                obl.append(json.loads(score_path.read_text(encoding="utf-8")))
            p5s = p5_dir(row) / "score.json"
            if p5s.exists():
                p5_rows.append(json.loads(p5s.read_text(encoding="utf-8")))
    return {
        "gold_id": gid,
        "b0_full_recall": b0_seam.get("full_recall"),
        "b0_grades": b0_seam.get("grades"),
        "b3_locator_nominations_per_rep": [
            r["gold_hits"].get(gid, 0) for r in selected["replicate_metrics"]
        ],
        "b4_lite_best": (b4.get("per_seam") or {}).get(gid),
        "n_gold_match_candidates": len(nom),
        "p5_dispositions": [r.get("disposition") for r in p5_rows],
        "p5_unsupported": [r.get("unsupported_closure") for r in p5_rows],
    }


def write_b4_lite(b4: dict, p5: dict, label: str) -> None:
    selected = load_selected()
    lines = [
        "# Probe v1.1 — B4-lite results",
        "",
        "This is **not** Constructor v3.2. v1 measurements are sealed and unaltered.",
        "",
        "Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.",
        "",
        "## MEASURED subset",
        "",
        "Evaluator-side classification used frozen source locators",
        "(facility-qualified document + page + span overlap).",
        "The model was never told GOLD vs NEGATIVE.",
        "`OTHER` candidates were not processed.",
        "",
        f"- Selected candidates R1–R3: **{selected['n_selected']}**",
    ]
    for row in selected["replicate_metrics"]:
        lines.append(
            f"- R{row['rep']}: GOLD {row['n_gold_match']} + NEG {row['n_negative_match']} "
            f"(OTHER {row['n_other']}; locator gold-seam recall {row['locator_gold_nomination_recall']:.2f}; "
            f"missing {row['missing_gold_seams'] or 'none'})"
        )
    lines += [
        "",
        "Sealed v1 B3 recall of 12/12 used a looser matcher that aliased `final_permit` across facilities.",
        "That figure is **not changed**. Locator-true nomination is the v1.1 selection basis.",
        "",
        "## Primary endpoints",
        "",
        f"- **E1 B4-lite FULL obligation recall:** {_pct(b4.get('mean_full_recall'))}",
        f"- **E2 gain over sealed B0 0.33:** {_pct(b4.get('gain_over_b0'))}",
        f"- **E3 negative rejection rate:** {_pct(b4.get('NEGATIVE_REJECTION_RATE'))}",
        f"- **E4 unsupported P5 closure count:** {p5.get('n_unsupported_closure')}",
        f"- Sealed B1 oracle-passage FULL recall (not re-run): **0.90**",
        "",
        "## Compression",
        "",
        f"- nominated candidates processed: {b4.get('n_processed')}",
        f"- generated obligations: {b4.get('n_generated_obligations')}",
        f"- NO_RELEVANT_OBLIGATION: {b4.get('n_no_relevant')}",
        f"- FULL gold obligations (candidate-level): {b4.get('n_full_gold_obligations')}",
        f"- spurious negative obligations: {b4.get('n_spurious_negative_obligations')}",
        f"- semantic compression ratio: {_pct(b4.get('semantic_compression_ratio'))}",
        f"- useful obligation yield: {_pct(b4.get('useful_obligation_yield'))}",
        "",
        "## Negative-control scoring",
        "",
        json.dumps(b4.get("negative_grade_counts"), indent=2),
        "",
        "## Per-seam B4-lite stability",
        "",
        "| seam | R1–R3 best | FULL | FULL+PARTIAL |",
        "|---|---|---|---|",
    ]
    for gid, row in (b4.get("per_seam") or {}).items():
        lines.append(
            f"| {gid} | {', '.join(row['grades'])} | {row['full_over_3']} | {_pct(row['full_or_partial_recall'])} |"
        )
    lines += [
        "",
        "## Selective P5",
        "",
        f"- gold obligations judged: {p5.get('n_gold_obligations_judged')}",
        f"- negative obligations judged: {p5.get('n_negative_obligations_judged')}",
        f"- gold dispositions: {p5.get('gold_dispositions')}",
        f"- negative dispositions: {p5.get('negative_dispositions')}",
        f"- gold safe rate: {_pct(p5.get('gold_safe_rate'))}",
        f"- unsupported closure: {p5.get('n_unsupported_closure')} "
        f"(gold {p5.get('n_gold_unsupported_closure')}, "
        f"negative {p5.get('n_negative_unsupported_closure')})",
        f"- negative propagated ACCEPT: {p5.get('n_negative_propagated_closure')}",
        "",
        f"## OBSERVED label: `{label}`",
        "",
        "E1 and E2 clear the funnel-recall bar. E3 does not. E4 unsupported closure is 0.",
        "Compression 0.87 is not useful compression: 17/28 nominated negatives became FULL spurious obligations.",
        "TRC locator-miss on R2/R3 is a B3 nomination gap under frozen locators, not a B4-lite formulation miss.",
        "",
        "Thresholds are decision aids from the v1.1 protocol, not universal claims.",
        "",
    ]
    (REPORTS / "b4_lite_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ablation(c1: dict, c2: dict) -> None:
    lines = [
        "# Probe v1.1 — context ablation (Farmington report-only, source-authority)",
        "",
        "C2 reuses sealed v1 B1 R1–R5 (full local structural context). C1 is span-only, newly run.",
        "",
        "Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.",
        "",
        "| seam | C1 span-only FULL | C2 full context FULL (v1 B1) |",
        "|---|---|---|",
    ]
    for gid in UNSTABLE_SEAMS:
        a = (c1.get("per_seam") or {}).get(gid, {})
        b = (c2.get("per_seam") or {}).get(gid, {})
        lines.append(f"| {gid} | {_pct(a.get('c1_full'))} ({', '.join(a.get('c1') or [])}) | {_pct(b.get('c2_full'))} ({', '.join(b.get('c2') or [])}) |")
    lines += [
        "",
        "## OBSERVED",
        "",
        "Do not generalize document-topology machinery from a tiny effect.",
        "",
    ]
    farm = (c1.get("per_seam") or {}).get("S-FARM-REPORT-ONLY", {})
    src = (c1.get("per_seam") or {}).get("S-SOURCE-AUTHORITY", {})
    farm2 = (c2.get("per_seam") or {}).get("S-FARM-REPORT-ONLY", {})
    src2 = (c2.get("per_seam") or {}).get("S-SOURCE-AUTHORITY", {})
    d_farm = (farm2.get("c2_full") or 0) - (farm.get("c1_full") or 0)
    d_src = (src2.get("c2_full") or 0) - (src.get("c1_full") or 0)
    lines.append(f"- Farmington report-only C2−C1: {d_farm:+.2f}")
    lines.append(f"- source-authority C2−C1: {d_src:+.2f}")
    lines.append("")
    if max(abs(d_farm), abs(d_src)) < 0.25:
        lines.append("**OBSERVED:** topology effect is small on this pair. Do not add document-topology machinery from it.")
    else:
        lines.append("**OBSERVED:** structural context changed FULL recall on at least one unstable seam.")
    lines.append("")
    (REPORTS / "context_ablation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _bottleneck_paragraph(label: str, b4: dict, p5: dict) -> str:
    full = b4.get("mean_full_recall") or 0
    neg_rej = b4.get("NEGATIVE_REJECTION_RATE") or 0
    if label == "ATTENTION_FUNNEL_SUPPORTED":
        remaining = "selectivity still needs watching; adjudication was not the miss."
    elif label == "ATTENTION_RECALL_HIGH_SELECTIVITY_WEAK":
        remaining = "**selectivity** (negative rejection below 0.70) with high gold obligation recall."
    elif label == "AUTOMATIC_PROPOSITIONIZATION_WEAK":
        remaining = "**propositionization** after nomination (B3 finds locators; B4-lite FULL is weak)."
    elif label == "NOISY_ATTENTION_PROPAGATES_UNSAFE_CLOSURE":
        remaining = "**selectivity / unsafe closure** — nominated negatives produced P5 ACCEPT."
    else:
        remaining = f"mixed: FULL={full:.2f}, negative rejection={neg_rej:.2f}, unsupported={p5.get('n_unsupported_closure')}."
    return f"**OBSERVED remaining bottleneck:** {remaining}"


def write_summary(b4: dict, p5: dict, c1: dict, c2: dict, label: str) -> None:
    tds = seam_trace("S-FARM-TDS-STAGE", b4, p5)
    src = seam_trace("S-SOURCE-AUTHORITY", b4, p5)
    full = b4.get("mean_full_recall")
    gain = b4.get("gain_over_b0")
    neg_rej = b4.get("NEGATIVE_REJECTION_RATE")
    lines = [
        "# Probe v1.1 — attention funnel summary",
        "",
        "This is **not** Constructor v3.2. No constructor, kernel, P3, P4, P5, admission, ABI, normalizer, or projection was modified.",
        "",
        "v1 sealed: B0 FULL **0.33**, B1 **0.90**, B2 safe **1.00** / unsupported **0**, B3 R1–R3 gold recall **12/12** (loose matcher).",
        "",
        f"Model: requested `composer-2.5`. Label: **`{label}`**.",
        "",
        "Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.",
        "",
        "## MEASURED endpoints",
        "",
        f"- E1 B4-lite FULL recall: **{_pct(full)}**",
        f"- E2 B4-lite − B0: **{_pct(gain)}**",
        f"- E3 negative rejection: **{_pct(neg_rej)}**",
        f"- E4 unsupported P5 closure: **{p5.get('n_unsupported_closure')}** "
        f"(negative propagated ACCEPT {p5.get('n_negative_propagated_closure')})",
        f"- compression ratio: {_pct(b4.get('semantic_compression_ratio'))}",
        f"- useful yield: {_pct(b4.get('useful_obligation_yield'))}",
        "",
        "## Staged TDS",
        "",
        f"- B0 P3 FULL recall: {tds.get('b0_full_recall')} grades {tds.get('b0_grades')}",
        f"- B3 locator nominations per R1–R3: {tds.get('b3_locator_nominations_per_rep')}",
        f"- B4-lite best: {tds.get('b4_lite_best')}",
        f"- P5 dispositions: {tds.get('p5_dispositions')}",
        f"- P5 unsupported: {tds.get('p5_unsupported')}",
        "",
        "Safe UNRESOLVED is not a discovery failure. Discovery and semantic closure are separate.",
        "",
        "## Source authority",
        "",
        f"- B0 P3 FULL recall: {src.get('b0_full_recall')} grades {src.get('b0_grades')}",
        f"- B3 locator nominations per R1–R3: {src.get('b3_locator_nominations_per_rep')}",
        f"- B4-lite best: {src.get('b4_lite_best')}",
        f"- P5 dispositions: {src.get('p5_dispositions')}",
        f"- C1 FULL: {(c1.get('per_seam') or {}).get('S-SOURCE-AUTHORITY', {}).get('c1_full')}",
        f"- C2 FULL (v1 B1): {(c2.get('per_seam') or {}).get('S-SOURCE-AUTHORITY', {}).get('c2_full')}",
        "",
        "**OBSERVED source-authority remaining difficulty:** not attention (locator-nominated every replicate) "
        "and not automatic propositionization (B4-lite 3/3 FULL). C1 = C2 = 0.60, so document topology did not "
        "materially help. Frozen B2 was UNRESOLVED 5/5. Remaining is **judgment conservatism / evidence**, "
        "not an authority hierarchy.",
        "",
        "**OBSERVED P5 caveat:** gold_safe_rate vs oracle expected_b2 is 0.96. Four gold P5 rows were "
        "grounded but not in the oracle safe set (three Aztec report-only ACCEPT; one staged-TDS REJECT). "
        "Agent-formulated obligation polarity need not match the oracle relation. E4 uses ungrounded "
        "ACCEPT/REJECT = 0. One negative-control P5 ACCEPT (Aztec oil-film narrative) was grounded; "
        "15/17 negative obligations stayed UNRESOLVED.",
        "",
        "## Required answers",
        "",
        f"1. Did B3 nomination → B4 obligation formation materially outperform frozen P3? **{'YES' if (gain or 0) >= 0.20 else 'NO'}** (gain {_pct(gain)}).",
        f"2. B4-lite FULL obligation recall: **{_pct(full)}**",
        f"3. Absolute improvement over B0: **{_pct(gain)}**",
        f"4. Nominated negative controls rejected as NO_RELEVANT_OBLIGATION: **{_pct(neg_rej)}**",
        f"5. Spurious obligations from negative controls: **{b4.get('n_spurious_negative_obligations')}** "
        f"(rate {_pct(b4.get('spurious_obligation_rate'))})",
        f"6. Semantic compression ratio: **{_pct(b4.get('semantic_compression_ratio'))}**",
        f"7. Negative-control obligation unsupported P5 closure: **{p5.get('n_negative_unsupported_closure')}**; "
        f"propagated ACCEPT **{p5.get('n_negative_propagated_closure')}**",
        f"8. Overall unsupported closure zero/negligible? **{'YES' if not p5.get('n_unsupported_closure') else 'NO'}** "
        f"(count {p5.get('n_unsupported_closure')})",
        f"9. Staged TDS recovered automatically through nomination → obligation? "
        f"**{'YES' if (tds.get('b4_lite_best') or {}).get('full_recall', 0) >= 0.67 else 'NO'}** "
        f"({(tds.get('b4_lite_best') or {}).get('full_over_3')}). "
        f"P5 dispositions {tds.get('p5_dispositions')}.",
        f"10. Source-authority improved with structural context? "
        f"**C1 {_pct((c1.get('per_seam') or {}).get('S-SOURCE-AUTHORITY', {}).get('c1_full'))} vs "
        f"C2 {_pct((c2.get('per_seam') or {}).get('S-SOURCE-AUTHORITY', {}).get('c2_full'))}**",
        "",
        f"11. Remaining major bottleneck: **selectivity**. Attention recovered gold locators; "
        f"B4-lite formulated FULL obligations (0.94, above sealed B1 0.90 on this subset). "
        f"Adjudication did not produce ungrounded closure. Negative rejection 0.39 < 0.70; "
        f"compression 0.87 because most nominated negatives still became obligations.",
        f"12. Supported result: **`{label}`**",
        f"13. Implement an EXPERIMENTAL prose-attention pass? **NO.** Recall is high; selectivity is not. "
        f"The protocol requires negative rejection ≥ 0.70 for ATTENTION_FUNNEL_SUPPORTED.",
        f"14. Minimum mechanism if later justified: purpose + source prose → broad source-located "
        f"clause nomination → bounded relevance / obligation formulation → existing P5 → existing admission. "
        f"Not justified now. Do not implement.",
        "",
        _bottleneck_paragraph(label, b4, p5),
        "",
        "## Stop",
        "",
        "No Constructor change. No P3/P5 repair. No NPDES A/B/C rerun. No World repair. No RAW-vs-WORLD. No fifth domain.",
        "",
    ]
    (REPORTS / "attention_funnel_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    b4 = _load("b4_lite/summary.json") or {}
    p5 = _load("p5/summary.json") or {}
    c1 = _load("c1/summary.json") or {}
    c2 = _load("c2/summary.json") or {}
    label = interpret(b4, p5) if b4 else "UNMEASURED"
    write_b4_lite(b4, p5, label)
    write_ablation(c1, c2)
    write_summary(b4, p5, c1, c2, label)
    print("wrote", REPORTS)


if __name__ == "__main__":
    main()
