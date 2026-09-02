#!/usr/bin/env python3
"""Compile purpose A/B/C outputs from admitted world.sqlite and P5 dispositions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]

WORLD_CANDIDATES = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"

ACQUISITION_CLAUSE_KINDS = frozenset(
    {
        "change_of_control_consent",
        "change_of_control_termination",
        "assignment_consent",
        "assignment_notice",
        "assignment_affiliate_exception",
        "assignment_competitor_prohibition",
    }
)

CLAUSE_TO_OBLIGATION_KIND = {
    "exclusivity": "exclusivity",
    "auto_renewal_term": "auto_renewal",
    "rolling_term": "rolling_term",
}

OBLIGATION_CLAUSE_KINDS = frozenset(CLAUSE_TO_OBLIGATION_KIND)


def find_world_db() -> Path:
    for path in WORLD_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def load_dispositions() -> list[dict]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def disposition_identity_key(relation: str, values: dict) -> tuple:
    """Key on identifying roles only; outcome fields like disposition/present are excluded."""
    skip = {"disposition", "present"}
    if relation == "contract_clause_present":
        skip = {"present"}
    items = [(key, values[key]) for key in sorted(values) if key not in skip]
    return tuple(items)


def disposition_lookup(dispositions: list[dict]) -> dict[tuple[str, tuple], dict]:
    table: dict[tuple[str, tuple], dict] = {}
    for entry in dispositions:
        relation = entry["relation"]
        key = (relation, disposition_identity_key(relation, entry["values"]))
        table[key] = entry
    return table


def get_disposition(
    lookup: dict[tuple[str, tuple], dict],
    relation: str,
    values: dict,
) -> dict | None:
    return lookup.get((relation, disposition_identity_key(relation, values)))


def contract_stem(contract_id: str) -> str:
    return contract_id.split(":", 1)[1] if contract_id.startswith("contract:") else contract_id


def invoice_code(invoice_id: str) -> str:
    return invoice_id.split(":", 1)[1] if invoice_id.startswith("invoice:") else invoice_id


def build_invoice_billing_map(tv: TaskView) -> dict[str, str]:
    return {
        row["invoice_id"]: row["billed_name"]
        for row in tv.query("SELECT invoice_id, billed_name FROM invoice_record")
    }


def identity_judgment_pairs(dispositions: list[dict]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for entry in dispositions:
        if entry["relation"] != "entity_identity_judgment":
            continue
        left = entry["values"]["left"]
        right = entry["values"]["right"]
        pairs.append((left, right))
    return pairs


def seed_commercial_clusters(
    dispositions: list[dict],
    invoice_billing: dict[str, str],
) -> list[set[str]]:
    clusters: dict[str, set[str]] = {}
    for entry in dispositions:
        if entry["relation"] != "invoice_counterparty_association":
            continue
        invoice_id = entry["values"]["invoice"]
        contract_id = entry["values"]["contract"]
        billed_name = invoice_billing.get(invoice_id)
        if billed_name is None:
            continue
        key = billed_name
        cluster = clusters.setdefault(key, set())
        cluster.add(f"billing:{billed_name}")
        cluster.add(contract_id)

    judgment_pairs = identity_judgment_pairs(dispositions)
    for cluster in clusters.values():
        changed = True
        while changed:
            changed = False
            for left, right in judgment_pairs:
                if left in cluster and right not in cluster:
                    cluster.add(right)
                    changed = True
                elif right in cluster and left not in cluster:
                    cluster.add(left)
                    changed = True

    return list(clusters.values())


def derive_identity_link_candidates(clusters: list[set[str]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for cluster in clusters:
        endpoints = sorted(cluster)
        for index, left in enumerate(endpoints):
            for right in endpoints[index + 1:]:
                pair = (left, right)
                if pair not in seen:
                    seen.add(pair)
                    pairs.append(pair)
    pairs.sort()
    return pairs


def mechanical_invoice_contract_pairs(tv: TaskView) -> set[tuple[str, str]]:
    rows = tv.query(
        """
        SELECT i.invoice_id, c.contract_id
        FROM invoice_record i
        CROSS JOIN contract_header c
        WHERE i.billed_name = c.counterparty_name
           OR EXISTS (
             SELECT 1 FROM legal_form_name_variant v
             WHERE (v.form_a = i.billed_name AND v.form_b = c.counterparty_name)
                OR (v.form_b = i.billed_name AND v.form_a = c.counterparty_name)
           )
        """
    )
    return {(row["invoice_id"], row["contract_id"]) for row in rows}


def derive_invoice_contract_candidates(
    tv: TaskView,
    clusters: list[set[str]],
) -> list[tuple[str, str]]:
    candidates = mechanical_invoice_contract_pairs(tv)
    invoice_billing = build_invoice_billing_map(tv)
    cluster_by_endpoint: dict[str, set[str]] = {}
    for cluster in clusters:
        for endpoint in cluster:
            cluster_by_endpoint[endpoint] = cluster

    for invoice_id, billed_name in invoice_billing.items():
        billing_endpoint = f"billing:{billed_name}"
        cluster = cluster_by_endpoint.get(billing_endpoint)
        if cluster is None:
            continue
        for endpoint in cluster:
            if endpoint.startswith("contract:"):
                candidates.add((invoice_id, endpoint))

    return sorted(candidates)


def acquisition_relevant_contracts(tv: TaskView) -> set[str]:
    placeholders = ", ".join(f"'{kind}'" for kind in sorted(ACQUISITION_CLAUSE_KINDS))
    rows = tv.query(
        f"""
        SELECT DISTINCT contract_id
        FROM contract_clause_present
        WHERE present = 1 AND clause_kind IN ({placeholders})
        """
    )
    return {row["contract_id"] for row in rows}


def active_contracts(tv: TaskView) -> set[str]:
    rows = tv.query(
        "SELECT contract_id FROM contract_lifecycle_status WHERE status = 'active'"
    )
    return {row["contract_id"] for row in rows}


def compile_purpose_a(
    tv: TaskView,
    lookup: dict[tuple[str, tuple], dict],
    invoice_candidates: list[tuple[str, str]],
    active: set[str],
    acquisition_contracts: set[str],
) -> dict:
    qualifying_contracts = active & acquisition_contracts
    invoices_out: list[dict] = []
    invoice_rows = {
        row["invoice_id"]: row
        for row in tv.query(
            "SELECT invoice_id, billed_name, amount, currency, period, status "
            "FROM invoice_record"
        )
    }

    for invoice_id, contract_id in invoice_candidates:
        if contract_id not in qualifying_contracts:
            continue
        row = invoice_rows[invoice_id]
        disposition = get_disposition(
            lookup,
            "invoice_counterparty_association",
            {"invoice": invoice_id, "contract": contract_id},
        )
        if disposition is None:
            association = "unresolved"
        elif (
            disposition.get("disposition") == "ACCEPT"
            and disposition["values"].get("disposition") == "asserted"
        ):
            association = "asserted"
        else:
            association = "unresolved"

        invoices_out.append(
            {
                "invoice_id": invoice_code(invoice_id),
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": contract_stem(contract_id),
                "association": association,
            }
        )

    invoices_out.sort(key=lambda item: item["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices_out}


def epistemic_from_disposition(entry: dict | None) -> str:
    if entry is None:
        return "UNRESOLVED"
    top = entry.get("disposition")
    if top in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}:
        return top
    return "UNRESOLVED"


def compile_purpose_b(
    lookup: dict[tuple[str, tuple], dict],
    identity_candidates: list[tuple[str, str]],
) -> dict:
    links: list[dict] = []
    for left, right in identity_candidates:
        entry = get_disposition(
            lookup,
            "entity_identity_judgment",
            {"left": left, "right": right},
        )
        links.append(
            {
                "left": left,
                "right": right,
                "epistemic": epistemic_from_disposition(entry),
            }
        )
    return {"purpose": "counterparty_reconciliation", "links": links}


def obligation_kinds_for_contract(tv: TaskView, contract_id: str) -> list[str]:
    placeholders = ", ".join(f"'{kind}'" for kind in sorted(OBLIGATION_CLAUSE_KINDS))
    rows = tv.query(
        f"""
        SELECT clause_kind
        FROM contract_clause_present
        WHERE contract_id = ? AND present = 1 AND clause_kind IN ({placeholders})
        ORDER BY clause_kind
        """,
        (contract_id,),
    )
    kinds = sorted({CLAUSE_TO_OBLIGATION_KIND[row["clause_kind"]] for row in rows})
    return kinds


def open_invoices_for_billing_on_contract(
    tv: TaskView,
    billed_name: str,
    contract_id: str,
    lookup: dict[tuple[str, tuple], dict],
) -> list[str]:
    rows = tv.query(
        """
        SELECT i.invoice_id
        FROM invoice_record i
        INNER JOIN open_invoice o ON o.invoice_id = i.invoice_id
        WHERE i.billed_name = ?
        ORDER BY i.invoice_id
        """,
        (billed_name,),
    )
    open_ids: list[str] = []
    for row in rows:
        invoice_id = row["invoice_id"]
        association = get_disposition(
            lookup,
            "invoice_counterparty_association",
            {"invoice": invoice_id, "contract": contract_id},
        )
        if association is None:
            continue
        if (
            association.get("disposition") == "ACCEPT"
            and association["values"].get("disposition") == "asserted"
        ):
            open_ids.append(invoice_code(invoice_id))
    return open_ids


def derive_dependency_candidates(
    tv: TaskView,
    lookup: dict[tuple[str, tuple], dict],
    active: set[str],
) -> list[tuple[str, str]]:
    candidates: set[tuple[str, str]] = set()
    invoice_billing = build_invoice_billing_map(tv)
    open_rows = tv.query(
        """
        SELECT i.invoice_id, i.billed_name
        FROM invoice_record i
        INNER JOIN open_invoice o ON o.invoice_id = i.invoice_id
        """
    )

    for row in open_rows:
        invoice_id = row["invoice_id"]
        billed_name = row["billed_name"]
        association_entries = [
            entry
            for entry in lookup.values()
            if entry["relation"] == "invoice_counterparty_association"
            and entry["values"].get("invoice") == invoice_id
        ]
        for entry in association_entries:
            contract_id = entry["values"]["contract"]
            if contract_id not in active:
                continue
            kinds = obligation_kinds_for_contract(tv, contract_id)
            if not kinds:
                continue
            candidates.add((f"billing:{billed_name}", contract_id))

    return sorted(candidates)


def compile_purpose_c(
    tv: TaskView,
    lookup: dict[tuple[str, tuple], dict],
    dependency_candidates: list[tuple[str, str]],
) -> dict:
    dependencies: list[dict] = []
    for counterparty, contract_id in dependency_candidates:
        billed_name = counterparty.split(":", 1)[1]
        open_ids = open_invoices_for_billing_on_contract(
            tv, billed_name, contract_id, lookup
        )
        obligation_kinds = obligation_kinds_for_contract(tv, contract_id)
        disposition_entry = get_disposition(
            lookup,
            "commercial_dependency_assertion",
            {"counterparty": counterparty, "contract": contract_id},
        )
        if (
            disposition_entry
            and disposition_entry.get("disposition") == "ACCEPT"
            and disposition_entry["values"].get("disposition") == "dependent"
        ):
            status = "dependent"
        else:
            status = "unresolved"

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_stem(contract_id),
                "open_invoice_ids": open_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda item: item["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> int:
    world_path = find_world_db()
    dispositions = load_dispositions()
    lookup = disposition_lookup(dispositions)

    with TaskView(world_path, view_id="diligence-world") as tv:
        invoice_billing = build_invoice_billing_map(tv)
        clusters = seed_commercial_clusters(dispositions, invoice_billing)
        identity_candidates = derive_identity_link_candidates(clusters)
        invoice_candidates = derive_invoice_contract_candidates(tv, clusters)
        active = active_contracts(tv)
        acquisition_contracts = acquisition_relevant_contracts(tv)
        dependency_candidates = derive_dependency_candidates(tv, lookup, active)

        purpose_a = compile_purpose_a(
            tv, lookup, invoice_candidates, active, acquisition_contracts
        )
        purpose_b = compile_purpose_b(lookup, identity_candidates)
        purpose_c = compile_purpose_c(tv, lookup, dependency_candidates)

    write_json(ROOT / "purpose_ir" / "a" / "output.json", purpose_a)
    write_json(ROOT / "purpose_ir" / "b" / "output.json", purpose_b)
    write_json(ROOT / "purpose_ir" / "c" / "output.json", purpose_c)

    print(f"Read world from {world_path}")
    print(f"Wrote purpose_ir/a/output.json ({len(purpose_a['invoices'])} invoices)")
    print(f"Wrote purpose_ir/b/output.json ({len(purpose_b['links'])} links)")
    print(f"Wrote purpose_ir/c/output.json ({len(purpose_c['dependencies'])} dependencies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
