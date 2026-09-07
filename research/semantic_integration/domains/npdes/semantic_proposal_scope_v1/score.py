"""Qualitative scoring over sealed proposal-scope traces. Evaluator judgment, not human usability."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.cases import CASES, INTENTS
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.diffs import deltas_match
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.paths import RUNS

ONTOLOGY_TERMS = (
    "require_interpreted",
    "require_unique",
    "referent(",
    "world.relation",
    "cardinality",
    "n-ary",
    "purpose.require",
    "ONE_OCCURRENCE",
    "mode=\"WORLD\"",
)

CLOSED_MENU = (
    "choose one",
    "option a",
    "option b",
    "pick a/b",
    "(a)",
    "(b)",
    "(c)",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": path.read_text(encoding="utf-8")[:4000]}


def case_dir(case_id: str) -> Path:
    return RUNS / case_id


def load_case(case_id: str) -> dict:
    path = case_dir(case_id) / "case.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def user_facing(case_id: str) -> str:
    sealed = case_dir(case_id)
    return "\n".join(
        [
            _read(sealed / "CLARIFY.md"),
            _read(sealed / "ACCEPTANCE.md"),
            _read(sealed / "COMMITTED.md"),
        ]
    )


def ontology_heavy(text: str) -> bool:
    blob = text.lower()
    return sum(blob.count(t.lower()) for t in ONTOLOGY_TERMS) >= 4


def closed_menu(text: str) -> bool:
    blob = text.lower()
    return any(tok in blob for tok in CLOSED_MENU)


def numbers_in(text: str) -> set[int]:
    return {int(m) for m in re.findall(r"\b\d{2,5}\b", text)}


def dry_run_numbers(case_id: str) -> set[int]:
    results = _json(case_dir(case_id) / "DRY_RUN_RESULTS.json") or {}
    found: set[int] = set()
    baseline = (results.get("baseline") or {}).get("relation_row_counts") or {}
    for val in baseline.values():
        if isinstance(val, int):
            found.add(val)
    for prop in results.get("proposals") or []:
        counts = ((prop.get("public") or {}).get("relation_row_counts") or {})
        for val in counts.values():
            if isinstance(val, int):
                found.add(val)
        ng = (prop.get("public") or {}).get("n_hole_groups")
        ni = (prop.get("public") or {}).get("n_hole_instances")
        if isinstance(ng, int):
            found.add(ng)
        if isinstance(ni, int):
            found.add(ni)
    return found


def consequence_overlap(case_id: str) -> dict[str, Any]:
    facing = user_facing(case_id)
    mentioned = numbers_in(facing)
    dry = dry_run_numbers(case_id)
    material = {n for n in dry if n in {824, 342, 186, 105, 150, 36, 12, 8} or n >= 100}
    if not material:
        return {"applicable": False, "hit": 0, "material": [], "mentioned": sorted(mentioned)}
    hits = mentioned & material
    return {
        "applicable": True,
        "hit": len(hits),
        "material": sorted(material),
        "mentioned": sorted(mentioned),
        "overlap": sorted(hits),
        "faithful": bool(hits) or not material,
    }


def unrelated_damage(case: dict) -> dict[str, Any]:
    issue = case.get("issue_id")
    delta = case.get("commit_delta") or {}
    counts = delta.get("relation_count_changes") or {}
    added = delta.get("requirements_added") or []
    removed = delta.get("requirements_removed") or []
    changed = [c.get("name") for c in delta.get("requirements_changed") or []]
    if issue == "unique_applicable_limit":
        unexpected = [k for k in counts if k not in {"measurement_limit_pair", "numeric_comparison_candidate", "fy2025_measurement"}]
        unexpected_req = [n for n in added + removed + changed if n and "unique" not in n and "limit" not in n and "comparison" not in n]
    elif issue == "nodi_semantics":
        unexpected = [k for k in counts if k not in {"no_numeric_result_case"}]
        unexpected_req = [n for n in added + removed + changed if n and "nodi" not in n and "unresolved" not in n and "missing" not in n]
    else:
        unexpected = [k for k in counts if k not in {"permit_document"}]
        unexpected_req = [n for n in added + removed + changed if n and "document" not in n and "permit" not in n]
    return {"unexpected_relation_count_changes": unexpected, "unexpected_requirements": unexpected_req, "damaged": bool(unexpected or unexpected_req)}


def score_case(case_id: str) -> dict[str, Any]:
    spec = next(c for c in CASES if c["id"] == case_id)
    intent = INTENTS[case_id]
    row = load_case(case_id)
    sealed = case_dir(case_id)
    proposal = _json(sealed / "PROPOSAL.json") or row.get("proposal") or {}
    decision = _json(sealed / "DECISION.json") or row.get("decision") or {}
    disposition = decision.get("disposition") or row.get("disposition")
    facing = user_facing(case_id)
    clarify = (sealed / "CLARIFY.md").exists()
    scope = proposal.get("candidate_scope")
    epistemic = proposal.get("epistemic_basis")
    mutated_before_accept = bool(row.get("mutated_after_propose") or row.get("mutated_after_decide"))
    preferred = intent["preferred_disposition"]
    clarification_correct = (preferred == "NEEDS_CLARIFICATION" and disposition == "NEEDS_CLARIFICATION") or (
        preferred == "READY_FOR_ACCEPTANCE" and disposition == "READY_FOR_ACCEPTANCE"
    )
    overclarified = (
        preferred == "READY_FOR_ACCEPTANCE"
        and disposition == "NEEDS_CLARIFICATION"
        and not intent.get("allow_unnecessary_clarification")
        and not (
            decision.get("consequence_divergence") is True
            and (row.get("n_dry_runs") or 0) >= 2
        )
    )
    underclarified = preferred == "NEEDS_CLARIFICATION" and disposition == "READY_FOR_ACCEPTANCE"
    scope_ok = intent["intended_scope"] in {scope, "UNKNOWN"} or (
        intent["intended_scope"] == "UNKNOWN" and scope in {"UNKNOWN", None}
    )
    if intent["intended_scope"] == "ONE_PURPOSE":
        scope_ok = scope == "ONE_PURPOSE"
        silently_world = scope == "WORLD"
    else:
        silently_world = intent["intended_scope"] != "WORLD" and scope == "WORLD"
    epistemic_ok = epistemic == intent["epistemic"]
    commit_match = None
    if row.get("committed") and row.get("commit_delta"):
        chosen = decision.get("chosen_dry_run_id")
        dry = _json(sealed / "DRY_RUN_RESULTS.json") or {}
        proposed_delta = None
        for prop in dry.get("proposals") or []:
            if prop.get("id") == chosen or (chosen is None and proposed_delta is None):
                proposed_delta = prop.get("delta")
        if proposed_delta is None and (dry.get("proposals") or []):
            proposed_delta = dry["proposals"][0].get("delta")
        commit_match = deltas_match(proposed_delta or {}, row.get("commit_delta") or {}) if proposed_delta else False
    cons = consequence_overlap(case_id)
    damage = unrelated_damage(row) if row.get("commit_delta") else {"damaged": False, "unexpected_relation_count_changes": [], "unexpected_requirements": []}
    revert = row.get("revert") or {}
    return {
        "id": case_id,
        "n": spec["n"],
        "utterance": spec["utterance"],
        "issue_id": spec["issue_id"],
        "preferred_disposition": preferred,
        "disposition": disposition,
        "clarification_correct": clarification_correct,
        "overclarified": overclarified,
        "underclarified": underclarified,
        "clarify_written": clarify,
        "acceptance_written": (sealed / "ACCEPTANCE.md").exists(),
        "n_dry_runs": row.get("n_dry_runs"),
        "proposal_before_mutation": not mutated_before_accept,
        "mutated_after_propose": row.get("mutated_after_propose"),
        "mutated_after_decide": row.get("mutated_after_decide"),
        "scope": scope,
        "intended_scope": intent["intended_scope"],
        "scope_ok": scope_ok,
        "silently_world": silently_world,
        "epistemic": epistemic,
        "intended_epistemic": intent["epistemic"],
        "epistemic_ok": epistemic_ok,
        "committed": row.get("committed"),
        "commit_matches_proposal": commit_match,
        "revert_ok": revert.get("construction_restored") and revert.get("sources_unchanged") and revert.get("rerun_matches_baseline") if revert else None,
        "ontology_heavy": ontology_heavy(facing),
        "closed_menu": closed_menu(facing),
        "consequence": cons,
        "damage": damage,
        "ordinary_language_ok": bool(facing.strip()) and not ontology_heavy(facing) and not closed_menu(facing),
        "reported_models": {
            "propose": row.get("reported_model_propose"),
            "decide": row.get("reported_model_decide"),
            "commit": row.get("reported_model_commit"),
        },
        "remaining_ambiguity": proposal.get("remaining_ambiguity"),
        "semantic_delta": proposal.get("semantic_delta"),
        "utterance_understood": proposal.get("utterance_understood"),
        "decision_reason": decision.get("reason"),
        "consequence_divergence": decision.get("consequence_divergence"),
        "clarify_excerpt": _read(sealed / "CLARIFY.md")[:1200],
        "acceptance_excerpt": _read(sealed / "ACCEPTANCE.md")[:1200],
        "committed_excerpt": _read(sealed / "COMMITTED.md")[:1200],
    }


def score_all() -> dict[str, Any]:
    cases = [score_case(c["id"]) for c in CASES if (case_dir(c["id"]) / "case.json").exists()]
    n = len(cases)
    proposal_compliance = all(c["proposal_before_mutation"] for c in cases) if cases else False
    c1 = next((c for c in cases if c["id"] == "case1_bare_rejection"), None)
    c2 = next((c for c in cases if c["id"] == "case2_underspecified"), None)
    ambiguity_ok = bool(c1 and c2 and c1["disposition"] == "NEEDS_CLARIFICATION" and c2["disposition"] == "NEEDS_CLARIFICATION")
    precise_ids = ("case3_substantive", "case4_purpose_scope", "case6_uncertainty", "case7_policy")
    precise = [c for c in cases if c["id"] in precise_ids]
    non_overclarification = all(not c["overclarified"] for c in precise) if precise else False
    scope_fail = any(c.get("silently_world") for c in cases)
    commit_rows = [c for c in cases if c.get("committed")]
    commit_mismatch = any(c.get("commit_matches_proposal") is False for c in commit_rows)
    consequence_weak = any(c["consequence"].get("applicable") and not c["consequence"].get("faithful") for c in cases if c["disposition"] == "READY_FOR_ACCEPTANCE")
    n_clarify = sum(1 for c in cases if c["disposition"] == "NEEDS_CLARIFICATION")
    return {
        "n_cases": n,
        "proposal_before_mutation_all": proposal_compliance,
        "ambiguity_detection_c1_c2": ambiguity_ok,
        "non_overclarification_precise": non_overclarification,
        "any_silent_world": scope_fail,
        "commit_mismatch": commit_mismatch,
        "consequence_weak": consequence_weak,
        "n_clarifications": n_clarify,
        "cases": cases,
    }


def choose_label(summary: dict[str, Any]) -> str:
    cases = summary.get("cases") or []
    if not cases or summary.get("n_cases", 0) < 8:
        return "MIXED_SEMANTIC_PROPOSAL_RESULT"
    c1 = next((c for c in cases if c["id"] == "case1_bare_rejection"), None)
    c2 = next((c for c in cases if c["id"] == "case2_underspecified"), None)
    if c1 and c1["disposition"] != "NEEDS_CLARIFICATION":
        return "AMBIGUITY_LOCALIZATION_WEAK"
    if c2 and c2["disposition"] != "NEEDS_CLARIFICATION" and (c2.get("n_dry_runs") or 0) <= 1:
        return "AMBIGUITY_LOCALIZATION_WEAK"
    if not summary.get("proposal_before_mutation_all"):
        return "MIXED_SEMANTIC_PROPOSAL_RESULT"
    if summary.get("commit_mismatch"):
        return "PROPOSAL_COMMIT_MISMATCH"
    if summary.get("any_silent_world"):
        return "SCOPE_INFERENCE_REMAINS_WEAK"
    if summary.get("consequence_weak"):
        return "CONSEQUENCE_TRANSPARENCY_WEAK"
    precise_ok = summary.get("non_overclarification_precise")
    commits_ok = all(c.get("commit_matches_proposal") in {True, None} for c in cases)
    revert_ok = all(c.get("revert_ok") in {True, None} for c in cases)
    if summary.get("ambiguity_detection_c1_c2") and precise_ok and commits_ok and revert_ok and summary.get("proposal_before_mutation_all"):
        return "PROPOSAL_CLARIFICATION_LOOP_SUPPORTED"
    return "MIXED_SEMANTIC_PROPOSAL_RESULT"
