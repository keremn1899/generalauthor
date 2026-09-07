"""Admit dispositions under strategy-specific deterministic rules. No resample."""

from __future__ import annotations

from typing import Any


def a3_admit(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    claims = payload.get("claims") if isinstance(payload.get("claims"), list) else []
    established = [c for c in claims if isinstance(c, dict) and str(c.get("status") or "").upper() == "ESTABLISHED"]
    burdens = {str(c.get("burden") or "").lower() for c in established}
    proposed = str(payload.get("disposition") or "UNRESOLVED").upper()
    if "unresolved_preservation" in burdens:
        return "UNRESOLVED", {"rule": "unresolved_preservation_established"}
    if proposed == "SAME_ENTITY" and "identity" in burdens and "distinctness" not in burdens:
        return "SAME_ENTITY", {"rule": "identity_burden_established"}
    if proposed == "DISTINCT" and "distinctness" in burdens and "identity" not in burdens:
        return "DISTINCT", {"rule": "distinctness_burden_established"}
    if proposed == "UNRESOLVED":
        return "UNRESOLVED", {"rule": "proposed_unresolved"}
    return "UNRESOLVED", {"rule": "claims_do_not_license_proposed_closure", "proposed": proposed}


def a4_admit(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    proposed = str(payload.get("proposed_disposition") or payload.get("disposition") or "UNRESOLVED").upper()
    obligations = payload.get("proof_obligations") if isinstance(payload.get("proof_obligations"), list) else []
    if proposed not in {"SAME_ENTITY", "DISTINCT"}:
        return "UNRESOLVED", {"rule": "unresolved"}
    required = [
        o for o in obligations
        if isinstance(o, dict) and str(o.get("required_for") or "").upper() == proposed
    ]
    if not required:
        return "UNRESOLVED", {"rule": "no_required_obligations_marked_for_proposed"}
    if all(bool(o.get("satisfied")) for o in required):
        unsat = payload.get("unsatisfied_obligations") or []
        if unsat:
            return "UNRESOLVED", {"rule": "unsatisfied_obligations_present"}
        return proposed, {"rule": "all_required_obligations_satisfied"}
    return "UNRESOLVED", {"rule": "required_obligation_unsatisfied"}


def a5_admit(payload: dict[str, Any], propositions: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    proposed = str(payload.get("disposition") or "UNRESOLVED").upper()
    tags = {str(p.get("establishes") or "").lower() for p in propositions}
    if "unresolved_preservation" in tags:
        return "UNRESOLVED", {"rule": "evidence_preserves_unresolved"}
    if proposed == "SAME_ENTITY" and "identity" in tags:
        return "SAME_ENTITY", {"rule": "identity_proposition_present"}
    if proposed == "DISTINCT" and "distinctness" in tags:
        return "DISTINCT", {"rule": "distinctness_proposition_present"}
    if proposed == "UNRESOLVED":
        return "UNRESOLVED", {"rule": "proposed_unresolved"}
    return "UNRESOLVED", {"rule": "propositions_do_not_license_closure", "proposed": proposed}


def a6_admit(payload: dict[str, Any], packet: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.parse import (
        evidence_in_packet,
    )

    proposed = str(payload.get("disposition") or "UNRESOLVED").upper()
    steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    if proposed not in {"SAME_ENTITY", "DISTINCT"}:
        return "UNRESOLVED", {"rule": "unresolved"}
    if not steps:
        return "UNRESOLVED", {"rule": "no_proof_steps"}
    for step in steps:
        if not isinstance(step, dict):
            return "UNRESOLVED", {"rule": "malformed_step"}
        grounding = step.get("grounding")
        mechanical = bool(step.get("mechanical"))
        if grounding:
            if not evidence_in_packet(grounding, packet):
                return "UNRESOLVED", {"rule": "step_grounding_not_in_packet"}
        elif not mechanical:
            return "UNRESOLVED", {"rule": "ungrounded_nonmechanical_step"}
    evidence = payload.get("supporting_evidence")
    if proposed in {"SAME_ENTITY", "DISTINCT"} and not evidence_in_packet(evidence, packet):
        return "UNRESOLVED", {"rule": "supporting_evidence_not_in_packet"}
    return proposed, {"rule": "steps_grounded"}


def a2_apply_critic(proposed: str, critic: dict[str, Any] | None) -> tuple[str, str]:
    proposed = (proposed or "UNRESOLVED").upper()
    if not critic:
        return "UNRESOLVED", "missing_critic"
    decision = str(critic.get("decision") or "").upper()
    if proposed == "UNRESOLVED":
        return "UNRESOLVED", "cannot_upgrade"
    if decision == "CONFIRM" and proposed in {"SAME_ENTITY", "DISTINCT"}:
        return proposed, "confirmed"
    return "UNRESOLVED", "downgraded"
