"""Required consumer ABI completeness with materializability invariant.

V3.1.1 invariant:
  ABI SATISFIED => required consumer semantic field/relation is mechanically materializable from World.
  Formally: for required consumer field/relation f: SATISFIED(f) => f in Normalize(W).

No fuzzy name matching. No LLM. Single source of truth via normalizer.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.catalog import (
    load_vocabulary,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.consumer import (
    CANONICAL_RELATIONS,
    CONSUMER_FIELDS,
    IDENTITY_DISPOSITIONS,
    REQUIRED_IDENTITY_TO_RELATION,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.normalizer import (
    normalize_world,
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
        name = str(row.get("name") or row.get("physical_table") or "")
        roles = row.get("roles") or row.get("physical_roles") or []
        for role in roles:
            if not isinstance(role, dict):
                continue
            sid = role.get("semantic_identity") or None
            rname = role.get("name") or role.get("column_name") or role.get("role_name")
            if sid:
                found[str(sid)].append(f"{name}.{rname}")

        # If relation declares an identity disposition contract or fixed disposition
        disp_values = row.get("dispositions") or row.get("allowed_dispositions") or []
        disp_set = {str(v).upper() for v in disp_values}
        if IDENTITY_DISPOSITIONS <= disp_set or row.get("fixed_disposition"):
            found["disposition"].append(f"{name}.fixed_disposition")

    # Contract/invoice referent identities map to canonical IDs if canonical ID not explicitly bound
    if "invoice_id" not in found and "invoice" in found:
        found["invoice_id"] = list(found["invoice"])
    if "contract_id" not in found and "contract" in found:
        found["contract_id"] = list(found["contract"])

    return dict(found)


def check_abi(
    vocabulary_path: Path,
    world_path: Path | None = None,
    dispositions_path: Path | None = None,
    *,
    require_materializable: bool = True,
) -> dict[str, Any]:
    """Check ABI completeness including both BINDING and MATERIALIZABILITY.

    Status model:
      SATISFIED: Binding declared AND mechanically materializable from World.
      UNSATISFIED (reason: NO_BINDING): Required field has no binding.
      UNSATISFIED (reason: NOT_MATERIALIZABLE): Binding declared but World cannot produce it.
      AMBIGUOUS (reason: AMBIGUOUS): Multiple conflicting bindings without disambiguation.
    """
    relations = load_vocabulary(vocabulary_path)
    bindings = _identities_from_vocabulary(relations)

    # Auto-detect world and dispositions if not provided
    if world_path is None and vocabulary_path.exists():
        parent = vocabulary_path.parent
        for candidate in [
            parent / "06_world" / "world.sqlite",
            parent / "world" / "world.sqlite",
            parent / "02_mechanical_world" / "world.sqlite",
        ]:
            if candidate.exists():
                world_path = candidate
                break

    if dispositions_path is None and vocabulary_path.exists():
        candidate_disp = vocabulary_path.parent / "05_dispositions.json"
        if candidate_disp.exists():
            dispositions_path = candidate_disp

    # Ambiguity check: detect multiple roles in the same relation claiming the same semantic identity
    ambiguous_fields: set[str] = set()
    ambiguity_details: list[dict[str, Any]] = []
    for row in relations:
        if not isinstance(row, dict):
            continue
        rel_name = str(row.get("name") or "")
        counts: dict[str, list[str]] = defaultdict(list)
        for role in row.get("roles") or []:
            if isinstance(role, dict) and role.get("semantic_identity"):
                counts[str(role["semantic_identity"])].append(str(role.get("name") or ""))
        for sid, role_names in counts.items():
            if len(role_names) > 1:
                ambiguous_fields.add(sid)
                ambiguity_details.append(
                    {
                        "relation": rel_name,
                        "semantic_identity": sid,
                        "roles": role_names,
                        "reason": "multiple roles with same semantic_identity in relation",
                    }
                )

    # Materializability check via normalizer (single source of truth)
    norm = None
    recovered_relations: set[str] = set()
    materialized_tables: dict[str, list[dict]] = {}
    if require_materializable and world_path is not None and world_path.exists():
        norm = normalize_world(world_path, vocabulary=vocabulary_path, dispositions=dispositions_path)
        recovered_relations = set(norm.get("consumer_relations_recovered") or [])
        materialized_tables = norm.get("tables") or {}
        for amb in norm.get("ambiguous_interface_mappings") or []:
            if "semantic_identity" in amb:
                ambiguous_fields.add(amb["semantic_identity"])
                ambiguity_details.append(amb)

    fields: dict[str, Any] = {}
    unsatisfied: list[str] = []
    satisfied: list[str] = []
    ambiguous: list[str] = []
    duplicates: list[dict[str, Any]] = []
    reasons: dict[str, str] = {}

    for field in sorted(REQUIRED_IDENTITIES):
        locs = bindings.get(field) or []
        has_binding = bool(locs)
        is_ambiguous = (field in ambiguous_fields)

        if len(locs) > 1:
            duplicates.append({"field": field, "locations": locs})

        if is_ambiguous:
            status = "AMBIGUOUS"
            reason = "AMBIGUOUS"
            ambiguous.append(field)
            reasons[field] = reason
        elif not has_binding:
            status = "UNSATISFIED"
            reason = "NO_BINDING"
            unsatisfied.append(field)
            reasons[field] = reason
        elif require_materializable:
            # Must verify that field is materializable in Normalize(W)
            target_rel = REQUIRED_IDENTITY_TO_RELATION.get(field)
            if target_rel not in recovered_relations:
                is_materializable = False
            else:
                rows = materialized_tables.get(target_rel) or []
                is_materializable = any(row.get(field) is not None and row.get(field) != "" for row in rows)

            if is_materializable:
                status = "SATISFIED"
                reason = None
                satisfied.append(field)
            else:
                status = "UNSATISFIED"
                reason = "NOT_MATERIALIZABLE"
                unsatisfied.append(field)
                reasons[field] = reason
        else:
            # Binding-only check without materializability requirement
            status = "SATISFIED"
            reason = None
            satisfied.append(field)

        fields[field] = {
            "status": status,
            "reason": reason,
            "locations": locs,
        }

    # Relation-level materialization status
    relations_status: dict[str, Any] = {}
    for rel_name in CANONICAL_RELATIONS:
        if rel_name in recovered_relations:
            relations_status[rel_name] = {"status": "SATISFIED", "reason": None}
        elif any(bindings.get(f) for f, r in REQUIRED_IDENTITY_TO_RELATION.items() if r == rel_name):
            relations_status[rel_name] = {"status": "UNSATISFIED", "reason": "NOT_MATERIALIZABLE"}
        else:
            relations_status[rel_name] = {"status": "UNSATISFIED", "reason": "NO_BINDING"}

    extra = sorted(sid for sid in bindings if sid not in CONSUMER_FIELDS and sid not in REQUIRED_IDENTITIES)

    return {
        "required_semantic_fields": sorted(REQUIRED_IDENTITIES),
        "fields": fields,
        "relations": relations_status,
        "satisfied": satisfied,
        "unsatisfied": unsatisfied,
        "ambiguous": ambiguous,
        "duplicate_bindings": duplicates,
        "false_bindings": [],
        "unrecognized_identities": extra,
        "unsatisfied_reasons": reasons,
        "ambiguity_details": ambiguity_details,
        "materialization_checked": norm is not None,
        "recovered_relations": sorted(recovered_relations),
        "missing_relations": sorted(set(CANONICAL_RELATIONS) - recovered_relations) if norm else [],
        "ok": not unsatisfied and not ambiguous,
    }


def write_abi_report(workspace: Path) -> dict[str, Any]:
    payload = check_abi(workspace / "01_vocabulary.json")
    (workspace / "01_abi_completeness.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload
