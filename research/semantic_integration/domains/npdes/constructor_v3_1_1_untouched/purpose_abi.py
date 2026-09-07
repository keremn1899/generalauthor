"""Purpose-driven ABI materializability using frozen v3.1.1 semantics.

SATISFIED(f) => f is declared AND mechanically present in World tables.
No diligence consumer field list. No EPA ontology. No fuzzy matching.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.catalog import (
    dict_tables,
    load_vocabulary,
)


def _required_from_intention(path: Path) -> list[str]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    purposes = payload.get("purposes") if isinstance(payload, dict) else {}
    found: list[str] = []
    for letter in ("A", "B", "C"):
        block = purposes.get(letter) or purposes.get(letter.lower()) or {}
        for key in ("required_semantic_distinctions", "required_output_shape"):
            value = block.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        found.append(item.strip())
                    elif isinstance(item, dict):
                        name = item.get("id") or item.get("name") or item.get("field")
                        if name:
                            found.append(str(name).strip())
    # Deduplicate while preserving order
    seen: set[str] = set()
    out = []
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _bindings(relations: list[dict[str, Any]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    for row in relations:
        name = str(row.get("name") or "")
        for role in row.get("roles") or []:
            if not isinstance(role, dict):
                continue
            sid = role.get("semantic_identity")
            rname = role.get("name") or role.get("role_name")
            if sid:
                found[str(sid)].append(f"{name}.{rname}")
    return dict(found)


def check_purpose_abi(workspace: Path) -> dict[str, Any]:
    vocab_path = workspace / "01_vocabulary.json"
    intention_path = workspace / "00_intention_contract.json"
    world = workspace / "06_world" / "world.sqlite"
    if not world.exists():
        world = workspace / "world" / "world.sqlite"
    relations = load_vocabulary(vocab_path)
    bindings = _bindings(relations)
    required = _required_from_intention(intention_path)
    # If P0 did not enumerate field ids, fall back to declared semantic_identity set.
    if not required:
        required = sorted(bindings)

    tables = dict_tables(world) if world.exists() else {}
    materialized: set[str] = set()
    for table, rows in tables.items():
        for row in rows:
            for key, value in row.items():
                if value is not None and str(value) != "":
                    materialized.add(str(key))
                    sid_matches = [
                        sid
                        for sid, locs in bindings.items()
                        if any(loc.endswith(f".{key}") or loc == f"{table}.{key}" for loc in locs)
                    ]
                    materialized.update(sid_matches)

    ambiguous_fields: set[str] = set()
    details = []
    for row in relations:
        counts: dict[str, list[str]] = defaultdict(list)
        name = str(row.get("name") or "")
        for role in row.get("roles") or []:
            if isinstance(role, dict) and role.get("semantic_identity"):
                counts[str(role["semantic_identity"])].append(str(role.get("name") or ""))
        for sid, names in counts.items():
            if len(names) > 1:
                ambiguous_fields.add(sid)
                details.append({"relation": name, "semantic_identity": sid, "roles": names})

    fields = {}
    satisfied = []
    unsatisfied = []
    ambiguous = []
    reasons = {}
    for field in required:
        locs = bindings.get(field) or []
        if field in ambiguous_fields:
            status, reason = "AMBIGUOUS", "AMBIGUOUS"
            ambiguous.append(field)
        elif not locs:
            status, reason = "UNSATISFIED", "NO_BINDING"
            unsatisfied.append(field)
        elif world.exists():
            # Binding exists; materializable if World has any rows in a bound table/column
            bound_tables = {loc.split(".", 1)[0] for loc in locs if "." in loc}
            has_rows = any(tables.get(t) for t in bound_tables) or field in materialized
            if has_rows:
                status, reason = "SATISFIED", None
                satisfied.append(field)
            else:
                status, reason = "UNSATISFIED", "NOT_MATERIALIZABLE"
                unsatisfied.append(field)
        else:
            status, reason = "UNSATISFIED", "NOT_MATERIALIZABLE"
            unsatisfied.append(field)
        reasons[field] = reason
        fields[field] = {"status": status, "reason": reason, "locations": locs}

    return {
        "required_semantic_fields": required,
        "fields": fields,
        "satisfied": satisfied,
        "unsatisfied": unsatisfied,
        "ambiguous": ambiguous,
        "unsatisfied_reasons": {k: v for k, v in reasons.items() if v},
        "ambiguity_details": details,
        "materialization_checked": world.exists(),
        "ok": not unsatisfied and not ambiguous,
    }
