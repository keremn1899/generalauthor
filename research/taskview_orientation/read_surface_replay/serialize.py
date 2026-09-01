"""Frozen serializers for the TaskView read-surface replay.

These rules are hashed before any candidate totals are computed.  Do not edit
this module to chase a preferred winner.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import sha256_file


SERIALIZER_ID = "taskview-read-surface-replay-serializers-v1"

# Frozen JSON wire format.  indent=2 matches the sealed v0.1 MCP delivery
# envelope (FastMCP pretty-print) so candidate A can reconcile with historical
# response bytes where the object graph overlaps.  Key order is insertion
# order of the constructed payload, never sort_keys.
JSON_INDENT = 2
JSON_ENSURE_ASCII = False
OMIT_NONE = True

CONTRACT_FIELD_ORDER = (
    "name",
    "roles",
    "columns",
    "types",
    "meaning",
    "mode",
    "inputs",
)

ROW_RESULT_KEYS = ("rows", "row_count")
SIMPLE_RESULT_KEYS = ("relation", "rows", "row_count")
STATUS_KEYS = ("status", "universe", "state")
NOT_MODIFIED_KEYS = (
    "relation",
    "relation_revision",
    "not_modified",
    "derivation",
    "coverage_state",
    "coverage",
)


def dumps(value: Any) -> str:
    """Serialize a JSON-compatible object with the frozen wire format."""

    return json.dumps(
        _omit(value),
        indent=JSON_INDENT,
        ensure_ascii=JSON_ENSURE_ASCII,
    )


def dump_bytes(value: Any) -> bytes:
    return dumps(value).encode("utf-8")


def byte_len(value: Any) -> int:
    return len(dump_bytes(value))


def _omit(value: Any) -> Any:
    if not OMIT_NONE:
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _omit(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_omit(item) for item in value]
    return value


def error_text(operation: str, message: str) -> str:
    """Frozen error payload, matching the sealed MCP tool-error prefix."""

    return f"Error executing tool {operation}: {message}"


def ordered(keys: Sequence[str], payload: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        if key in payload and payload[key] is not None:
            out[key] = payload[key]
    for key, value in payload.items():
        if key not in out and value is not None:
            out[key] = value
    return out


def row_result(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = [dict(row) for row in rows]
    return ordered(ROW_RESULT_KEYS, {"rows": materialized, "row_count": len(materialized)})


def simple_result(relation: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Identical row representation to SQL; relation name is the only extra key.

    Candidate C's economic comparison with B holds the row array and row_count
    bytes fixed by using :func:`row_result` for both.  This helper exists for
    request-language documentation and optional envelope diagnostics.
    """

    body = row_result(rows)
    return ordered(SIMPLE_RESULT_KEYS, {"relation": relation, **body})


def coverage_payload(
    *,
    status: str | None,
    universe: str | None,
    state: str | None,
) -> dict[str, Any] | None:
    if status is None and universe is None and state is None:
        return None
    return ordered(STATUS_KEYS, {"status": status, "universe": universe, "state": state})


def not_modified_payload(
    *,
    relation: str,
    relation_revision: int,
    derivation: str | None,
    coverage_state: str | None,
    coverage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return ordered(
        NOT_MODIFIED_KEYS,
        {
            "relation": relation,
            "relation_revision": relation_revision,
            "not_modified": True,
            "derivation": derivation,
            "coverage_state": coverage_state,
            "coverage": dict(coverage) if coverage else None,
        },
    )


def first_use_payload(
    *,
    relation: str,
    signature: str | None,
    meaning: str | None,
    revision: int | None,
    derivation: str | None,
    coverage: Mapping[str, Any] | None,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    payload = {
        "relation": relation,
        "signature": signature,
        "meaning": meaning,
        "revision": revision,
        "derivation": derivation,
        "coverage": dict(coverage) if coverage else None,
        "rows": [dict(row) for row in rows],
    }
    return ordered(
        (
            "relation",
            "signature",
            "meaning",
            "revision",
            "derivation",
            "coverage",
            "rows",
        ),
        payload,
    )


def bundle_payload(
    *,
    snapshot_revision: int,
    relations: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    ordered_relations = {
        name: ordered(
            ("coverage", "derivation", "relation_revision", "rows"),
            dict(body),
        )
        for name, body in sorted(relations.items())
    }
    return ordered(
        ("snapshot_revision", "relations"),
        {"snapshot_revision": snapshot_revision, "relations": ordered_relations},
    )


def stable_contract_text(contract: Mapping[str, Any]) -> str:
    """Minimal frozen vocabulary contract.  No dynamic rows."""

    lines = [
        f"task_view={contract['task_view']} schema={contract['schema']}",
    ]
    for relation in contract["relations"]:
        roles = ", ".join(
            f"{role['role']}->{role['column']}" for role in relation["roles"]
        )
        lines.append(f"{relation['name']}({roles})")
        lines.append(f"  {relation['meaning']}")
        marker = relation["mode"]
        inputs = relation.get("inputs") or []
        if marker == "DERIVED" and inputs:
            lines.append(f"  DERIVED inputs={','.join(inputs)}")
        else:
            lines.append(f"  {marker}")
    return "\n".join(lines) + "\n"


def tool_schema_payload(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    frozen = []
    for tool in tools:
        frozen.append(
            ordered(
                ("name", "description", "arguments"),
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "arguments": dict(tool["arguments"]),
                },
            )
        )
    return frozen


def split_component_bytes(total: str, components: Mapping[str, Any | None]) -> dict[str, int]:
    """Attribute subtree bytes without claiming they sum to the envelope.

    Residual wrapper bytes are charged to ``envelope`` so totals remain exact
    and overlapping savings are never treated as additive.
    """

    sizes = {
        name: byte_len(value)
        for name, value in components.items()
        if value not in (None, "", [], {})
    }
    charged = sum(sizes.values())
    residual = max(0, len(total.encode("utf-8")) - charged)
    if residual:
        sizes["envelope"] = residual
    return sizes


def serializer_hash() -> dict[str, str]:
    """Hash frozen serializer identity and this module's bytes."""

    config = {
        "serializer_id": SERIALIZER_ID,
        "json_indent": JSON_INDENT,
        "json_ensure_ascii": JSON_ENSURE_ASCII,
        "omit_none": OMIT_NONE,
        "sort_keys": False,
        "encoding": "utf-8",
        "error_prefix": "Error executing tool {operation}: {message}",
        "row_result_keys": list(ROW_RESULT_KEYS),
        "contract_field_order": list(CONTRACT_FIELD_ORDER),
        "not_modified_keys": list(NOT_MODIFIED_KEYS),
    }
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "serializer_id": SERIALIZER_ID,
        "config_sha256": hashlib.sha256(encoded).hexdigest(),
        "module_sha256": sha256_file(Path(__file__)),
    }
