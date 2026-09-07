"""Seal obligation-targeted resolution reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import (
    EVALUATOR_ONLY,
    FROZEN,
    REPORTS,
    RUNS,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.score import (
    choose_label,
    establishability,
    score,
    selected,
)


def write(name: str, body: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def jdump(obj) -> str:
    return json.dumps(obj, indent=2, default=str)


def selected_md() -> str:
    payload = json.loads((FROZEN / "selected_obligations.json").read_text(encoding="utf-8"))
    lines = [
        "# Selected obligations",
        "",
        "## MEASURED",
        "",
        payload.get("selection_rule", ""),
        "",
        "| id | question | n | purpose | why included |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec in payload.get("obligations") or []:
        lines.append(
            f"| {spec['obligation_id']} | {spec['exact_semantic_question']} | {spec['n_occurrences']} | "
            f"{spec['declared_purposes']} | {spec['include_reason']} |"
        )
    lines.extend(["", "## OBSERVED", "", "Selection frozen before host resolution. Varied evidence shapes, not only establishable cases.", "", "## HYPOTHESIS", "", "A small reusable obligation set can cover hundreds of T5 hole instances without sending raw rows to the resolver."])
    return "\n".join(lines)


def factorization_md(summary: dict) -> str:
    cands = json.loads((FROZEN / "candidate_obligations.json").read_text(encoding="utf-8"))
    lines = [
        "# Factorization",
        "",
        "## MEASURED",
        "",
        f"T5 hole instances (baseline): see frozen/baseline.json. Candidate obligations after value-level grouping: {len(cands)}. Selected: {summary.get('n_selected_obligations')}. Refinements written by host: {summary.get('n_refinements')}.",
        "",
        "| candidate | n |",
        "| --- | --- |",
    ]
    for c in cands:
        lines.append(f"| {c.get('candidate_id')} | {c.get('n_occurrences')} |")
    lines.extend(["", "## OBSERVED", "", "Hole-group count is 8; candidate obligations after splitting NODI codes and frequency values are 23, matching anatomy's T5 candidate count.", "", "## HYPOTHESIS", "", "Compile occurrences into reusable questions before retrieval."])
    return "\n".join(lines)


def arm_a_md(summary: dict) -> str:
    lines = [
        "# Occurrence-first baseline (Arm A)",
        "",
        "Naive comparison condition. ~20 sampled occurrences. Not a statistical benchmark.",
        "",
        "## MEASURED",
        "",
        f"n={summary.get('n_arm_a_cases')} dispositions={summary.get('arm_a_dispositions')} mean documents touched={summary.get('arm_a_mean_documents')}",
        "",
        "| case | obligation | occurrence | disposition | docs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in summary.get("arm_a") or []:
        j = c.get("judgment") or {}
        r = c.get("retrieval") or {}
        lines.append(
            f"| {c.get('case_id')} | {c.get('obligation_id')} | {c.get('occurrence_id')} | {j.get('disposition')} | {r.get('n_documents_touched')} |"
        )
    if summary.get("arm_a_inconsistent_obligations"):
        lines.extend(["", "Inconsistent interpretations across sibling samples:", "", jdump(summary["arm_a_inconsistent_obligations"])])
    lines.extend(["", "## OBSERVED", "", "See table. Duplicate retrieval is expected when each row is judged independently.", "", "## HYPOTHESIS", "", "Occurrence-first repeats codebook/permit lookups for the same meaning."])
    return "\n".join(lines)


def plans_md(summary: dict) -> str:
    lines = ["# Evidence plans", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append("```json")
        lines.append(jdump(c.get("plan") or {})[:4000])
        lines.append("```")
        lines.append("")
    lines.extend(["## OBSERVED", "", "Plans are host-authored before/during retrieval. Compare whether NODI plans reject CSV correlation.", "", "## HYPOTHESIS", "", "An evidence plan can constrain retrieval to obligation-relevant sources."])
    return "\n".join(lines)


def retrieval_md(summary: dict) -> str:
    lines = [
        "# Retrieval trace",
        "",
        "## MEASURED",
        "",
        f"Arm B mean documents touched={summary.get('mean_documents_opened_b')} mean retained snippets={summary.get('mean_retained_snippets_b')}",
        "",
        "| trial | obligation | docs touched | queries | retained | budget exception |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in summary.get("cells") or []:
        r = c.get("retrieval") or {}
        n_ret = len((c.get("packet") or {}).get("retained_snippets") or [])
        sealed = RUNS / "arm_b" / str(c.get("trial")) / str(c.get("obligation_id")) / "BUDGET_EXCEPTION.md"
        lines.append(
            f"| {c.get('trial')} | {c.get('obligation_id')} | {r.get('n_documents_touched')} | {r.get('n_queries')} | {n_ret} | {sealed.exists()} |"
        )
    lines.extend(["", "## OBSERVED", "", "Soft budget is 5 documents / 8 snippets. Broad nomination would show most of the 12 document files opened per obligation.", "", "## HYPOTHESIS", "", "Obligation-first retrieval stays local to the question."])
    return "\n".join(lines)


def packets_md(summary: dict) -> str:
    lines = ["# Evidence packets", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        pkt = c.get("packet") or {}
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append(f"candidates: {pkt.get('candidate_interpretations')}")
        lines.append(f"n_retained: {len(pkt.get('retained_snippets') or [])}")
        lines.append(f"limitations: {pkt.get('known_limitations')}")
        lines.append("")
        for snip in (pkt.get("retained_snippets") or [])[:8]:
            text = str((snip or {}).get("text") or "")[:400]
            lines.append(f"- `{ (snip or {}).get('source_id') }` {(snip or {}).get('location')}: {text}")
        lines.append("")
    lines.extend(["## OBSERVED", "", "Packets freeze what the adjudicator may use.", "", "## HYPOTHESIS", "", "Bounded packets prevent later search from laundering extra corpus into a judgment."])
    return "\n".join(lines)


def adjudication_md(summary: dict) -> str:
    est = establishability()
    lines = [
        "# Adjudication results",
        "",
        "## MEASURED",
        "",
        f"dispositions={summary.get('dispositions')} unsupported_closures={summary.get('unsupported_closures')}",
        "",
        "| trial | obligation | disposition | epistemic | scope | admit | establishability |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in summary.get("cells") or []:
        j = c.get("judgment") or {}
        p = c.get("proposal") or {}
        oid = c.get("obligation_id")
        lab = (est.get(oid) or {}).get("label")
        lines.append(
            f"| {c.get('trial')} | {oid} | {j.get('disposition')} | {j.get('epistemic_basis')} | {j.get('scope')} | {p.get('admit')} | {lab} |"
        )
    lines.extend(["", "## OBSERVED", "", "UNSUPPORTED_CLOSURE is any ADMIT_DISPOSABLE without a supported disposition and adequate epistemic basis.", "", "## HYPOTHESIS", "", "When the corpus cannot establish a code legend, UNRESOLVED is the correct durable state."])
    return "\n".join(lines)


def refinements_md(summary: dict) -> str:
    lines = ["# Obligation refinements", "", "## MEASURED", "", f"n_refinements={summary.get('n_refinements')}", ""]
    for c in summary.get("cells") or []:
        ref = c.get("refinement")
        if not ref:
            continue
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append("```json")
        lines.append(jdump(ref)[:4000])
        lines.append("```")
        lines.append("")
    lines.extend(["## OBSERVED", "", "Preferred: JUSTIFIED_FACTORIZATION into a small reusable set. Flag OVERFRAGMENTATION if dozens of children appear.", "", "## HYPOTHESIS", "", "Evidence contact should split only when consequences differ (e.g. comment families already split evaluator-side)."])
    return "\n".join(lines)


def proposals_md(summary: dict) -> str:
    lines = ["# Semantic proposals", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        p = c.get("proposal") or {}
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append(f"- admit: {p.get('admit')}")
        lines.append(f"- scope: {p.get('scope')} epistemic: {p.get('epistemic_basis')}")
        lines.append(f"- delta: {p.get('semantic_delta')}")
        lines.append(f"- grounding: {p.get('exact_grounding')}")
        lines.append("")
    lines.extend(["## OBSERVED", "", "Scope may be WORLD while admit is UNVERIFIED_PROPOSAL.", "", "## HYPOTHESIS", "", "Proposal-before-mutation plus epistemic admission keeps unverified legal claims out of World truth."])
    return "\n".join(lines)


def propagation_md(summary: dict) -> str:
    lines = ["# Propagation results", "", "## MEASURED", ""]
    for c in summary.get("cells") or []:
        dry = c.get("dry_run")
        if not dry:
            continue
        dlt = dry.get("delta") or {}
        lines.append(f"### {c.get('trial')} {c.get('obligation_id')}")
        lines.append("")
        lines.append(f"count changes: `{json.dumps(dlt.get('relation_count_changes'))}`")
        lines.append(f"holes groups {dlt.get('n_hole_groups')} instances {dlt.get('n_hole_instances')}")
        lines.append(f"requirements added/removed: {dlt.get('requirements_added')} / {dlt.get('requirements_removed')}")
        lines.append("")
    lines.extend(["## OBSERVED", "", "Intended: one reusable mapping changes all matching occurrences. Leakage: NODI 9 must not close NODI C; WHEN DISCHARGING must not close geometric-mean comments.", "", "## HYPOTHESIS", "", "Deterministic application beats per-row model judgments."])
    return "\n".join(lines)


def compression_md(summary: dict) -> str:
    lines = [
        "# Compression metrics",
        "",
        "## MEASURED",
        "",
        f"- selected occurrences: {summary.get('n_affected_occurrences_selected')}",
        f"- selected obligations: {summary.get('n_selected_obligations')}",
        f"- occurrences / obligation: {summary.get('compression')}",
        f"- Arm B judgments (cells): {summary.get('n_arm_b_cells')}",
        f"- occurrences / Arm B judgment: {summary.get('occurrences_per_arm_b_judgment')}",
        f"- Arm A cases: {summary.get('n_arm_a_cases')}",
        f"- Arm A mean documents: {summary.get('arm_a_mean_documents')}",
        f"- Arm B mean documents: {summary.get('mean_documents_opened_b')}",
        f"- mean retained snippets: {summary.get('mean_retained_snippets_b')}",
        "",
        "## OBSERVED",
        "",
        "Leverage is occurrences whose state can change per semantic judgment, not token cost.",
        "",
        "## HYPOTHESIS",
        "",
        "Compile meaning once, compute consequences many times.",
    ]
    return "\n".join(lines)


def failure_md(summary: dict) -> str:
    est = establishability()
    lines = [
        "# Failure analysis",
        "",
        "## MEASURED establishability (hidden from host)",
        "",
        "| obligation | evaluator label | note |",
        "| --- | --- | --- |",
    ]
    for oid, row in est.items():
        lines.append(f"| {oid} | {row.get('label')} | {row.get('note')} |")
    lines.extend(
        [
            "",
            "## OBSERVED",
            "",
            f"- unsupported_closures={summary.get('unsupported_closures')} (target 0)",
            f"- protocol_mismatches={summary.get('protocol_mismatches')}",
            f"- failed_dry_runs={summary.get('failed_dry_runs')}",
            f"- mutated_before_evidence={summary.get('mutated_before_evidence')}",
            f"- leakage_flags={json.dumps(summary.get('leakage_flags') or {})}",
            f"- unresolved_by_mode={json.dumps(summary.get('unresolved_by_mode') or {})}",
            f"- extra_corpus Arm B={summary.get('extra_corpus_snippet_ids_arm_b')} Arm A={summary.get('extra_corpus_snippet_ids_arm_a')}",
            "",
            "NODI C stayed UNRESOLVED on all three Arm B trials with failure_mode EVIDENCE_INSUFFICIENT, matching NOT_ESTABLISHABLE_IN_CORPUS.",
            "NODI 9 stayed unadmitted; T3 returned SUPPORTED_NEGATIVE without ADMIT_DISPOSABLE (the code legend is still absent).",
            "empty_numeric_limit was refined into comment-family children and left UNRESOLVED at parent grain — OBLIGATION_TOO_BROAD / EVIDENCE_INSUFFICIENT, not a retrieval miss of a single codebook.",
            "T2 pass_fail dry-run crashed (`KeyError: 'limit_unit_desc'`). That is a disposable-apply failure, not a sibling-leakage event.",
            "T2 geometric_mean admitted a TDS-scoped proposal while the parent disposition remained UNRESOLVED (protocol mismatch, grounded footnote evidence).",
            "document_authority exceeded the 5-document soft budget (T1 wrote BUDGET_EXCEPTION.md) because the obligation spans three facilities.",
            "",
            "An aborted first Arm A wave cited an extra-corpus EPA NODI legend. Those cases were deleted before sealing. See frozen/aborted_arm_a_wave.md.",
            "",
            "## HYPOTHESIS",
            "",
            "Establishability audit distinguishes retrieval quality from epistemic insufficiency. That distinction held for NODI codes.",
        ]
    )
    return "\n".join(lines)


def master_md(summary: dict, label: str) -> str:
    specs = selected()
    n_occ = summary.get("n_affected_occurrences_selected")
    per = "\n".join(f"- {s['obligation_id']}: {s['n_occurrences']}" for s in specs)
    n_est = len(summary.get("establishable_ids") or [])
    n_got = summary.get("establishable_resolved_at_least_once") or 0
    lines = [
        "# Obligation-Driven Targeted Semantic Resolution Probe v1",
        "",
        f"Sealed interpretation: **{label}**",
        "",
        "Draft spine: sealed Purpose-First Python Spine Probe **T5**.",
        "Model: **Composer 2.5** on every successful host call (Arm A ×20, Arm B retrieve+adjudicate ×24×2).",
        "GOLD and `evaluator_only/establishability.json` were not copied into host workspaces.",
        "This is evaluator/host-agent evidence, not real-user usability. Not constructor promotion.",
        "",
        "## What was tested",
        "",
        "```text",
        "semantic obligation → evidence plan → targeted retrieval → bounded packet",
        "→ bounded judgment → semantic proposal → disposable dry-run → admit or UNRESOLVED",
        "```",
        "",
        "Desired shape: many blocked occurrences → few reusable obligations → few investigations → few judgments → many deterministic consequences.",
        "",
        "## Required answers",
        "",
        "### 1. How many raw hole occurrences are covered by the selected obligations?",
        "",
        f"MEASURED: **{n_occ}** affected occurrences across 8 selected obligations (families counted separately; a row may appear in more than one family).",
        "",
        per,
        "",
        f"T5 baseline hole instances were 535 across 8 hole groups. Selected coverage is {n_occ} after splitting NODI by code and adding empty LIMIT_VALUE_NMBR rows that T5 never named as a hole.",
        "",
        "### 2. How many reusable obligations remain after evidence-contact refinement?",
        "",
        f"MEASURED: initial selected = **{summary.get('n_selected_obligations')}**. Host wrote refinements on **{summary.get('n_refinements')}** of 24 Arm B cells.",
        "Typical children: geometric_mean → TDS vs non-TDS comment carryover (2); empty_numeric_limit → 4 comment-family partitions; monitoring_frequency → calendar vs continuous vs retest; nodi_9 → WET-optional vs TRC. Final reusable grain is on the order of **12–16** questions, not thousands of rows.",
        "",
        "### 3. Does the factorization remain compact, or does it explode?",
        "",
        f"MEASURED: 23 candidate obligations after value-level grouping; 8 selected; refinements added a handful of children per parent. Not occurrence-level explosion. Not compact enough for the strict success label (refinement cells={summary.get('n_refinements')}, threshold was ≤8).",
        "OBSERVED: children follow mechanically computable structured partitions (PARAMETER_CODE, DMR_COMMENT_TEXT, LIMIT_FREQ_OF_ANALYSIS_CODE), not unique source wording per row.",
        "",
        "### 4. How many selected obligations are establishable from the frozen corpus?",
        "",
        f"MEASURED evaluator labels: ESTABLISHABLE = {summary.get('establishable_ids')} (**{n_est}**).",
        "NOT_ESTABLISHABLE: nodi_c, nodi_9, monitoring_frequency (no codebook in permit packages).",
        "UNCERTAIN: empty_numeric_limit, document_authority.",
        "",
        "### 5. Of establishable obligations, how many are successfully retrieved and resolved?",
        "",
        f"MEASURED: **{n_got} / {n_est}** had at least one Arm B trial with SUPPORTED_RESOLUTION or SUPPORTED_NEGATIVE.",
        "when_discharging: 3/3 SUPPORTED_RESOLUTION with Aztec permit footnote *1 and statement-of-basis 'when discharging'.",
        "pass_fail: 3/3 SUPPORTED_RESOLUTION with Farmington Part II 0/1 WET coding plus structured PASS=0 FAIL=1 comments.",
        "geometric_mean: T1 UNRESOLVED (too broad / residual comparison statistic); T3 SUPPORTED_RESOLUTION after TDS vs non-TDS split; T2 parent UNRESOLVED but admitted a TDS-scoped proposal.",
        "Establishing permit passages were retrieved into the frozen packets (not missed).",
        "",
        "### 6. How many obligations correctly remain unresolved because the corpus is insufficient?",
        "",
        "OBSERVED: nodi_c 3/3 UNRESOLVED + unadmitted, failure_mode EVIDENCE_INSUFFICIENT.",
        "nodi_9 unadmitted on all trials; T1/T2 UNRESOLVED, T3 SUPPORTED_NEGATIVE without durable admit (still no NODI legend).",
        "monitoring_frequency: T1 UNVERIFIED_PROPOSAL, T2 UNRESOLVED, T3 SUPPORTED_NEGATIVE unadmitted — no workspace codebook mapping 05/WK as a field legend, though occurrence-local permit tables can gloss some codes (see Arm A).",
        "empty_numeric_limit parent remained UNRESOLVED after justified splits.",
        "",
        "### 7. Are retrieval failure and evidence insufficiency distinguishable in practice?",
        "",
        "YES for NODI. Evaluator pre-labeled NOT_ESTABLISHABLE; host failure_mode was EVIDENCE_INSUFFICIENT, not RETRIEVAL_FAILURE. Packets cite GCC permit/fact-sheet absence of a NODI legend rather than inventing EPA ICIS text.",
        f"unresolved_by_mode={json.dumps(summary.get('unresolved_by_mode') or {})}",
        "An earlier unsealed Arm A wave *did* cite extra-corpus EPA NODI legends; the sealed protocol forbade that. Distinction requires both the hidden establishability audit and workspace-only grounding.",
        "",
        "### 8. How much evidence is inspected per obligation?",
        "",
        f"MEASURED Arm B mean documents_touched={summary.get('mean_documents_opened_b'):.2f} mean retained snippets={summary.get('mean_retained_snippets_b'):.2f} (cap 8).",
        "pass_fail typically 2–3 documents; when_discharging 4–5; geometric_mean 3–4; document_authority 11–13 (over budget).",
        "",
        "### 9. Does obligation-first retrieval avoid broad corpus attention?",
        "",
        "MOSTLY. Plans named codebook vs permit-clause vs filename-metadata insufficiency before retrieval. Hosts did not run 'find all useful semantic passages'.",
        "Exception: document_authority opened most of the 12 permit-text files to test cross-facility self-description; T1 recorded BUDGET_EXCEPTION.md. That is still bounded to inventoried permit packages, not the hidden GOLD corpus.",
        "Instrumentation counts path touches under documents/; directory reads inflate n_documents_touched relative to unique .txt files.",
        "",
        "### 10. Does one semantic judgment propagate to many occurrences?",
        "",
        "YES for supported comment-family obligations.",
        "T1 when_discharging: 535 → 518 hole instances (−17, matching the 17 WHEN DISCHARGING rows) and added `discharge_occurrence_in_period` (semantic sharpening).",
        "T2/T3 when_discharging: 535 → 501 (−34); they removed `conditional_discharge_dependent_monitoring` and added a monitoring-condition relation without always emitting the factual discharge hole as cleanly as T1.",
        "T1 pass_fail: 535 → 525 (−10-class) after replacing the pass/fail unresolved family with binary reporting relations.",
        "T3 geometric_mean: numeric_comparison_candidate 342 → 318 (−24 non-TDS carryover rows) and removed `aggregated_reporting_requirement`.",
        "",
        "### 11. What is the measured occurrences-per-semantic-judgment ratio?",
        "",
        f"MEASURED across all 24 Arm B cells: {n_occ} / {summary.get('n_arm_b_cells')} = **{summary.get('occurrences_per_arm_b_judgment')}**.",
        "That denominator counts unresolved cells too. Per supported reusable decision the leverage is higher: 17 WHEN DISCHARGING rows per when_discharging judgment; 12 pass/fail rows; 40 geometric-mean comment rows collapsing to a 16/24 TDS vs carryover split.",
        "",
        "### 12. Does deterministic propagation affect exactly the intended occurrences?",
        "",
        "T1 when_discharging delta matches the 17-row family and does not remove geometric-mean or pass/fail hole requirements.",
        "T3 geometric_mean removed only `aggregated_reporting_requirement` (not WHEN DISCHARGING / pass-fail).",
        "T2 pass_fail dry-run **failed** and is not a valid propagation observation.",
        f"leakage_flags after ignoring failed dry-runs: {json.dumps(summary.get('leakage_flags') or {})}",
        "",
        "### 13. Are sibling values/comments protected from semantic leakage?",
        "",
        "NODI C was never admitted; NODI 9 was never admitted as a positive code legend. No trial wrote known=['C','9'].",
        "geometric_mean refinements explicitly refuse to apply footnote *6 to BOD/pH/TSS rows that inherited the TDS comment — Arm A occurrence-first reached the same BOD-negative on A10/A11.",
        "when_discharging dry-runs did not drop pass_fail or aggregated_reporting hole requirements.",
        "document_authority replaced filename-only unresolved with role/precedence unresolved rather than ranking every kind from names alone.",
        "",
        "### 14. Does resolving semantic meaning sometimes generate sharper factual obligations?",
        "",
        "YES. T1 when_discharging is the spec's acceptable example: comment semantics resolved; `discharge_occurrence_in_period` added; remaining uncertainty is whether discharge occurred in FY2025 periods (structured NODI blank / numeric values present, not independently proving discharge).",
        "",
        "### 15. Does obligation refinement improve semantic grain, or merely split source wording?",
        "",
        "JUSTIFIED_FACTORIZATION for geometric_mean (TDS vs misattached comment), empty_numeric_limit (report-only / WET / WHEN DISCHARGING / geometric-mean empty cells), nodi_9 (optional WET retest vs TRC), monitoring_frequency (calendar vs 99/99 continuous vs 09/99 retest).",
        "Not SURFACE_TEXT_SPLIT_ONLY: partitions are mechanically computable from structured fields and change the computational consequence.",
        "Not OVERFRAGMENTATION to unique rows.",
        "",
        "### 16. Does occurrence-first reasoning repeat the same retrieval/judgment work?",
        "",
        f"MEASURED Arm A n={summary.get('n_arm_a_cases')} mean documents_touched={summary.get('arm_a_mean_documents')}.",
        "Three WHEN DISCHARGING samples each reopened Aztec final_permit + statement_of_basis. Three NODI C samples each searched GCC documents for a missing legend. Four monitoring_frequency samples each joined a local permit table.",
        "Arm B asked the reusable question once per trial. Duplicate work is real even though mean documents/call is similar (Arm B mean is pulled up by document_authority).",
        "",
        "### 17. Is obligation-first reasoning more semantically consistent than occurrence-first?",
        "",
        f"Arm A inconsistent interpretation sets (string-level): {list((summary.get('arm_a_inconsistent_obligations') or {}).keys())}.",
        "NODI 9 mixed UNRESOLVED (A04/A05) vs SUPPORTED_NEGATIVE on the WET retest row (A06) — occurrence-local optional-retest facts, not a code legend.",
        "Arm B NODI C was stable UNRESOLVED. when_discharging and pass_fail were stable SUPPORTED_RESOLUTION.",
        "geometric_mean and monitoring_frequency dispositions varied by trial (UNRESOLVED vs supported/negative) while the *consequential* split (TDS vs carryover; calendar vs special codes) recurred. Naming differences were ignored per spec.",
        "",
        "### 18. Are there any unsupported durable closures?",
        "",
        f"MEASURED unsupported_closures={summary.get('unsupported_closures')} (target 0).",
        "NODI C/9 were not admitted as World code legends. Sealed packets do not retain extra-corpus EPA dictionaries.",
        f"protocol_mismatches={summary.get('protocol_mismatches')} (T2 geometric_mean: parent UNRESOLVED, TDS-scoped ADMIT_DISPOSABLE with footnote grounding).",
        f"failed_dry_runs={summary.get('failed_dry_runs')}.",
        "mutated_before_evidence=0: retrieve stage did not rewrite durable construction.py.",
        "",
        "### 19. Do semantic proposals preserve exact source grounding?",
        "",
        "Supported packets retain quoted permit footnotes and CSV locations (Aztec *1, Farmington *6/*9 / Part II 0/1 WET). Adjudicator workspaces had PACKET.json only — no documents/ tree.",
        "",
        "### 20. Does scope remain distinct from epistemic admission?",
        "",
        "YES in the artifact schema. Proposals carry separate `scope` and `epistemic_basis` and `admit`.",
        "T1 monitoring_frequency used admit=UNVERIFIED_PROPOSAL while remaining UNRESOLVED — a WORLD-ish frequency guess was not treated as World truth.",
        "",
        "### 21. Can a WORLD-scoped but unverified proposition remain unadmitted as World truth?",
        "",
        "YES. T2 geometric_mean interpretation discussed WORLD-scope uncertainty while the admitted delta was ONE_SOURCE_VALUE (PARAMETER_CODE=70295). T1 monitoring_frequency stayed UNVERIFIED_PROPOSAL. empty_numeric_limit proposals were not admitted.",
        "",
        "### 22. How many model semantic judgments relative to affected source occurrences?",
        "",
        f"Arm B: 24 adjudicator judgments (plus 24 retrieve calls) covering {n_occ} selected occurrences, vs Arm A: 20 judgments covering 20 sampled rows.",
        "If occurrence-first were run on all 150 NODI-C rows it would take 150 judgments for one missing legend; obligation-first used 3 retrieve+3 adjudicate and correctly refused closure.",
        "",
        "### 23. Does the experiment support compile-meaning-once → compute-consequences-many-times at residual resolution?",
        "",
        "PARTIALLY. Supported for WHEN DISCHARGING and pass/fail: one grounded permit reading, disposable construction change, many hole instances moved.",
        "Supported negatively for NODI: compiling the reusable question prevented 150+36 invented legends.",
        "Weaker where dry-run quality is uneven (T2 pass_fail crash) or parent/child admit protocol drifts (T2 geometric_mean).",
        f"Interpretation: **{label}** — not a clean promotion of obligation-factoring into the kernel.",
        "",
        "### 24. Does the experiment support purpose-derived obligation → selective evidence → bounded judgment → grounded reusable semantic state as an alternative to broad prose attention?",
        "",
        "YES as a *research mechanism*, with caveats.",
        "Evidence plans constrained attention; packets were bounded (≤8 snippets); adjudicator could not search the corpus; establishable permit clauses were found without nominating the whole library; unsupported NODI closure was avoided.",
        "Caveats: document_authority still opened most permit files; refinements multiplied questions (justifiably); disposable apply is not yet a reliable mechanical compiler (one crash); Arm A can locally join a permit table and 'resolve' a frequency code that the reusable codebook obligation correctly leaves unresolved.",
        "",
        "## Bad outcomes checked",
        "",
        "- 8 obligations → hundreds of bespoke obligations: **not observed**.",
        "- One code meaning → model re-judges every row: **not observed in Arm B** (Arm A is that baseline, capped at 20).",
        "- Resolver reads most of the corpus every question: **only document_authority** approached that, with a recorded budget exception.",
        "- Structural correlation as durable NODI truth: **not admitted** in sealed Arm B.",
        "- Comment-family leakage: **not observed** on successful dry-runs.",
        "- Unresolved evidence treated as negative durable World: NODI 9 T3 SUPPORTED_NEGATIVE was **not admitted**.",
        "- Retrieval failure mislabeled as insufficiency: NODI insufficiency matches the hidden audit.",
        "",
        "## Interpretation",
        "",
        f"**{label}**",
        "",
        "Factorization stayed compact at reusable grain. Targeted retrieval found establishing permit text when it existed (WHEN DISCHARGING, pass/fail, TDS geometric-mean footnotes). Unsupported NODI durable closure was 0. Propagation of supported comment semantics moved many hole instances. Obligation-first avoided repeating NODI/permit lookups per row.",
        "The strict success label is withheld because refinements were frequent, document_authority overran the document budget, one disposable apply crashed, and one trial admitted a refined geometric-mean proposal while leaving the parent UNRESOLVED.",
        "",
        "## STOP",
        "",
        "No constructor/kernel change. No P1–P4 collapse. No semantic-family taxonomy. No broad prose nomination. No product promotion. No UI. No real-user study. No fifth domain. No spine rewrite from scratch.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    summary = score()
    label = choose_label(summary)
    (RUNS / "score.json").write_text(json.dumps({"label": label, **{k: v for k, v in summary.items() if k not in {"cells", "arm_a"}}}, indent=2, default=str) + "\n", encoding="utf-8")
    write("selected_obligations.md", selected_md())
    write("factorization.md", factorization_md(summary))
    write("occurrence_first_baseline.md", arm_a_md(summary))
    write("evidence_plans.md", plans_md(summary))
    write("retrieval_trace.md", retrieval_md(summary))
    write("evidence_packets.md", packets_md(summary))
    write("adjudication_results.md", adjudication_md(summary))
    write("obligation_refinements.md", refinements_md(summary))
    write("semantic_proposals.md", proposals_md(summary))
    write("propagation_results.md", propagation_md(summary))
    write("compression_metrics.md", compression_md(summary))
    write("failure_analysis.md", failure_md(summary))
    write("obligation_targeted_resolution_v1.md", master_md(summary, label))
    print(label, flush=True)


if __name__ == "__main__":
    main()
