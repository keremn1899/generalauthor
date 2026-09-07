"""Seal conversational-review reports from measured traces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.paths import REPORTS, RUNS
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.score import (
    mp1_scores,
    mp2_compare,
    mp3_score,
)


def load(name: str):
    path = RUNS / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, body: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def yn(flag: bool) -> str:
    return "Y" if flag else "N"


def decision_record_probe(mp1) -> str:
    lines = [
        "# Decision-record → conversation (Microprobe 1)",
        "",
        "Proxy-host explanations of sealed T5 draft obligations. Not human usability evidence.",
        "",
        "## MEASURED",
        "",
    ]
    for i, trial in enumerate(mp1 or [], start=1):
        scores = mp1_scores(RUNS / "mp1" / f"T{i}")
        flags = scores["flags"]
        lines.append(f"### T{i}")
        lines.append("")
        lines.append(f"- records written: {scores['n_records']}; conversation files: {scores['n_explanations']}")
        lines.append(f"- reported_model: {(trial.get('agent') or {}).get('reported_model')}")
        lines.append("")
        lines.append("| flag | hit |")
        lines.append("| --- | --- |")
        for k, v in flags.items():
            lines.append(f"| {k} | {yn(v)} |")
        lines.append("")
        if scores["ontology_term_hits"]:
            lines.append("Ontology-term hits in explanations: " + json.dumps(scores["ontology_term_hits"]))
            lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            "T1 NODI conversation is representative: ordinary language, counts C=150 and 9=36, refuses to assign no-discharge vs not-required, asks the expert to correct. Decision records cite ISSUES.md and construction.py, not GOLD.",
            "Hosts sometimes still ask the expert to interpret codes the draft already left unresolved — that is the intended review question, not asking them to re-decide a mechanical join count.",
            "",
            "## HYPOTHESIS",
            "",
            "A forensic decision record can be translated into ordinary language without exposing GOLD, if the host is given factorized obligations rather than raw hole rows.",
        ]
    )
    return "\n".join(lines)


def near_miss_probe(mp2) -> str:
    cmp_ = mp2_compare(mp2 or [])
    lines = [
        "# Open question vs near-miss (Microprobe 2)",
        "",
        "Proxy-expert packets are evaluator-authored stances, not NPDES law and not GOLD.",
        "",
        "## MEASURED distinction recovery",
        "",
        "| issue | OPEN recovered | NEAR recovered | Δ | NEAR boxed into A/B/C |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in cmp_["issues"]:
        lines.append(
            f"| {row['issue_id']} | {row['open_recovered']}/{row['open']['n_distinctions']} | "
            f"{row['near_recovered']}/{row['near']['n_distinctions']} | {row['near_minus_open']:+d} | {yn(row['near_boxed'])} |"
        )
    lines.extend(
        [
            "",
            "## Per-issue missed distinctions",
            "",
        ]
    )
    for row in cmp_["issues"]:
        lines.append(f"### {row['issue_id']}")
        lines.append("")
        lines.append("OPEN missed: " + "; ".join(row["open"]["missed"] or ["none"]))
        lines.append("")
        lines.append("NEAR missed: " + "; ".join(row["near"]["missed"] or ["none"]))
        lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            "NEAR NODI proposed a closed mapping (C = no discharge, 9 = not required) from structural correlation. The hidden packet forbids that inference. The proxy refused the mapping while keeping C ≠ 9. That is the intended near-miss behavior: a wrong-or-partial interpretation that can be pushed off.",
            "OPEN NODI also elicited C ≠ 9 and legend-required uncertainty, with less to reject.",
            "WHEN DISCHARGING NEAR proposed discharge-conditional applicability and listed alternatives; the proxy accepted the discharge-occurrence reading and rejected seasonal/aggregation conflation without choosing A/B/C.",
            "The frozen exact-utterance ambiguity test belongs to MP3, not MP2.",
            "",
            "## HYPOTHESIS",
            "",
            "NEAR-MISS transfers more of the consequential distinction when the host states a wrong-or-partial interpretation the expert can push off, without boxing the expert into listed alternatives.",
        ]
    )
    return "\n".join(lines)


def revision_probe(mp3) -> str:
    lines = [
        "# Conversational revision (Microprobe 3)",
        "",
        "Research copies of sealed T5 `construction.py`. Deterministic reruns via the frozen Python-spine runner.",
        "",
        "## MEASURED",
        "",
    ]
    for trial in mp3 or []:
        scored = mp3_score(trial)
        lines.append(f"### {scored['trial']}")
        lines.append("")
        lines.append("| step | kind | host epistemic | intended epistemic | host scope | turns | changed | rerun ok | generalization |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for step in scored["steps"]:
            lines.append(
                f"| {step['id']} | {step['kind']} | {step['host_epistemic']} | {step['intended_epistemic']} | "
                f"{step['host_scope']} | {step['n_turns']} | {step['construction_changed']} | {step['rerun_ok']} | {step['generalization']} |"
            )
        lines.append("")
        base = trial.get("baseline") or {}
        lines.append(f"Baseline rerun ok={base.get('ok')} groups={base.get('n_hole_groups')} instances={base.get('n_hole_instances')}")
        lines.append("")
    lines.extend(
        [
            "## OBSERVED",
            "",
            "All six MP3 deterministic reruns ok=true (Composer 2.5).",
            "H1 NODI: groups 8→10; codes remain UNINTERPRETED; extra unresolved for 9 and C. Uncertainty preserved.",
            "H2: groups stayed 8; three comment families remained separate.",
            "H3 document: policy that final permit would outrank fact sheet *if text existed* was recorded without ranking from filenames.",
            "H3_bare_no: the proxy did **not** emit the frozen sentence 'No, that's wrong.' It produced a long uniqueness correction. The host compiled that reply (removed uniqueness; pairs 824→2768) and did not write CLARIFY.md. The ambiguity-localization stress test is therefore proxy-contaminated and inconclusive.",
            "See semantic_deltas.md for hole-group and requirement-name diffs. Epistemic labels are the host's INTERPRETATION.json, compared to frozen intended kinds.",
            "",
            "## HYPOTHESIS",
            "",
            "Unrestricted natural-language feedback can compile into scoped construction edits if the host keeps policy, uncertainty, and source-grounded state distinct.",
        ]
    )
    return "\n".join(lines)


def traces(mp1, mp2, mp3) -> str:
    lines = ["# Interaction traces", "", "Truncated. Full files live under `runs/`.", ""]
    for i in range(1, 4):
        conv = RUNS / "mp1" / f"T{i}" / "conversation"
        lines.append(f"## MP1 T{i}")
        lines.append("")
        if conv.exists():
            for path in sorted(conv.glob("*.md")):
                text = path.read_text(encoding="utf-8")
                lines.append(f"### {path.name}")
                lines.append("")
                lines.append(text[:2500])
                lines.append("")
        else:
            lines.append("(no conversation/ directory)")
            lines.append("")
    for cell in mp2 or []:
        lines.append(f"## MP2 {cell.get('issue_id')} {cell.get('condition')}")
        lines.append("")
        lines.append("HOST:")
        lines.append("")
        lines.append((cell.get("host_message") or "")[:2000])
        lines.append("")
        lines.append("PROXY:")
        lines.append("")
        lines.append((cell.get("proxy_reply") or "")[:2000])
        lines.append("")
    for trial in mp3 or []:
        lines.append(f"## MP3 {trial.get('trial')}")
        lines.append("")
        for step in trial.get("steps") or []:
            lines.append(f"### {step.get('id')}")
            lines.append("")
            lines.append("HOST:")
            lines.append((step.get("host_message") or "")[:1500])
            lines.append("")
            lines.append("USER:")
            lines.append((step.get("user_utterance") or "")[:1500])
            lines.append("")
            lines.append("INTERPRETATION: " + json.dumps(step.get("host_interpretation") or {}, default=str)[:1500])
            lines.append("")
    return "\n".join(lines)


def deltas(mp3) -> str:
    lines = ["# Semantic deltas", "", "MEASURED hole-group and requirement-name changes after each MP3 edit.", ""]
    for trial in mp3 or []:
        base = trial.get("baseline") or {}
        prev_groups = set(str(g.get("requirement")) for g in (base.get("hole_groups") or []))
        prev_names = set(base.get("requirement_names") or [])
        lines.append(f"## {trial.get('trial')}")
        lines.append("")
        lines.append(f"baseline groups={base.get('n_hole_groups')} instances={base.get('n_hole_instances')}")
        lines.append("")
        for step in trial.get("steps") or []:
            rerun = step.get("rerun") or {}
            groups = set(str(g.get("requirement")) for g in (rerun.get("hole_groups") or []))
            names = set(rerun.get("requirement_names") or [])
            lines.append(f"### {step.get('id')}")
            lines.append("")
            lines.append(f"ok={rerun.get('ok')} groups={rerun.get('n_hole_groups')} instances={rerun.get('n_hole_instances')}")
            lines.append(f"requirement names added: {sorted(names - prev_names)[:20]}")
            lines.append(f"requirement names removed: {sorted(prev_names - names)[:20]}")
            lines.append(f"hole-group requirements added: {sorted(groups - prev_groups)}")
            lines.append(f"hole-group requirements removed: {sorted(prev_groups - groups)}")
            lines.append("")
            prev_groups, prev_names = groups, names
    return "\n".join(lines)


def choose_label(mp1, mp2, mp3) -> str:
    if not mp1 or not mp2 or not mp3:
        return "PROXY_INTERACTION_INCONCLUSIVE"
    # Evaluator override after reading traces: MP1 faithful; MP2 NEAR transferred
    # corrections including rejection of a wrong NODI mapping; MP3 compiled
    # policy/uncertainty/comment splits with all reruns ok — but the frozen
    # "No, that's wrong." stress test was not executed as designed (proxy
    # expanded it) and that step produced a large uniqueness rewrite.
    return "MIXED_CONVERSATIONAL_SEMANTIC_RESULT"


def master(mp1, mp2, mp3) -> str:
    label = choose_label(mp1, mp2, mp3)
    cmp_ = mp2_compare(mp2 or [])
    answers = {
        "1": (
            "MEASURED: 3/3 MP1 trials wrote four decision records and four conversation files; "
            "reported_model Composer 2.5. OBSERVED: explanations used ordinary DMR/permit language "
            "(e.g. T1 NODI: 186 cases, C vs 9, refuses to guess no-discharge vs not-required)."
        ),
        "2": (
            "Purpose, current draft reading, a few structured counts/snippets (C=150, 9=36, "
            "WHEN DISCHARGING 17, 12 inventoried documents), why the distinction changes the "
            "analysis, remaining uncertainty, and an invitation to correct. Not raw Python and not 2,972 hole rows."
        ),
        "3": (
            "NEAR vs OPEN recovered-distinction Δ (token heuristic): "
            + ", ".join(f"{r['issue_id']} {r['near_minus_open']:+d}" for r in cmp_["issues"])
            + ". OBSERVED: NEAR NODI additionally let the proxy *reject a specific wrong mapping* "
            "(C=no-discharge, 9=not-required) that OPEN never proposed. That is extra semantic information."
        ),
        "4": (
            "NEAR boxed-into-A/B/C heuristic: "
            + ", ".join(f"{r['issue_id']}={r['near_boxed']}" for r in cmp_["issues"])
            + ". OBSERVED: proxies did not pick listed alternatives. NEAR NODI proposed a wrong closed reading; "
            "the proxy refused it. Anchoring risk is real and was resisted in this proxy, not proven as capture."
        ),
        "5": (
            "Yes in proxy traces: uniqueness NEAR proxy introduced seasonal-as-qualifier rather than a second "
            "simultaneous limit; NODI proxies kept C vs 9 distinct and refused glyph-inference. Those were in the hidden packet, not a host menu."
        ),
        "6": (
            "H1 acceptance → USER_CERTIFIED_POLICY; H1 NODI → USER_UNCERTAINTY; H2 comment split → MODEL_CORRECTION; "
            "H3 document → USER_CERTIFIED_POLICY. H2 qualification was also labeled MODEL_CORRECTION (intended USER_CERTIFIED_POLICY). "
            "Four kinds were mostly distinguished; qualification vs correction is the weak boundary."
        ),
        "7": (
            "Yes when the utterance was specific: H1 NODI added two explicit unresolved families (groups 8→10) without closing codes; "
            "H3 document sharpened unresolved reasons; H2 kept three comment families separate. "
            "H3 uniqueness rewrite (pairs 824→2768, uniqueness requirement removed) compiled the *received* reply, which was not the frozen bare-no utterance."
        ),
        "8": (
            "NODI → one_source_value (appropriate). Comments → one_relation (appropriate). Document policy → one_relation. "
            "Acceptance uniqueness → general_world (broader than intended purpose-A rule). "
            "H3 uniqueness rewrite → one_purpose."
        ),
        "9": "No INSTANCE_MEMORIZATION steps (did not hard-code a single DMR_VALUE_ID).",
        "10": (
            "H1 acceptance labeled general_world while leaving uniqueness in place (over-scoped label, small edit). "
            "H3 uniqueness expansion is a large reusable-rule change matching the reply it actually received."
        ),
        "11": (
            "Mostly: document ranking was recorded as analysis policy if text existed, not as a filename fact. "
            "NODI C 'usually documented no-data' was kept as policy context while holes stayed UNINTERPRETED. "
            "The host did not write new CSV rows as source truth."
        ),
        "12": (
            "Edits lived in purpose requirements, unresolved reasons, and pairing derivations. "
            "CONSEQUENCE.md files claim no invented source fields. Human provenance is narrative (policy notes / unresolved reasons), "
            "not a kernel ConstructionOrigin tag — this probe did not add kernel primitives."
        ),
        "13": (
            "Yes on H1 NODI: known=[''] retained; 186 UNINTERPRETED remain; extra unresolved items for 9 (legend) and C (period-specific). "
            "Did not convert I-don't-know into false or not-applicable."
        ),
        "14": (
            "CONSEQUENCE.md for H1 NODI and H3 uniqueness matched rerun deltas (groups 8→10; pairs 824→2768). "
            "H2 claimed annotation-only change; groups stayed 8."
        ),
        "15": (
            "MP1: one host turn per trial (four issues). MP2: one host message + one proxy reply. "
            "MP3: two host calls per intervention (explain then revise) and one proxy reply; no CLARIFY.md was written. "
            "The designed second turn for bare-no localization did not occur."
        ),
        "16": (
            "Proxy evidence supports conversation as a viable *review* interface for ordinary-language explanation, "
            "near-miss correction, uncertainty, and modest construction edits. It does not yet support promoting it to the "
            "primary production editing surface: the ambiguity stress test was proxy-contaminated, and one uniqueness "
            "rewrite was a large behavioral delta from a single rejection-shaped reply."
        ),
        "17": (
            "Still wants an ontology-engineer glance: uniqueness cardinality vs limit-kind matching, "
            "provenance tagging distinct from source grounding, and fixture-sensitive phrase detectors (WHEN DISCHARGING). "
            "A formal surface is not required for the four review questions themselves."
        ),
    }
    q = "\n\n".join(f"### {k}\n\n{v}" for k, v in answers.items())
    return "\n".join(
        [
            "# Conversational Semantic Review Microprobes v1",
            "",
            f"Sealed interpretation: **{label}**",
            "",
            "Not a product UI. Constructor v3.1.1, TaskView/kernel, P3/P5, Purpose-First Python Spine Probe, and Semantic Spine Anatomy Probe were not modified.",
            "",
            "All user/host language here is **proxy interaction evidence**, not real-user usability.",
            "",
            "## Required answers",
            "",
            q,
            "",
            "## Interpretation",
            "",
            f"**{label}**",
            "",
            "## STOP",
            "",
            "No UI. No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5. No fifth domain. No real-user usability claims.",
        ]
    )


def main() -> None:
    mp1 = load("mp1.json") or []
    mp2 = load("mp2.json") or []
    mp3 = load("mp3.json") or []
    write("decision_record_probe.md", decision_record_probe(mp1))
    write("near_miss_probe.md", near_miss_probe(mp2))
    write("conversational_revision_probe.md", revision_probe(mp3))
    write("interaction_traces.md", traces(mp1, mp2, mp3))
    write("semantic_deltas.md", deltas(mp3))
    write("conversational_semantic_review_v1.md", master(mp1, mp2, mp3))
    print("reports written", REPORTS)


if __name__ == "__main__":
    main()
