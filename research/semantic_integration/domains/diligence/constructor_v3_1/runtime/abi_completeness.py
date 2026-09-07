"""Required consumer ABI completeness. No fuzzy name matching."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.catalog import (
    load_vocabulary,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.consumer import (
    CONSUMER_FIELDS,
)

# Projector/purpose A/B/C/D required identities. Missing these is a compiler error, not a silent miss.
REQUIRED_IDENTITIES = frozenset(
    {
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
    }
)


def _identities_from_vocabulary(relations: list[dict[str, Any]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    for row in relations:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "")
        for role in row.get("roles") or []:
            if not isinstance(role, dict):
                continue
            sid = role.get("semantic_identity") or None
            if sid:
                found[str(sid)].append(f"{name}.{role.get('name')}")
    return dict(found)


def check_abi(vocabulary_path: Path) -> dict[str, Any]:
    relations = load_vocabulary(vocabulary_path)
    bindings = _identities_from_vocabulary(relations)
    fields = {}
    unsatisfied = []
    satisfied = []
    ambiguous = []
    duplicates = []
    for field in sorted(REQUIRED_IDENTITIES):
        locs = bindings.get(field) or []
        if not locs:
            status = "UNSATISFIED"
            unsatisfied.append(field)
        else:
            status = "SATISFIED"
            satisfied.append(field)
            if len(locs) > 1:
                duplicates.append({"field": field, "locations": locs})
        fields[field] = {"status": status, "locations": locs}
    extra = sorted(sid for sid in bindings if sid not in CONSUMER_FIELDS and sid not in REQUIRED_IDENTITIES)
    return {
        "required_semantic_fields": sorted(REQUIRED_IDENTITIES),
        "fields": fields,
        "satisfied": satisfied,
        "unsatisfied": unsatisfied,
        "ambiguous": ambiguous,
        "duplicate_bindings": duplicates,
        "false_bindings": [],
        "unrecognized_identities": extra,
        "ok": not unsatisfied and not ambiguous,
    }


def write_abi_report(workspace: Path) -> dict[str, Any]:
    payload = check_abi(workspace / "01_vocabulary.json")
    (workspace / "01_abi_completeness.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload
