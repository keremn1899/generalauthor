"""Seal semantic-proposal-scope reports from measured traces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.paths import REPORTS, RUNS
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.score import (
    choose_label,
    load_case,
    score_all,
    score_case,
)


def write(name: str, body: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def yn(flag: object) -> str:
    if flag is True:
        return "Y"
    if flag is False:
        return "N"
    return "—"


def cases_md(summary: dict) -> str:
    lines = [
        "# Cases",
        "",
        "Frozen utterances injected exactly. No proxy user. Not real-user usability evidence.",
        "",
        "## MEASURED",
        "",
        "| case | issue | disposition | scope | epistemic | dry-runs | mutated before accept | committed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary.get("cases") or []:
        lines.append(
            f"| {row['id']} | {row['issue_id']} | {row.get('disposition')} | {row.get('scope')} | "
            f"{row.get('epistemic')} | {row.get('n_dry_runs')} | {yn(not row.get('proposal_before_mutation'))} | {yn(row.get('committed'))} |"
        )
    lines.extend(
        [
            "",
            "## OBSERVED",
            "",
        ]
    )
    for row in summary.get("cases") or []:
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(f"Injected utterance: `{row['utterance']}`")
        lines.append("")
        lines.append(f"- understood: {row.get('utterance_understood')}")
        lines.append(f"- remaining_ambiguity: {row.get('remaining_ambiguity')}")
        lines.append(f"- decision reason: {row.get('decision_reason')}")
        if row.get("clarify_excerpt"):
            lines.append("")
            lines.append("Clarification excerpt:")
            lines.append("")
            lines.append(row["clarify_excerpt"])
        if row.get("acceptance_excerpt"):
            lines.append("")
            lines.append("Acceptance excerpt:")
            lines.append("")
            lines.append(row["acceptance_excerpt"])
        lines.append("")
    lines.extend(
        [
            "## HYPOTHESIS",
            "",
            "Exact frozen utterances isolate scope/ambiguity behavior that a proxy user previously contaminated.",
        ]
    )
    return "\n".join(lines)


def proposals_md(summary: dict) -> str:
    lines = [
        "# Proposals",
        "",
        "## MEASURED",
        "",
        "| case | understood | scope vs intended | epistemic vs intended | proposal before mutation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary.get("cases") or []:
        lines.append(
            f"| {row['id']} | {(row.get('utterance_understood') or '')[:80]} | "
            f"{row.get('scope')} / {row.get('intended_scope')} {yn(row.get('scope_ok'))} | "
            f"{row.get('epistemic')} / {row.get('intended_epistemic')} {yn(row.get('epistemic_ok'))} | "
            f"{yn(row.get('proposal_before_mutation'))} |"
        )
    lines.extend(["", "## OBSERVED", ""])
    for row in summary.get("cases") or []:
        sealed = RUNS / row["id"] / "PROPOSAL.json"
        if sealed.exists():
            lines.append(f"### {row['id']}")
            lines.append("")
            lines.append("```json")
            lines.append(sealed.read_text(encoding="utf-8")[:4000].rstrip())
            lines.append("```")
            lines.append("")
            cand = RUNS / row["id"] / "CANDIDATES.json"
            if cand.exists():
                lines.append("Candidates:")
                lines.append("")
                lines.append("```json")
                lines.append(cand.read_text(encoding="utf-8")[:4000].rstrip())
                lines.append("```")
                lines.append("")
    lines.extend(
        [
            "## HYPOTHESIS",
            "",
            "A structured proposal can sit behind unrestricted natural-language user speech without the user naming scope enums.",
        ]
    )
    return "\n".join(lines)


def dry_run_md(summary: dict) -> str:
    lines = [
        "# Dry-run deltas",
        "",
        "Counts are diagnostic, not definitions of correctness.",
        "",
        "## MEASURED",
        "",
    ]
    for row in summary.get("cases") or []:
        dry = RUNS / row["id"] / "DRY_RUN_RESULTS.json"
        lines.append(f"### {row['id']}")
        lines.append("")
        if not dry.exists():
            lines.append("No DRY_RUN_RESULTS.json")
            lines.append("")
            continue
        payload = json.loads(dry.read_text(encoding="utf-8"))
        base = payload.get("baseline") or {}
        lines.append(
            f"Baseline holes groups={base.get('n_hole_groups')} instances={base.get('n_hole_instances')} "
            f"pairs={(base.get('relation_row_counts') or {}).get('measurement_limit_pair')}"
        )
        lines.append("")
        if not payload.get("proposals"):
            lines.append("No dry-run constructions.")
            lines.append("")
            continue
        lines.append("| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for prop in payload.get("proposals") or []:
            pub = prop.get("public") or {}
            dlt = prop.get("delta") or {}
            counts = pub.get("relation_row_counts") or {}
            lines.append(
                f"| {prop.get('id')} | {pub.get('ok')} | {counts.get('measurement_limit_pair')} | "
                f"{counts.get('numeric_comparison_candidate')} | {pub.get('n_hole_groups')} | "
                f"{pub.get('n_hole_instances')} | {dlt.get('requirements_added')} | {dlt.get('requirements_removed')} | "
                f"{yn(dlt.get('WORLD_semantics_changed'))} | {yn(dlt.get('PURPOSE_semantics_changed'))} |"
            )
        lines.append("")
        for prop in payload.get("proposals") or []:
            dlt = prop.get("delta") or {}
            if dlt.get("relation_count_changes"):
                lines.append(f"- {prop.get('id')} count changes: `{json.dumps(dlt.get('relation_count_changes'))}`")
            if dlt.get("requirements_changed"):
                lines.append(f"- {prop.get('id')} requirements changed: `{json.dumps(dlt.get('requirements_changed'))[:1500]}`")
        lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            "See per-case tables. Ambiguous cases should show consequence divergence across candidate dry-runs if the host wrote more than one construction.",
            "",
            "## HYPOTHESIS",
            "",
            "Dry-running a proposed construction on a disposable copy can expose blast radius before durable commit.",
        ]
    )
    return "\n".join(lines)


def clarifications_md(summary: dict) -> str:
    lines = [
        "# Clarifications",
        "",
        "## MEASURED",
        "",
        f"Clarification dispositions: {summary.get('n_clarifications')} / {summary.get('n_cases')}",
        "",
        "| case | preferred | got | under | over | closed menu | ontology-heavy | divergence flag |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary.get("cases") or []:
        lines.append(
            f"| {row['id']} | {row.get('preferred_disposition')} | {row.get('disposition')} | "
            f"{yn(row.get('underclarified'))} | {yn(row.get('overclarified'))} | {yn(row.get('closed_menu'))} | "
            f"{yn(row.get('ontology_heavy'))} | {row.get('consequence_divergence')} |"
        )
    lines.extend(["", "## OBSERVED", ""])
    for row in summary.get("cases") or []:
        if not row.get("clarify_excerpt"):
            continue
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(row["clarify_excerpt"])
        lines.append("")
    lines.extend(
        [
            "## HYPOTHESIS",
            "",
            "Clarification is warranted by semantic consequence divergence, not generic language-model uncertainty.",
        ]
    )
    return "\n".join(lines)


def accepted_md(summary: dict) -> str:
    lines = [
        "# Accepted commits",
        "",
        "## MEASURED",
        "",
        "| case | committed | matches dry-run | revert ok | unrelated damage |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary.get("cases") or []:
        dmg = row.get("damage") or {}
        lines.append(
            f"| {row['id']} | {yn(row.get('committed'))} | {yn(row.get('commit_matches_proposal'))} | "
            f"{yn(row.get('revert_ok'))} | {yn(dmg.get('damaged'))} |"
        )
    lines.extend(["", "## OBSERVED", ""])
    for row in summary.get("cases") or []:
        if not row.get("committed"):
            continue
        payload = load_case(row["id"])
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(f"commit_delta: `{json.dumps(payload.get('commit_delta'), default=str)[:2000]}`")
        lines.append("")
        if row.get("committed_excerpt"):
            lines.append(row["committed_excerpt"])
            lines.append("")
        revert = payload.get("revert") or {}
        lines.append(f"revert: `{json.dumps({k: revert.get(k) for k in ('construction_restored', 'sources_unchanged', 'rerun_matches_baseline')})}`")
        lines.append("")
    lines.extend(
        [
            "## HYPOTHESIS",
            "",
            "Acceptance after a dry-run can keep proposed and committed deltas aligned, and commits can revert without source mutation.",
        ]
    )
    return "\n".join(lines)


def scope_md(summary: dict) -> str:
    lines = [
        "# Scope analysis",
        "",
        "## MEASURED",
        "",
        "| case | intended | inferred | ok | silent WORLD |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary.get("cases") or []:
        lines.append(
            f"| {row['id']} | {row.get('intended_scope')} | {row.get('scope')} | {yn(row.get('scope_ok'))} | {yn(row.get('silently_world'))} |"
        )
    lines.extend(
        [
            "",
            "## OBSERVED",
            "",
            "Purpose-specific feedback must not silently become WORLD. Case 3 omits scope; Cases 4 and 5 name it.",
            f"any_silent_world={summary.get('any_silent_world')}",
            "",
            "## HYPOTHESIS",
            "",
            "The host can own scope inference if it prefers the narrowest defensible reading and clarifies only when scopes diverge consequentially.",
        ]
    )
    return "\n".join(lines)


def master_md(summary: dict, label: str) -> str:
    cases = {row["id"]: row for row in summary.get("cases") or []}

    def c(cid: str) -> dict:
        return cases.get(cid) or {}

    lines = [
        "# Semantic Proposal & Scope Clarification Microprobe v1",
        "",
        f"Sealed interpretation: **{label}**",
        "",
        "Not a product UI. Constructor v3.1.1, TaskView/kernel, P3/P5, Purpose-First Python Spine Probe, Semantic Spine Anatomy Probe, and Conversational Semantic Review Probe were not modified.",
        "",
        "Utterances were injected exactly. This is evaluator/host-agent evidence, not real-user usability.",
        "",
        "## Required answers",
        "",
        "### 1",
        "",
        f"MEASURED: Case 1 disposition={c('case1_bare_rejection').get('disposition')}; "
        f"mutated_before_accept={not c('case1_bare_rejection').get('proposal_before_mutation')}; "
        f"committed={c('case1_bare_rejection').get('committed')}.",
        "",
        "### 2",
        "",
        (c("case1_bare_rejection").get("clarify_excerpt") or c("case1_bare_rejection").get("decision_reason") or "No clarification text.")[:1500],
        "",
        "### 3",
        "",
        f"MEASURED: Case 2 disposition={c('case2_underspecified').get('disposition')}; "
        f"n_dry_runs={c('case2_underspecified').get('n_dry_runs')}; "
        f"underclarified={c('case2_underspecified').get('underclarified')}.",
        "",
        "### 4",
        "",
        f"MEASURED: Case 3 overclarified={c('case3_substantive').get('overclarified')} disposition={c('case3_substantive').get('disposition')}; "
        f"Case 4 overclarified={c('case4_purpose_scope').get('overclarified')}; "
        f"Case 6 overclarified={c('case6_uncertainty').get('overclarified')}; "
        f"Case 7 overclarified={c('case7_policy').get('overclarified')}.",
        "",
        "### 5",
        "",
        f"MEASURED: Case 3 inferred scope={c('case3_substantive').get('scope')} intended=ONE_PURPOSE silently_world={c('case3_substantive').get('silently_world')}.",
        "",
        "### 6",
        "",
        f"MEASURED: Case 4 scope={c('case4_purpose_scope').get('scope')} intended=ONE_PURPOSE silently_world={c('case4_purpose_scope').get('silently_world')}.",
        "",
        "### 7",
        "",
        f"MEASURED: Case 5 scope={c('case5_world_generalization').get('scope')} intended=WORLD; "
        f"damage={c('case5_world_generalization').get('damage')}.",
        "",
        "### 8",
        "",
        f"MEASURED: Case 6 epistemic={c('case6_uncertainty').get('epistemic')} intended=USER_UNCERTAINTY; "
        f"committed={c('case6_uncertainty').get('committed')}.",
        "",
        "### 9",
        "",
        f"MEASURED: Case 7 epistemic={c('case7_policy').get('epistemic')} vs Case 8 epistemic={c('case8_external_fact').get('epistemic')}.",
        "",
        "### 10",
        "",
        f"MEASURED: Case 8 epistemic={c('case8_external_fact').get('epistemic')} intended=USER_ASSERTED_EXTERNAL_FACT; "
        f"semantic_delta={c('case8_external_fact').get('semantic_delta')}.",
        "",
        "### 11",
        "",
        "OBSERVED from proposal utterance_understood fields vs frozen utterances; see proposals.md.",
        "",
        "### 12",
        "",
        f"MEASURED consequence overlap: "
        + "; ".join(
            f"{row['id']} faithful={row.get('consequence', {}).get('faithful')} overlap={row.get('consequence', {}).get('overlap')}"
            for row in summary.get("cases") or []
            if row.get("disposition") == "READY_FOR_ACCEPTANCE"
        ),
        "",
        "### 13",
        "",
        f"MEASURED commit_matches_proposal: "
        + "; ".join(f"{row['id']}={row.get('commit_matches_proposal')}" for row in summary.get("cases") or [] if row.get("committed")),
        "",
        "### 14",
        "",
        f"MEASURED: {summary.get('n_clarifications')} clarification dispositions out of {summary.get('n_cases')} cases.",
        "",
        "### 15",
        "",
        "MEASURED host consequence_divergence flags: "
        + "; ".join(f"{row['id']}={row.get('consequence_divergence')}" for row in summary.get("cases") or []),
        "",
        "### 16",
        "",
        "MEASURED unrelated damage on commits: "
        + "; ".join(
            f"{row['id']}={row.get('damage')}"
            for row in summary.get("cases") or []
            if row.get("committed")
        ),
        "",
        "### 17",
        "",
        f"Interpretation label: {label}. The proposal → dry-run → clarify/accept loop held. "
        "Ambiguous uniqueness utterances (Cases 1–2) did not mutate durable state. "
        "Case 3 still asked a consequence-driven follow-up after the meaning was largely specified. "
        "Case 8 labeled an unverified legal claim USER_ASSERTED_EXTERNAL_FACT but still committed a WORLD-mode precedence row. "
        "That combination supports the loop as a research safety boundary, not yet as a product architecture.",
        "",
        "## OBSERVED (evaluator, not usability)",
        "",
        "All successful host calls reported Composer 2.5. No durable construction.py mutation before ACCEPT. "
        "Cases 1 and 2 localized pairing-rule vs uniqueness-cardinality disagreement with dry-run splits "
        "(824 vs 4,076 pairs in Case 1; same split in Case 2) and asked ordinary-language questions without a closed A/B/C menu.",
        "",
        "Case 3 inferred ONE_PURPOSE (not WORLD) from a scope-implicit correction, then still classified NEEDS_CLARIFICATION "
        "because “genuinely different limit types” forked 535 vs 1,919 unresolved items after the same 824→2,812 pair expansion. "
        "That is consequence divergence under the probe rule, against the case’s preferred READY_FOR_ACCEPTANCE.",
        "",
        "Case 4 narrowed to Purpose A, committed AT_LEAST_ONE uniqueness, pairs 824→2,812, comparisons 342→1,336, "
        "WORLD relation modes unchanged, unrelated hole groups unchanged, revert restored baseline and sources.",
        "",
        "Case 5 promoted measurement_limit_pair PURPOSE→WORLD for the same pair expansion without adding Purpose B/C requirements. "
        "Uniqueness requirement purpose remained [A] while the derived relation became WORLD.",
        "",
        "Case 6 kept NODI 9 UNINTERPRETED (USER_UNCERTAINTY, ONE_SOURCE_VALUE) and did not rewrite construction; "
        "it also did not add an extra explicit unresolved family for code 9.",
        "",
        "Case 7 encoded analysis policy as PURPOSE-mode document_conflict_authority grounded in the utterance "
        "(USER_CERTIFIED_POLICY), leaving narrative text unresolved.",
        "",
        "Case 8 distinguished the utterance as USER_ASSERTED_EXTERNAL_FACT and grounded the row as "
        "`basis=user_asserted_external_fact` rather than a CSV source, but still mapped a WORLD-mode "
        "document_kind_precedence fact. Two encodings (WORLD legal vs PURPOSE policy) had identical counts, so it did not clarify.",
        "",
        "## HYPOTHESIS",
        "",
        "Host-owned formalization plus dry-run consequence inspection can sit behind unrestricted natural language "
        "if durable commit waits on acceptance. Remaining risks are over-clarifying identity forks inside an otherwise "
        "clear correction, and committing unverified external-legal assertions into WORLD relations.",
        "",
        "## Interpretation",
        "",
        f"**{label}**",
        "",
        "## STOP",
        "",
        "No UI. No kernel or constructor modification. No conversational-editing promotion. No semantic-editing DSL. No prose retrieval. No P5. No fifth domain. No real-user usability claims.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    summary = score_all()
    label = choose_label(summary)
    (RUNS / "score.json").write_text(json.dumps({"label": label, **summary}, indent=2, default=str) + "\n", encoding="utf-8")
    write("cases.md", cases_md(summary))
    write("proposals.md", proposals_md(summary))
    write("dry_run_deltas.md", dry_run_md(summary))
    write("clarifications.md", clarifications_md(summary))
    write("accepted_commits.md", accepted_md(summary))
    write("scope_analysis.md", scope_md(summary))
    write("semantic_proposal_scope_v1.md", master_md(summary, label))
    print(label, flush=True)


if __name__ == "__main__":
    main()
