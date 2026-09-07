"""Deterministic purpose projector. Consumes normalized consumer tables. No source reread."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.contracts import (
    PURPOSE_A,
    PURPOSE_B,
    PURPOSE_C,
    PURPOSE_D,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.normalizer import (
    normalize_workspace,
    normalize_world,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.world_io import (
    active_contracts,
    clause_kinds,
    contracts,
    identity_from_dispositions,
    identity_from_tables,
    invoices,
)
from research.semantic_integration.domains.diligence.pass_localization.gold_derive import (
    A_CLAUSES,
    D_ASSIGN,
)


def strip_prefix(value: str, prefixes: tuple[str, ...] = ("invoice:", "contract:")) -> str:
    text = str(value)
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text


def class_rank(referent: str) -> tuple[int, str]:
    if referent.startswith("crm:"):
        return (0, referent)
    if referent.startswith("billing:"):
        return (1, referent)
    if referent.startswith("contract:"):
        return (2, referent)
    if referent.startswith("registry:"):
        return (3, referent)
    return (9, referent)


def orient(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right), key=class_rank))  # type: ignore[return-value]


def map_disposition(disp: str) -> str:
    return PURPOSE_B.disposition_mapping.get(disp, disp)


def _same(identity: list[dict[str, str]], a: str, b: str) -> bool:
    return any(
        row["disposition"] == "SAME_ENTITY" and {row["left"], row["right"]} == {a, b}
        for row in identity
    )


def _unresolved(identity: list[dict[str, str]], a: str, b: str) -> bool:
    return any(
        row["disposition"] == "UNRESOLVED" and {row["left"], row["right"]} == {a, b}
        for row in identity
    )


def _crm_for_billing(identity: list[dict[str, str]], billing: str) -> str | None:
    for row in identity:
        if row["disposition"] != "SAME_ENTITY":
            continue
        if row["right"] == billing and row["left"].startswith("crm:"):
            return row["left"]
        if row["left"] == billing and row["right"].startswith("crm:"):
            return row["right"]
    return None


def _name_linked(billed: str, counterparty_text: str) -> bool:
    billed_norm = billed.replace(",", "")
    ctext = counterparty_text.replace(",", "")
    return billed_norm in ctext or ctext in billed_norm


def _contract_for_billed(
    billed: str,
    contract_rows: list[dict[str, str]],
    active: dict[str, bool],
    identity: list[dict[str, str]],
) -> tuple[str | None, str]:
    billing = f"billing:{billed}"
    for rec in contract_rows:
        cid = str(rec["contract_id"])
        if active and not active.get(cid) and not active.get(strip_prefix(cid)):
            continue
        name_match = _name_linked(billed, rec["counterparty_text"])
        linked = _same(identity, billing, cid if cid.startswith("contract:") else f"contract:{strip_prefix(cid)}")
        if not name_match and not linked:
            continue
        cref = cid if cid.startswith("contract:") else f"contract:{strip_prefix(cid)}"
        if _unresolved(identity, billing, cref):
            return cid, PURPOSE_A.disposition_mapping.get("UNRESOLVED", "unresolved")
        return cid, PURPOSE_A.disposition_mapping.get("SAME_ENTITY", "asserted")
    return None, PURPOSE_A.disposition_mapping.get("UNRESOLVED", "unresolved")


def _kinds_for_purpose(raw: set[str], allowed: list[str]) -> list[str]:
    allowed_set = set(allowed)
    return sorted({kind for kind in raw if kind in allowed_set})


def project_tables(
    tables: dict[str, list[dict[str, Any]]],
    *,
    extra_identity: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    inv_rows = invoices(tables)
    contract_rows = contracts(tables)
    kinds = clause_kinds(tables)
    active = active_contracts(tables)
    identity = list(identity_from_tables(tables))
    if extra_identity:
        identity.extend(extra_identity)

    a_invoices = []
    for inv in inv_rows:
        cid, assoc = _contract_for_billed(str(inv["billed_name"]), contract_rows, active, identity)
        if not cid:
            continue
        if active and not (active.get(cid) or active.get(strip_prefix(cid))):
            continue
        raw_kinds = kinds.get(cid, set()) | kinds.get(strip_prefix(cid), set()) | kinds.get(f"contract:{strip_prefix(cid)}", set())
        a_ok = bool(raw_kinds & A_CLAUSES) or bool(set(_kinds_for_purpose(raw_kinds, PURPOSE_A.allowed_kinds)))
        if not a_ok:
            continue
        a_invoices.append(
            {
                "invoice_id": strip_prefix(inv["invoice_id"]),
                "billed_name": inv["billed_name"],
                "amount": inv.get("amount"),
                "currency": inv.get("currency"),
                "period": inv.get("period"),
                "status": inv.get("status"),
                "contract_id": strip_prefix(cid),
                "association": assoc,
            }
        )
    a_invoices.sort(key=lambda row: str(row["invoice_id"]))

    b_links = []
    seen: set[tuple[str, str, str]] = set()
    for row in identity:
        left, right = orient(row["left"], row["right"])
        epistemic = map_disposition(row["disposition"])
        if epistemic not in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}:
            continue
        if not left or not right:
            continue
        key = (left, right, epistemic)
        if key in seen:
            continue
        seen.add(key)
        b_links.append({"left": left, "right": right, "epistemic": epistemic})
    b_links.sort(key=lambda item: (item["left"], item["right"]))

    c_deps = []
    for rec in contract_rows:
        cid = str(rec["contract_id"])
        if active and not (active.get(cid) or active.get(strip_prefix(cid))):
            continue
        raw_kinds = kinds.get(cid, set()) | kinds.get(strip_prefix(cid), set()) | kinds.get(f"contract:{strip_prefix(cid)}", set())
        allowed = _kinds_for_purpose(raw_kinds, PURPOSE_C.allowed_kinds)
        if not allowed:
            continue
        billed_candidates = []
        for inv in inv_rows:
            found, _assoc = _contract_for_billed(str(inv["billed_name"]), contract_rows, active, identity)
            if found and strip_prefix(found) == strip_prefix(cid):
                billed_candidates.append(inv)
        if not billed_candidates:
            continue
        open_ids = sorted(
            {
                strip_prefix(inv["invoice_id"])
                for inv in billed_candidates
                if str(inv.get("status")) == "open"
            }
        )
        billed = str(billed_candidates[0]["billed_name"])
        billing = f"billing:{billed}"
        crm = _crm_for_billing(identity, billing)
        cref = cid if cid.startswith("contract:") else f"contract:{strip_prefix(cid)}"
        status = PURPOSE_C.disposition_mapping.get("SAME_ENTITY", "dependent")
        if _unresolved(identity, billing, cref):
            status = PURPOSE_C.disposition_mapping.get("UNRESOLVED", "unresolved")
        c_deps.append(
            {
                "counterparty": crm or billing,
                "contract_id": strip_prefix(cid),
                "open_invoice_ids": open_ids,
                "obligation_kinds": allowed,
                "status": status,
            }
        )
    c_deps.sort(key=lambda item: item["contract_id"])

    d_cases = []
    for inv in inv_rows:
        if str(inv.get("status")) != "open":
            continue
        billed = str(inv["billed_name"])
        billing = f"billing:{billed}"
        for rec in contract_rows:
            cid = str(rec["contract_id"])
            if active and not (active.get(cid) or active.get(strip_prefix(cid))):
                continue
            raw_kinds = kinds.get(cid, set()) | kinds.get(strip_prefix(cid), set()) | kinds.get(f"contract:{strip_prefix(cid)}", set())
            allowed = set(_kinds_for_purpose(raw_kinds, PURPOSE_D.allowed_kinds)) or (raw_kinds & D_ASSIGN)
            if not allowed:
                continue
            cref = cid if cid.startswith("contract:") else f"contract:{strip_prefix(cid)}"
            name_match = _name_linked(billed, rec["counterparty_text"])
            if not name_match and not _same(identity, billing, cref):
                continue
            d_cases.append(
                {
                    "invoice_id": strip_prefix(inv["invoice_id"]),
                    "contract_id": strip_prefix(cid),
                    "status": "matches",
                }
            )
    d_cases.sort(key=lambda item: item["invoice_id"])
    return {
        "a": {"purpose": "contractual_revenue_exposure", "invoices": a_invoices},
        "b": {"purpose": "counterparty_reconciliation", "links": b_links},
        "c": {"purpose": "commercial_dependency", "dependencies": c_deps},
        "d": {"purpose": "open_ar_assignment_restriction", "cases": d_cases},
        "normalization": None,
    }


def project_normalized(normalized: dict[str, Any], *, extra_identity: list[dict[str, str]] | None = None) -> dict[str, Any]:
    payload = project_tables(normalized["tables"], extra_identity=extra_identity)
    payload["normalization"] = {
        "consumer_relations_recovered": normalized.get("consumer_relations_recovered"),
        "missing_mappings": normalized.get("missing_mappings"),
        "role_binding_failures": normalized.get("role_binding_failures"),
    }
    return payload


def project_certified(world: Path, vocabulary: Path | None = None) -> dict[str, Any]:
    normalized = normalize_world(world, vocabulary=vocabulary)
    return project_normalized(normalized)


def project_workspace(workspace: Path) -> dict[str, Any]:
    extra = identity_from_dispositions(workspace / "05_dispositions.json")
    normalized = normalize_workspace(workspace)
    return project_normalized(normalized, extra_identity=extra)


def write_workspace_outputs(workspace: Path) -> dict[str, Any]:
    from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.abi_completeness import (
        check_abi,
    )

    world = workspace / "06_world" / "world.sqlite"
    if not world.exists():
        world = workspace / "world" / "world.sqlite"
    disp = workspace / "05_dispositions.json"

    abi = check_abi(
        workspace / "01_vocabulary.json",
        world_path=world if world.exists() else None,
        dispositions_path=disp if disp.exists() else None,
    )
    dest = workspace / "08_outputs"
    dest.mkdir(parents=True, exist_ok=True)
    (workspace / "08_abi_completeness.json").write_text(json.dumps(abi, indent=2) + "\n")
    if not abi.get("ok"):
        incomplete = {
            "abi_status": "INCOMPLETE_PURPOSE",
            "unsatisfied": abi.get("unsatisfied") or [],
            "ambiguous": abi.get("ambiguous") or [],
            "reasons": abi.get("unsatisfied_reasons") or {},
        }
        payload = {
            "a": {"purpose": "contractual_revenue_exposure", "invoices": [], **incomplete},
            "b": {"purpose": "counterparty_reconciliation", "links": [], **incomplete},
            "c": {"purpose": "commercial_dependency", "dependencies": [], **incomplete},
            "d": {"purpose": "open_ar_assignment_restriction", "cases": [], **incomplete},
            "normalization": {"skipped": True, "reason": "ABI_COMPLETENESS", "abi": abi},
        }
        (workspace / "08_normalization.json").write_text(
            json.dumps(payload["normalization"], indent=2) + "\n"
        )
        for letter in ("a", "b", "c", "d"):
            obj = {k: v for k, v in payload[letter].items()}
            (dest / f"{letter}.json").write_text(json.dumps(obj, indent=2) + "\n")
            out = workspace / "purpose_ir" / letter / "output.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(obj, indent=2) + "\n")
        return payload
    payload = project_workspace(workspace)
    (workspace / "08_normalization.json").write_text(
        json.dumps(payload.get("normalization") or {}, indent=2) + "\n"
    )
    for letter in ("a", "b", "c", "d"):
        obj = {k: v for k, v in payload[letter].items()}
        (dest / f"{letter}.json").write_text(json.dumps(obj, indent=2) + "\n")
        out = workspace / "purpose_ir" / letter / "output.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(obj, indent=2) + "\n")
    return payload
