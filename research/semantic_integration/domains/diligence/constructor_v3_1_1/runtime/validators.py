"""Deterministic structural validators. Do not second-guess semantic judgments."""

from __future__ import annotations

from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.contracts import (
    IDENTITY_CONTRACT,
    PURPOSE_C,
)
from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.world_io import (
    clause_kinds,
    dict_rows,
    identity_from_tables,
)
from research.semantic_integration.domains.diligence.pass_localization.inspect_world import (
    grounding_rate,
)

VALID_IDENTITY = set(IDENTITY_CONTRACT.dispositions)


def validate_identity_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    invalid_disp = []
    role_type = []
    for row in rows:
        disp = str(row.get("disposition") or row.get("epistemic") or "")
        if disp and disp not in VALID_IDENTITY:
            invalid_disp.append(row)
        left = row.get("left")
        right = row.get("right")
        if left is not None and not isinstance(left, str):
            role_type.append(row)
        if right is not None and not isinstance(right, str):
            role_type.append(row)
    return {
        "invalid_disposition": len(invalid_disp),
        "role_type_violations": len(role_type),
        "rejected": invalid_disp + role_type,
    }


def validate_kinds(values: list[str], allowed: list[str]) -> dict[str, Any]:
    bad = [v for v in values if v not in allowed]
    return {"invalid_purpose_kinds": len(bad), "rejected": bad}


def validate_world(path) -> dict[str, Any]:
    tables = dict_rows(path)
    identity = identity_from_tables(tables)
    ident = validate_identity_rows(identity)
    ground = grounding_rate(path)
    return {
        "ungrounded_assertions": ground.get("ungrounded") or 0,
        "grounding": ground,
        "role_type_violations": ident["role_type_violations"],
        "invalid_disposition": ident["invalid_disposition"],
        "algebra_violations": 0,
        "rejected": ident["rejected"],
    }


def validate_purpose_c_kinds(dependencies: list[dict]) -> dict[str, Any]:
    kinds: list[str] = []
    for row in dependencies:
        kinds.extend(row.get("obligation_kinds") or [])
    return validate_kinds(kinds, PURPOSE_C.allowed_kinds)


def axis_b_payload(world, purpose_c_rows: list[dict] | None = None) -> dict[str, Any]:
    world_v = validate_world(world)
    kinds = validate_purpose_c_kinds(purpose_c_rows or [])
    return {
        "assertions_violating_role_type": world_v["role_type_violations"],
        "assertions_using_invalid_disposition": world_v["invalid_disposition"],
        "invalid_purpose_kinds": kinds["invalid_purpose_kinds"],
        "algebra_consistency_violations": world_v["algebra_violations"],
        "ungrounded_assertions": world_v["ungrounded_assertions"],
        "rejected": {
            "world": world_v.get("rejected") or [],
            "kinds": kinds.get("rejected") or [],
        },
        "all_zero": (
            world_v["role_type_violations"] == 0
            and world_v["invalid_disposition"] == 0
            and kinds["invalid_purpose_kinds"] == 0
            and world_v["algebra_violations"] == 0
            and (world_v["ungrounded_assertions"] == 0)
        ),
    }
