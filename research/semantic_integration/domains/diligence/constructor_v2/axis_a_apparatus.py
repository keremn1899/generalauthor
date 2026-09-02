"""Frozen AXIS A apparatus: identity obligations + bounded packets. No gold dispositions in packets."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.runtime.contracts import (
    contract_to_dict,
    IDENTITY_CONTRACT,
)
from research.semantic_integration.domains.diligence.freeze_apparatus import HIDDEN, SOURCES

ROOT = Path(__file__).resolve().parent
APPARATUS = ROOT / "axis_a_apparatus"


def _notes() -> str:
    return (SOURCES / "commercial_notes.md").read_text(encoding="utf-8")


def _registry_rows() -> list[dict[str, str]]:
    with (SOURCES / "company_registry.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _crm_rows() -> list[dict[str, str]]:
    with (SOURCES / "crm.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _invoice_names() -> list[str]:
    rows = json.loads((SOURCES / "billing" / "invoices.json").read_text())
    return [row["billed_name"] for row in rows]


def _tokens(left: str, right: str) -> list[str]:
    toks = []
    for item in (left, right):
        if ":" in item:
            toks.append(item.split(":", 1)[1])
        toks.append(item)
    for row in _crm_rows():
        if any(tok in row.get("crm_account_id", "") or tok in row.get("account_name", "") for tok in toks):
            toks.append(row["account_name"])
    for row in _registry_rows():
        if any(tok in row["company_number"] or tok in row["legal_name"] for tok in toks):
            toks.append(row["legal_name"])
    seen: set[str] = set()
    unique: list[str] = []
    for tok in toks:
        if tok and tok not in seen:
            seen.add(tok)
            unique.append(tok)
    return unique


def _relevant_note_excerpts(left: str, right: str) -> list[str]:
    notes = _notes()
    tokens = [t.lower() for t in _tokens(left, right) if len(t) > 3]
    excerpts = []
    for para in notes.split("\n\n"):
        blob = para.lower()
        if any(tok.lower() in blob for tok in tokens):
            excerpts.append(para.strip())
    return excerpts


def packet_for(left: str, right: str) -> dict:
    observations = []
    for i, excerpt in enumerate(_relevant_note_excerpts(left, right)):
        observations.append(
            {
                "source_path": "sources/commercial_notes.md",
                "location": f"paragraph {i+1}",
                "excerpt": excerpt,
            }
        )
    tokens = _tokens(left, right)
    for row in _crm_rows():
        blob = " ".join(row.values())
        if any(tok in blob or tok in row.get("crm_account_id", "") for tok in tokens):
            observations.append(
                {
                    "source_path": "sources/crm.csv",
                    "location": f"row {row['crm_account_id']}",
                    "excerpt": ",".join(row.values()),
                }
            )
    for row in _registry_rows():
        if any(tok in row["company_number"] or tok in row["legal_name"] for tok in tokens):
            observations.append(
                {
                    "source_path": "sources/company_registry.csv",
                    "location": f"row {row['company_number']}",
                    "excerpt": ",".join(row.values()),
                }
            )
    names = _invoice_names()
    for name in names:
        if any(tok in name for tok in tokens if len(tok) > 4):
            observations.append(
                {
                    "source_path": "sources/billing/invoices.json",
                    "location": f"billed_name {name}",
                    "excerpt": name,
                }
            )
    for path in sorted((SOURCES / "contracts").glob("*.md")):
        stem = path.stem
        if f"contract:{stem}" in (left, right) or any(tok == stem for tok in tokens):
            text = path.read_text(encoding="utf-8")
            observations.append(
                {
                    "source_path": f"sources/contracts/{path.name}",
                    "location": "header",
                    "excerpt": "\n".join(text.splitlines()[:12]),
                }
            )
    return {
        "obligation_id": f"{left}|{right}",
        "left": left,
        "right": right,
        "selected_observations": observations,
        "selection_rationale": "Identity packet: notes plus rows/documents mentioning the candidate referents.",
        "known_missing_information": [],
    }


def oracle_pairs() -> list[tuple[str, str, str]]:
    payload = json.loads((HIDDEN / "annotations" / "identity_dispositions.json").read_text())
    out = []
    for kind, key in (
        ("SAME_ENTITY", "same_entity"),
        ("DISTINCT", "distinct"),
        ("UNRESOLVED", "unresolved"),
    ):
        for left, right in payload[key]:
            out.append((left, right, kind))
    return out


def write_apparatus() -> Path:
    dest = APPARATUS
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "packets").mkdir(exist_ok=True)
    (dest / "identity_contract.json").write_text(
        json.dumps(contract_to_dict(IDENTITY_CONTRACT), indent=2) + "\n"
    )
    obligations = []
    for i, (left, right, _kind) in enumerate(oracle_pairs(), start=1):
        oid = f"id-{i:02d}"
        packet = packet_for(left, right)
        packet["obligation_id"] = oid
        (dest / "packets" / f"{oid}.json").write_text(json.dumps(packet, indent=2) + "\n")
        obligations.append(
            {
                "obligation_id": oid,
                "relation": "identity_judgment",
                "values": {"left": left, "right": right},
                "why_demanded": "Required identity judgment for counterparty reconciliation.",
                "required_by": ["B"],
                "current_epistemic_state": "UNRESOLVED",
            }
        )
    (dest / "obligations.json").write_text(json.dumps(obligations, indent=2) + "\n")
    (dest / "README.md").write_text(
        "AXIS A frozen identity apparatus. Packets contain sources only. No gold dispositions.\n",
        encoding="utf-8",
    )
    return dest
