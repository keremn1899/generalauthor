"""B0 exact-contract normalizer. No relation-name heuristics. No semantic-family hints."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.schema_normalization_v1.canonical import (
    CANONICAL_RELATIONS,
    CLAUSE_KIND_ROLES,
    CLAUSE_POSITIVE,
    CRM_NAME_ROLES,
    IDENTITY_DISPOSITIONS,
    INVOICE_ROLE_FIELDS,
    REGISTRY_NAME_ROLES,
)
from research.semantic_integration.schema_normalization_v1.catalog import (
    contracts_for_world,
    dict_tables,
)

# Consumer-interface role vocabulary (certified World). Not constructor table names.
CONSUMER_ROLES = {
    "invoice_id",
    "billed_name",
    "amount",
    "currency",
    "period",
    "status",
    "contract_id",
    "counterparty_text",
    "active",
    "clause_kind",
    "left",
    "right",
    "disposition",
    "account",
    "account_name",
    "company_number",
    "legal_name",
}


def _disp_set(contract: dict[str, Any]) -> set[str]:
    values = contract.get("dispositions") or contract.get("allowed_dispositions") or []
    return {str(v).upper() for v in values}


def _roles(contract: dict[str, Any]) -> list[dict[str, str]]:
    return list(contract.get("physical_roles") or [])


def _role_names(contract: dict[str, Any]) -> set[str]:
    return {str(r.get("role_name") or "") for r in _roles(contract)}


def is_identity_contract(contract: dict[str, Any]) -> bool:
    return IDENTITY_DISPOSITIONS <= _disp_set(contract)


def is_clause_contract(contract: dict[str, Any]) -> bool:
    disp = _disp_set(contract)
    return bool(disp & CLAUSE_POSITIVE) and "SAME_ENTITY" not in disp


def col(contract: dict[str, Any], role: str) -> str | None:
    for item in _roles(contract):
        if item.get("role_name") == role:
            return item.get("column_name") or role
    return None


def join_on_role(tables: dict[str, list[dict]], attached: dict[str, dict], role: str) -> dict[str, dict[str, Any]]:
    """Assemble attribute bags keyed by the physical column of a shared role name."""
    bags: dict[str, dict[str, Any]] = defaultdict(dict)
    for table, contract in attached.items():
        column = col(contract, role)
        if not column:
            continue
        for row in tables.get(table) or []:
            key = str(row.get(column) or "")
            if not key:
                continue
            for item in _roles(contract):
                rname = item.get("role_name") or ""
                cname = item.get("column_name") or rname
                if rname == role:
                    bags[key].setdefault(role, key)
                    continue
                if cname in row:
                    bags[key][rname] = row[cname]
    return dict(bags)


def _identity_rows(
    tables: dict[str, list[dict]],
    attached: dict[str, dict],
    dispositions_sidecar: list[dict] | None,
) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    mappings: list[dict[str, str]] = []
    for table, contract in attached.items():
        if not is_identity_contract(contract):
            continue
        left_c = col(contract, "left")
        right_c = col(contract, "right")
        disp_c = col(contract, "disposition")
        fixed = str(contract.get("fixed_disposition") or "").upper()
        for row in tables.get(table) or []:
            if not left_c or not right_c:
                continue
            disp = str(row.get(disp_c) or "").upper() if disp_c else ""
            if disp not in IDENTITY_DISPOSITIONS:
                disp = fixed if fixed in IDENTITY_DISPOSITIONS else ""
            found.append(
                {
                    "left": str(row.get(left_c)),
                    "right": str(row.get(right_c)),
                    "disposition": disp,
                    "_table": table,
                }
            )
            mappings.append({"table": table, "canonical": "identity_judgment", "reason": "disposition_set"})
    if dispositions_sidecar:
        for row in dispositions_sidecar:
            values = row.get("values") if isinstance(row.get("values"), dict) else row
            left = values.get("left") if isinstance(values, dict) else None
            right = values.get("right") if isinstance(values, dict) else None
            disp = str(row.get("final_admitted_disposition") or row.get("disposition") or "").upper()
            if left and right and disp in IDENTITY_DISPOSITIONS:
                key = {str(left), str(right)}
                matched = False
                for item in found:
                    if {item["left"], item["right"]} == key:
                        if not item["disposition"]:
                            item["disposition"] = disp
                        matched = True
                if not matched:
                    found.append({"left": str(left), "right": str(right), "disposition": disp, "_table": "sidecar"})
    cleaned = []
    for item in found:
        if item.get("disposition") in IDENTITY_DISPOSITIONS:
            cleaned.append({"left": item["left"], "right": item["right"], "disposition": item["disposition"]})
    return cleaned


def _clause_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    out = []
    for table, contract in attached.items():
        kind_role = next((r for r in CLAUSE_KIND_ROLES if r in _role_names(contract)), None)
        contract_role = next((r for r in ("contract", "contract_id") if r in _role_names(contract)), None)
        if not kind_role or not contract_role:
            continue
        if is_identity_contract(contract):
            continue
        disp_c = col(contract, "disposition")
        kind_c = col(contract, kind_role)
        cid_c = col(contract, contract_role)
        clause_like = is_clause_contract(contract) or (not _disp_set(contract) and kind_role in CLAUSE_KIND_ROLES)
        if not clause_like and disp_c is None and not is_clause_contract(contract):
            # presence-only clause table: clause_kind role, no identity dispositions
            if kind_role not in CLAUSE_KIND_ROLES:
                continue
        for row in tables.get(table) or []:
            disp = str(row.get(disp_c) or "").upper() if disp_c else "PRESENT"
            if disp in CLAUSE_POSITIVE or (disp_c is None and row.get(kind_c)):
                out.append(
                    {
                        "contract_id": str(row.get(cid_c)),
                        "clause_kind": str(row.get(kind_c)),
                    }
                )
            elif disp in {"ABSENT", "REJECT"}:
                continue
    return out


def _invoice_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, Any]]:
    bags = join_on_role(tables, attached, "invoice")
    for key, bag in list(bags.items()):
        bag.setdefault("invoice_id", key)
    # also already-wide tables whose roles include billed_name
    for table, contract in attached.items():
        names = _role_names(contract)
        if "billed_name" in names and "invoice_id" in names:
            id_c = col(contract, "invoice_id")
            for row in tables.get(table) or []:
                key = str(row.get(id_c) or "")
                bags.setdefault(key, {})
                for role, field in INVOICE_ROLE_FIELDS.items():
                    c = col(contract, role)
                    if c and c in row:
                        bags[key][field] = row[c]
                bags[key]["invoice_id"] = key
    rows = []
    for key, bag in bags.items():
        if "billed_name" not in bag and "billed_name" not in {k for k in bag}:
            continue
        billed = bag.get("billed_name")
        if billed is None:
            continue
        rows.append(
            {
                "invoice_id": bag.get("invoice_id") or key,
                "billed_name": bag.get("billed_name"),
                "amount": bag.get("amount"),
                "currency": bag.get("currency"),
                "period": bag.get("period"),
                "status": bag.get("status"),
            }
        )
    return rows


def _contract_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    bags = join_on_role(tables, attached, "contract")
    for table, contract in attached.items():
        names = _role_names(contract)
        if "counterparty_text" in names and "contract_id" in names:
            cid = col(contract, "contract_id")
            ctext = col(contract, "counterparty_text")
            for row in tables.get(table) or []:
                key = str(row.get(cid) or "")
                bags.setdefault(key, {})
                bags[key]["counterparty_text"] = row.get(ctext)
                bags[key]["contract_id"] = key
    rows = []
    for key, bag in bags.items():
        text = bag.get("counterparty_text")
        if text is None:
            continue
        rows.append({"contract_id": bag.get("contract_id") or key, "counterparty_text": str(text)})
    return rows


def _active_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, Any]]:
    out = []
    for table, contract in attached.items():
        if "active" not in _role_names(contract):
            continue
        cid = col(contract, "contract") or col(contract, "contract_id")
        act = col(contract, "active")
        for row in tables.get(table) or []:
            out.append({"contract_id": str(row.get(cid)), "active": bool(row.get(act))})
    return out


def _crm_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    out = []
    for table, contract in attached.items():
        names = _role_names(contract)
        if "account_name" not in names:
            continue
        acc = col(contract, "account") or col(contract, "account_id")
        name = col(contract, "account_name")
        for row in tables.get(table) or []:
            out.append({"account": str(row.get(acc)), "account_name": str(row.get(name))})
    return out


def _registry_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    bags = join_on_role(tables, attached, "entity")
    for table, contract in attached.items():
        names = _role_names(contract)
        if "legal_name" in names and "company_number" in names:
            num = col(contract, "company_number")
            legal = col(contract, "legal_name")
            status = col(contract, "status")
            for row in tables.get(table) or []:
                bags.setdefault(str(row.get(num)), {})
                bags[str(row.get(num))]["legal_name"] = row.get(legal)
                bags[str(row.get(num))]["status"] = row.get(status)
                bags[str(row.get(num))]["company_number"] = row.get(num)
    rows = []
    for key, bag in bags.items():
        if "legal_name" not in bag:
            continue
        rows.append(
            {
                "company_number": str(bag.get("company_number") or key),
                "legal_name": str(bag.get("legal_name")),
                "status": bag.get("status"),
            }
        )
    return rows


def load_sidecar_dispositions(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload if isinstance(payload, list) else []


def normalize_world(
    world: Path,
    *,
    vocabulary: Path | None,
    dispositions: Path | None = None,
    use_family_hint: bool = False,
) -> dict[str, Any]:
    tables = dict_tables(world)
    attached = contracts_for_world(world, vocabulary)
    sidecar = load_sidecar_dispositions(dispositions) if dispositions else []
    identity = _identity_rows(tables, attached, sidecar)
    invoices = _invoice_rows(tables, attached)
    contracts = _contract_rows(tables, attached)
    clauses = _clause_rows(tables, attached)
    active = _active_rows(tables, attached)
    crm = _crm_rows(tables, attached)
    registry = _registry_rows(tables, attached)
    missed = []
    if not identity:
        missed.append("identity_judgment")
    if not invoices:
        missed.append("invoice_record")
    if not contracts:
        missed.append("contract_record")
    false_mappings = []
    if use_family_hint:
        for table, contract in attached.items():
            if str(contract.get("semantic_family_hint") or "").upper() == "IDENTITY" and not is_identity_contract(contract):
                false_mappings.append({"table": table, "hint": "IDENTITY", "reason": "hint_without_disposition_contract"})
    recovered = [name for name, rows in (
        ("invoice_record", invoices),
        ("contract_record", contracts),
        ("contract_active", active),
        ("contract_clause_kind", clauses),
        ("identity_judgment", identity),
        ("crm_record", crm),
        ("registry_record", registry),
    ) if rows]
    return {
        "tables": {
            "invoice_record": invoices,
            "contract_record": contracts,
            "contract_active": active,
            "contract_clause_kind": clauses,
            "identity_judgment": identity,
            "crm_record": crm,
            "registry_record": registry,
        },
        "canonical_relations_recovered": recovered,
        "required_mappings_missed": missed,
        "false_mappings": false_mappings,
        "used_relation_names": False,
        "used_family_hints": use_family_hint,
        "cases_requiring_relation_name_knowledge": [],
        "cases_contracts_cannot_disambiguate": missed,
    }


def project_normalized(normalized: dict[str, Any]) -> dict[str, Any]:
    from research.semantic_integration.domains.diligence.constructor_v2.runtime.projector import (
        project_tables,
    )

    return project_tables(normalized["tables"])
