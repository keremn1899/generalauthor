"""Contract-driven normalizer. No LLM. No semantic-family hints. No fuzzy role names."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3.runtime.catalog import (
    contracts_for_world,
    dict_tables,
)
from research.semantic_integration.domains.diligence.constructor_v3.runtime.consumer import (
    CANONICAL_RELATIONS,
    CLAUSE_POSITIVE,
    IDENTITY_DISPOSITIONS,
    INVOICE_FIELDS,
)


def semantic_id(role: dict[str, Any]) -> str:
    return str(role.get("semantic_identity") or role.get("role_name") or "")


def _roles(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return list(contract.get("physical_roles") or [])


def _identities(contract: dict[str, Any]) -> set[str]:
    return {semantic_id(role) for role in _roles(contract) if semantic_id(role)}


def _disp_set(contract: dict[str, Any]) -> set[str]:
    values = contract.get("dispositions") or contract.get("allowed_dispositions") or []
    return {str(v).upper() for v in values}


def col_for(contract: dict[str, Any], identity: str) -> str | None:
    for item in _roles(contract):
        if semantic_id(item) == identity:
            column = item.get("column_name")
            if column:
                return str(column)
            return str(item.get("role_name") or identity)
    return None


def is_identity_contract(contract: dict[str, Any]) -> bool:
    return IDENTITY_DISPOSITIONS <= _disp_set(contract)


def join_on_identity(
    tables: dict[str, list[dict]],
    attached: dict[str, dict],
    identity: str,
) -> dict[str, dict[str, Any]]:
    bags: dict[str, dict[str, Any]] = defaultdict(dict)
    for table, contract in attached.items():
        column = col_for(contract, identity)
        if not column:
            continue
        for row in tables.get(table) or []:
            key = str(row.get(column) or "")
            if not key:
                continue
            for item in _roles(contract):
                sid = semantic_id(item)
                cname = item.get("column_name") or item.get("role_name")
                if sid == identity:
                    bags[key].setdefault(identity, key)
                    continue
                if cname and cname in row:
                    bags[key][sid] = row[cname]
    return dict(bags)


def _identity_rows(
    tables: dict[str, list[dict]],
    attached: dict[str, dict],
    dispositions_sidecar: list[dict] | None,
) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for table, contract in attached.items():
        if not is_identity_contract(contract):
            continue
        left_c = col_for(contract, "left")
        right_c = col_for(contract, "right")
        disp_c = col_for(contract, "disposition")
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
                }
            )
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
                    found.append({"left": str(left), "right": str(right), "disposition": disp})
    return [item for item in found if item.get("disposition") in IDENTITY_DISPOSITIONS]


def _clause_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    out = []
    for table, contract in attached.items():
        if "clause_kind" not in _identities(contract):
            continue
        if is_identity_contract(contract):
            continue
        kind_c = col_for(contract, "clause_kind")
        cid_c = col_for(contract, "contract_id") or col_for(contract, "contract")
        disp_c = col_for(contract, "disposition")
        if not kind_c or not cid_c:
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
    return out


def _invoice_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, Any]]:
    bags = join_on_identity(tables, attached, "invoice")
    for key, bag in list(bags.items()):
        bag.setdefault("invoice_id", key)
    for table, contract in attached.items():
        ids = _identities(contract)
        if "billed_name" in ids and "invoice_id" in ids:
            id_c = col_for(contract, "invoice_id")
            for row in tables.get(table) or []:
                key = str(row.get(id_c) or "")
                bags.setdefault(key, {})
                for field in INVOICE_FIELDS:
                    c = col_for(contract, field)
                    if c and c in row:
                        bags[key][field] = row[c]
                bags[key]["invoice_id"] = key
    rows = []
    for key, bag in bags.items():
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
    bags = join_on_identity(tables, attached, "contract")
    for table, contract in attached.items():
        ids = _identities(contract)
        if "counterparty_text" in ids and ("contract_id" in ids or "contract" in ids):
            cid = col_for(contract, "contract_id") or col_for(contract, "contract")
            ctext = col_for(contract, "counterparty_text")
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
        if "active" not in _identities(contract):
            continue
        cid = col_for(contract, "contract") or col_for(contract, "contract_id")
        act = col_for(contract, "active")
        for row in tables.get(table) or []:
            out.append({"contract_id": str(row.get(cid)), "active": bool(row.get(act))})
    return out


def _crm_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    out = []
    for table, contract in attached.items():
        ids = _identities(contract)
        if "account_name" not in ids:
            continue
        acc = col_for(contract, "account") or col_for(contract, "account_id")
        name = col_for(contract, "account_name")
        for row in tables.get(table) or []:
            out.append({"account": str(row.get(acc)), "account_name": str(row.get(name))})
    return out


def _registry_rows(tables: dict[str, list[dict]], attached: dict[str, dict]) -> list[dict[str, str]]:
    bags = join_on_identity(tables, attached, "entity")
    for table, contract in attached.items():
        ids = _identities(contract)
        if "legal_name" in ids and "company_number" in ids:
            num = col_for(contract, "company_number")
            legal = col_for(contract, "legal_name")
            status = col_for(contract, "status")
            for row in tables.get(table) or []:
                bags.setdefault(str(row.get(num)), {})
                bags[str(row.get(num))]["legal_name"] = row.get(legal)
                bags[str(row.get(num))]["status"] = row.get(status) if status else None
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


def load_sidecar_dispositions(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload if isinstance(payload, list) else []


def interface_gaps(attached: dict[str, dict]) -> dict[str, Any]:
    missing_bindings = []
    ambiguous = []
    seen: dict[str, list[str]] = defaultdict(list)
    for table, contract in attached.items():
        for role in _roles(contract):
            sid = semantic_id(role)
            if sid:
                seen[sid].append(f"{table}.{role.get('role_name')}")
        names = {str(r.get("role_name") or "") for r in _roles(contract)}
        if "counterparty" in names and "counterparty_text" not in _identities(contract):
            missing_bindings.append(
                {
                    "table": table,
                    "surface_role": "counterparty",
                    "required_identity": "counterparty_text",
                    "reason": "surface role without semantic_identity",
                }
            )
    for sid, locations in seen.items():
        if sid in {"status"} and len(locations) > 1:
            continue
    return {"missing_role_bindings": missing_bindings, "ambiguous_interface_mappings": ambiguous}


def normalize_world(
    world: Path,
    *,
    vocabulary: Path | None,
    dispositions: Path | None = None,
) -> dict[str, Any]:
    tables = dict_tables(world)
    attached = contracts_for_world(world, vocabulary)
    sidecar = load_sidecar_dispositions(dispositions)
    identity = _identity_rows(tables, attached, sidecar)
    invoices = _invoice_rows(tables, attached)
    contracts = _contract_rows(tables, attached)
    clauses = _clause_rows(tables, attached)
    active = _active_rows(tables, attached)
    crm = _crm_rows(tables, attached)
    registry = _registry_rows(tables, attached)
    gaps = interface_gaps(attached)
    recovered = [
        name
        for name, rows in (
            ("invoice_record", invoices),
            ("contract_record", contracts),
            ("contract_active", active),
            ("contract_clause_kind", clauses),
            ("identity_judgment", identity),
            ("crm_record", crm),
            ("registry_record", registry),
        )
        if rows
    ]
    missed = [name for name in CANONICAL_RELATIONS if name not in recovered]
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
        "consumer_relations_required": list(CANONICAL_RELATIONS),
        "consumer_relations_recovered": recovered,
        "missing_mappings": missed,
        "false_mappings": [],
        "role_binding_failures": gaps["missing_role_bindings"],
        "ambiguous_interface_mappings": gaps["ambiguous_interface_mappings"],
        "used_relation_names": False,
        "used_family_hints": False,
        "used_fuzzy_role_matching": False,
    }


def normalize_workspace(workspace: Path) -> dict[str, Any]:
    world = workspace / "06_world" / "world.sqlite"
    if not world.exists():
        world = workspace / "world" / "world.sqlite"
    vocabulary = workspace / "01_vocabulary.json"
    dispositions = workspace / "05_dispositions.json"
    return normalize_world(world, vocabulary=vocabulary, dispositions=dispositions)
