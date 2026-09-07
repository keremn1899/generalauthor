"""Score Constructor v3 trials. Keep pass failures attributed, not collapsed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.abi_completeness import (
    check_abi,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.normalizer import (
    normalize_world,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.provenance import (
    validate_provenance,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.validators import (
    axis_b_payload,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.workspaces import TRIALS
from research.semantic_integration.domains.diligence.evaluator import (
    load_json,
    score_purpose_a,
    score_purpose_b,
    score_purpose_c,
    score_purpose_d,
)
from research.semantic_integration.domains.diligence.pass_localization.inspect_world import (
    contains_token,
    disposition_rows,
    grounding_rate,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    all_oracle_pairs,
    load_dispositions,
    load_obligations,
    pair_from_obj,
)
from research.semantic_integration.domains.diligence.pass_localization.score_passes import (
    MECHANICAL_TOKENS,
)

HIDDEN = Path(__file__).resolve().parent.parent / "hidden"


def snapshot(trial: int, pass_id: str) -> Path:
    return TRIALS / f"T{trial}" / "passes" / pass_id / "workspace_snapshot"


def _local_p0(trial: int) -> dict[str, Any]:
    payload = load_json(snapshot(trial, "p0") / "00_intention_contract.json") or {}
    purposes = payload.get("purposes") if isinstance(payload, dict) else None
    if not isinstance(purposes, dict):
        return {"pass": False, "reason": "missing purposes"}
    missing = [letter for letter in ("A", "B", "C") if letter not in purposes]
    required = (
        "objective",
        "universe_scope",
        "required_output_shape",
        "required_semantic_distinctions",
        "epistemic_requirements",
        "allowed_unresolved_states",
        "completeness_expectations",
        "purpose_specific_policies",
    )
    field_gaps = []
    blob = json.dumps(purposes).lower()
    checks = {
        "a_active_contracts": "active" in blob,
        "a_acquisition_policy": any(
            token in blob for token in ("change of control", "assignment", "consent", "notice")
        ),
        "b_unresolved": "unresolved" in blob,
        "c_obligation_kinds": any(
            token in blob for token in ("exclusiv", "auto-renew", "auto_renew", "rolling")
        ),
        "policy_field_present": all(
            isinstance(purposes.get(letter), dict)
            and "purpose_specific_policies" in purposes[letter]
            for letter in ("A", "B", "C")
            if letter in purposes
        ),
    }
    for letter, obj in purposes.items():
        if not isinstance(obj, dict):
            continue
        for field in required:
            if field not in obj:
                field_gaps.append(f"{letter}.{field}")
    ok = not missing and not field_gaps and all(checks.values())
    return {"pass": ok, "missing_purposes": missing, "field_gaps": field_gaps, "checks": checks}


def score_p1(trial: int) -> dict[str, Any]:
    payload = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or {}
    relations = payload.get("relations") if isinstance(payload, dict) else None
    if not isinstance(relations, list) or not relations:
        return {"pass": False, "reason": "missing relations"}
    world = [row for row in relations if isinstance(row, dict) and row.get("admission") == "WORLD"]
    purpose = [row for row in relations if isinstance(row, dict) and row.get("admission") == "PURPOSE"]
    leakage = [
        row.get("name")
        for row in world
        if any(
            token in str(row.get("name", "")).lower()
            for token in ("purpose_a", "purpose_b", "purpose_c", "answer_to", "analysis_result", "high_risk")
        )
    ]
    semantic = [row for row in relations if row.get("construction_class") == "SEMANTIC"]
    mechanical = [row for row in relations if row.get("construction_class") == "MECHANICAL"]
    unrepresentable = any("new primitive" in json.dumps(row).lower() for row in relations)
    identities = []
    missing_counterparty_bind = []
    for row in relations:
        if not isinstance(row, dict):
            continue
        for role in row.get("roles") or []:
            if not isinstance(role, dict):
                continue
            sid = role.get("semantic_identity")
            if sid:
                identities.append(f"{row.get('name')}.{role.get('name')}->{sid}")
            if str(role.get("name") or "") == "counterparty" and sid != "counterparty_text":
                missing_counterparty_bind.append(row.get("name"))
    ok = bool(mechanical) and bool(semantic) and bool(purpose) and not leakage and not unrepresentable
    abi = check_abi(snapshot(trial, "p1") / "01_vocabulary.json")
    return {
        "pass": ok,
        "n_relations": len(relations),
        "n_world": len(world),
        "n_purpose": len(purpose),
        "n_semantic": len(semantic),
        "world_purpose_leakage": leakage,
        "unrepresentable_claimed": unrepresentable,
        "semantic_identity_bindings": identities,
        "counterparty_without_consumer_bind": missing_counterparty_bind,
        "abi": abi,
    }


def score_p2(trial: int) -> dict[str, Any]:
    world = snapshot(trial, "p2") / "02_mechanical_world" / "world.sqlite"
    ground = grounding_rate(world)
    recovered = {token: contains_token(world, token) for token in MECHANICAL_TOKENS}
    missing = [token for token, ok in recovered.items() if not ok]
    early_identity = [
        row
        for row in disposition_rows(world)
        if row["disposition"] in {"SAME_ENTITY", "DISTINCT"}
    ]
    ungrounded = ground.get("ungrounded") or 0
    ok = world.exists() and ungrounded == 0 and len(missing) <= 3 and not early_identity
    return {
        "pass": ok,
        "grounding": ground,
        "missing_mechanical_tokens": missing,
        "early_identity_closures": early_identity[:20],
        "mechanical_delegated_to_semantics": bool(early_identity),
    }


def score_p3(trial: int) -> dict[str, Any]:
    obligations = load_obligations(snapshot(trial, "p3") / "03_obligations.json")
    generated = {pair_from_obj(row) for row in obligations}
    generated.discard(None)
    oracle = all_oracle_pairs()
    required = set(oracle)
    hit = generated & required
    recall = len(hit) / len(required) if required else None
    precision = len(hit) / len(generated) if generated else None
    invalid = [row for row in obligations if not isinstance(row, dict) or not row.get("obligation_id")]
    ok = recall is not None and recall >= 0.7
    return {
        "pass": ok,
        "n_obligations": len(obligations),
        "required": len(required),
        "required_hit": len(hit),
        "required_missed": sorted("_".join(pair) for pair in sorted(required - generated)),
        "recall": recall,
        "precision_vs_oracle_pairs": precision,
        "unnecessary": len(generated - required),
        "duplicate_obligations": len(obligations) - len(generated),
        "invalid_obligations": len(invalid),
    }


def score_p4(trial: int) -> dict[str, Any]:
    packets_dir = snapshot(trial, "p4") / "04_packets"
    obligations = load_obligations(snapshot(trial, "p3") / "03_obligations.json")
    if not packets_dir.is_dir():
        return {"pass": False, "reason": "no packets"}
    files = list(packets_dir.glob("*.json"))
    oracle = all_oracle_pairs()
    sufficient = 0
    required_with_packet = 0
    notes_hits = 0
    for row in obligations:
        pair = pair_from_obj(row)
        oid = str(row.get("obligation_id") or "")
        packet_path = packets_dir / f"{oid}.json"
        if not packet_path.exists() and files:
            matches = [path for path in files if oid and oid in path.name]
            packet_path = matches[0] if matches else packet_path
        if not packet_path.exists():
            continue
        blob = packet_path.read_text(encoding="utf-8").lower()
        if pair in oracle:
            required_with_packet += 1
            has_loc = "source" in blob or "crm" in blob or "registry" in blob or "contract" in blob or "notes" in blob
            if has_loc:
                sufficient += 1
            if "commercial_notes" in blob or "notes" in blob:
                notes_hits += 1
    ok = bool(files) and (required_with_packet == 0 or sufficient / required_with_packet >= 0.7)
    return {
        "pass": ok,
        "n_packets": len(files),
        "required_with_packet": required_with_packet,
        "sufficient_required": sufficient,
        "packets_mentioning_notes": notes_hits,
    }


def score_p5(trial: int) -> dict[str, Any]:
    rows = load_dispositions(snapshot(trial, "p5") / "05_dispositions.json")
    audit = load_json(snapshot(trial, "p5") / "05_adjudication_audit.json") or []
    oracle = all_oracle_pairs()
    compared = 0
    correct = 0
    closure = 0
    under = 0
    polarity = 0
    false_distinct = 0
    same_want = 0
    same_hit = 0
    distinct_want = 0
    distinct_hit = 0
    unresolved_preserved = 0
    delaware = pair_from_obj(
        {"left": "billing:Northbridge Analytics Inc.", "right": "registry:3840192"}
    )
    delaware_disp = None
    for row in rows:
        pair = pair_from_obj(row)
        if pair is None or pair not in oracle:
            continue
        compared += 1
        want = oracle[pair]
        got = str(row.get("disposition") or "").upper()
        if pair == delaware:
            delaware_disp = got
        if got == want:
            correct += 1
        if want == "SAME_ENTITY":
            same_want += 1
            if got == "SAME_ENTITY":
                same_hit += 1
        if want == "DISTINCT":
            distinct_want += 1
            if got == "DISTINCT":
                distinct_hit += 1
        if want == "UNRESOLVED" and got == "UNRESOLVED":
            unresolved_preserved += 1
        if want == "UNRESOLVED" and got in {"SAME_ENTITY", "DISTINCT"}:
            closure += 1
        if want in {"SAME_ENTITY", "DISTINCT"} and got == "UNRESOLVED":
            under += 1
        if {want, got} == {"SAME_ENTITY", "DISTINCT"}:
            polarity += 1
        elif want != "DISTINCT" and got == "DISTINCT":
            false_distinct += 1
    structural_changed = sum(
        1 for row in audit if isinstance(row, dict) and row.get("initial_disposition") != row.get("final_disposition")
    )
    gate_ran = sum(1 for row in audit if isinstance(row, dict) and row.get("negative_closure"))
    gate_downgraded = sum(
        1
        for row in audit
        if isinstance(row, dict)
        and str(row.get("initial_disposition") or "").upper() == "DISTINCT"
        and str(row.get("final_disposition") or "").upper() == "UNRESOLVED"
        and str((row.get("negative_closure") or {}).get("result") or "").upper() == "NOT_ESTABLISHED"
    )
    acc = correct / compared if compared else None
    coverage = (same_hit + distinct_hit) / (same_want + distinct_want) if (same_want + distinct_want) else None
    ok = compared > 0 and closure == 0
    return {
        "pass": ok,
        "compared": compared,
        "correct": correct,
        "accuracy": acc,
        "incorrect_semantic_closure": closure,
        "incorrect_under_closure": under,
        "incorrect_polarity": polarity,
        "incorrect_rejection": false_distinct,
        "same_recall": same_hit / same_want if same_want else None,
        "distinct_recall": distinct_hit / distinct_want if distinct_want else None,
        "coverage": coverage,
        "unresolved_preservation": unresolved_preserved,
        "delaware_inc_disposition": delaware_disp,
        "delaware_should_be": "UNRESOLVED",
        "structural_changed": structural_changed,
        "verifier_changed": 0,
        "gate_ran": gate_ran,
        "gate_downgraded": gate_downgraded,
        "audit_n": len(audit) if isinstance(audit, list) else 0,
    }


def score_p6(trial: int) -> dict[str, Any]:
    admission = load_json(snapshot(trial, "p6") / "06_admission.json") or {}
    vocab = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or {}
    relations = vocab.get("relations") if isinstance(vocab, dict) else []
    world_answers = [
        row.get("name")
        for row in relations or []
        if row.get("admission") == "WORLD"
        and any(tok in str(row.get("name", "")).lower() for tok in ("purpose_a", "purpose_b", "purpose_c"))
    ]
    blob = json.dumps(admission).upper()
    identity_world = "WORLD" in blob
    world = snapshot(trial, "p6") / "06_world" / "world.sqlite"
    provenance = load_json(snapshot(trial, "p6") / "06_provenance.json") or validate_provenance(world)
    ok = world.exists() and not world_answers and bool(provenance.get("ok"))
    return {
        "pass": ok,
        "sqlite": world.exists(),
        "purpose_output_promoted_world": world_answers,
        "admission_mentions_world": identity_world,
        "provenance": provenance,
        "ungrounded_count": provenance.get("ungrounded_count"),
    }


def score_p7(trial: int) -> dict[str, Any]:
    spec = load_json(snapshot(trial, "p7") / "07_derivations.json")
    derive = snapshot(trial, "p7") / "construction" / "derivations" / "derive_purposes.py"
    if spec is None:
        return {"pass": False, "reason": "missing derivations json"}
    blob = json.dumps(spec).lower()
    checks = {
        "required_premise": "required" in blob,
        "blocking_unresolved": "blocking" in blob or "unresolved" in blob,
        "derive_script": derive.exists(),
    }
    return {"pass": all(checks.values()), "checks": checks}


def attribute_p8(
    *,
    a: dict,
    b: dict,
    c: dict,
    d: dict,
    p3: dict,
    p5: dict,
    p6: dict,
    normalization: dict,
    abi: dict,
) -> list[str]:
    reasons = []
    if (p5.get("incorrect_semantic_closure") or 0) > 0:
        reasons.append("unsupported_closure")
    if not a.get("pass") or not b.get("exact") or not c.get("pass"):
        if (p5.get("incorrect_under_closure") or 0) > 0:
            reasons.append("semantic_under_closure")
        if p3.get("recall") is not None and p3["recall"] < 0.7:
            reasons.append("frontier_failure")
        missed = normalization.get("missing_mappings") or []
        binds = normalization.get("role_binding_failures") or []
        if abi and not abi.get("ok"):
            reasons.append("ABI completeness failure")
        if "contract_record" in missed or (binds and "contract_record" in missed):
            reasons.append("normalization_failure")
        if (p6.get("ungrounded_count") or 0) > 0:
            reasons.append("grounding/provenance failure")
        if not reasons:
            reasons.append("semantic_fact_failure")
        if a.get("pass") and c.get("pass") and not b.get("exact"):
            reasons.append("projection_failure")
    if d and not d.get("pass"):
        if "semantic_fact_failure" not in reasons and "semantic_under_closure" not in reasons:
            reasons.append("semantic_fact_failure")
    return sorted(set(reasons))


def score_p8(trial: int) -> dict[str, Any]:
    expected_a = load_json(HIDDEN / "expected" / "purpose_a.json")
    expected_b = load_json(HIDDEN / "expected" / "purpose_b.json")
    expected_c = load_json(HIDDEN / "expected" / "purpose_c.json")
    expected_d = load_json(HIDDEN / "expected" / "purpose_d.json")
    snap = snapshot(trial, "p8")
    actual_a = load_json(snap / "08_outputs" / "a.json") or load_json(snap / "purpose_ir" / "a" / "output.json")
    actual_b = load_json(snap / "08_outputs" / "b.json") or load_json(snap / "purpose_ir" / "b" / "output.json")
    actual_c = load_json(snap / "08_outputs" / "c.json") or load_json(snap / "purpose_ir" / "c" / "output.json")
    actual_d = load_json(snap / "08_outputs" / "d.json") or load_json(snap / "purpose_ir" / "d" / "output.json")
    a = score_purpose_a(actual_a, expected_a)
    b = score_purpose_b(actual_b, expected_b)
    c = score_purpose_c(actual_c, expected_c)
    d = score_purpose_d(actual_d, expected_d)
    world = snapshot(trial, "p6") / "06_world" / "world.sqlite"
    vocab = snapshot(trial, "p1") / "01_vocabulary.json"
    disp = snapshot(trial, "p5") / "05_dispositions.json"
    normalization = {}
    if world.exists():
        normalization = normalize_world(world, vocabulary=vocab, dispositions=disp)
        keep = {
            "consumer_relations_required": normalization.get("consumer_relations_required"),
            "consumer_relations_recovered": normalization.get("consumer_relations_recovered"),
            "missing_mappings": normalization.get("missing_mappings"),
            "false_mappings": normalization.get("false_mappings"),
            "role_binding_failures": normalization.get("role_binding_failures"),
        }
        normalization = keep
    integrity = axis_b_payload(world, (actual_c or {}).get("dependencies") or []) if world.exists() else {}
    unresolved_null = [
        row
        for row in (actual_b or {}).get("links") or []
        if row.get("epistemic") == "UNRESOLVED" and (not row.get("left") or not row.get("right"))
    ]
    reject_to_unresolved = [
        row
        for row in (actual_b or {}).get("links") or []
        if row.get("epistemic") == "UNRESOLVED" and "REJECT" in json.dumps(row)
    ]
    prefix_fail = [
        row
        for row in (actual_a or {}).get("invoices") or []
        if str(row.get("invoice_id") or "").startswith("invoice:")
        or str(row.get("contract_id") or "").startswith("contract:")
    ]
    p3 = score_p3(trial) if snapshot(trial, "p3").joinpath("03_obligations.json").exists() else {}
    p5 = score_p5(trial) if snapshot(trial, "p5").joinpath("05_dispositions.json").exists() else {}
    p6 = score_p6(trial) if world.exists() else {}
    abi = load_json(snap / "08_abi_completeness.json") or check_abi(vocab)
    attribution = attribute_p8(a=a, b=b, c=c, d=d, p3=p3, p5=p5, p6=p6, normalization=normalization, abi=abi)
    return {
        "pass": bool(a["pass"] and b.get("exact") and c["pass"] and abi.get("ok")),
        "A": a,
        "B": b,
        "C": c,
        "D": d,
        "source_rereads": [],
        "zero_source_rereads": True,
        "axis_b": integrity,
        "unresolved_candidate_loss": unresolved_null,
        "reject_to_unresolved": reject_to_unresolved,
        "identifier_render_failures": prefix_fail,
        "normalization": normalization,
        "abi": abi,
        "failure_attribution": attribution,
    }


SCORERS = {
    "p0": _local_p0,
    "p1": score_p1,
    "p2": score_p2,
    "p3": score_p3,
    "p4": score_p4,
    "p5": score_p5,
    "p6": score_p6,
    "p7": score_p7,
    "p8": score_p8,
}


def score_trial(trial: int) -> dict[str, Any]:
    return {pass_id: scorer(trial) for pass_id, scorer in SCORERS.items()}


def score_all() -> dict[str, Any]:
    matrix = {}
    for trial in range(1, 6):
        if (TRIALS / f"T{trial}" / "passes" / "p0" / "agent.json").exists():
            matrix[f"T{trial}"] = score_trial(trial)
    return matrix


if __name__ == "__main__":
    print(json.dumps(score_all(), indent=2, sort_keys=True))
