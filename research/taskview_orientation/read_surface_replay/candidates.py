"""Deterministic candidate-surface replay over a logical-access ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from research.taskview_orientation.read_surface_replay.ledger import (
    EpisodeLedger,
    LogicalAccess,
)
from research.taskview_orientation.read_surface_replay.serialize import (
    byte_len,
    bundle_payload,
    coverage_payload,
    dumps,
    error_text,
    first_use_payload,
    not_modified_payload,
    row_result,
    split_component_bytes,
    stable_contract_text,
    tool_schema_payload,
)


TOOL_SCHEMAS: dict[str, list[dict[str, Any]]] = {
    "A": [
        {
            "name": "describe",
            "description": "Describe frozen relations, derivations, currentness, and optionally one tuple's grounding.",
            "arguments": {"relation": "optional string", "why": "optional relation and tuple"},
        },
        {
            "name": "query_sql",
            "description": "Run read-only SQL over declared semantic relation tables.",
            "arguments": {"sql": "string", "parameters": "array"},
        },
        {
            "name": "assertion",
            "description": "Assert or retract one BASE semantic tuple.",
            "arguments": {"action": "ASSERT or RETRACT", "relation": "string", "values": "object", "grounding": "array"},
        },
        {
            "name": "rerun",
            "description": "Rerun a registered derivation under its fixture-owned completeness contract.",
            "arguments": {"relation": "string"},
        },
    ],
    "B": [
        {
            "name": "describe",
            "description": "Inspect one relation's currentness/completeness or one tuple's grounding. Stable vocabulary is in the schema-versioned contract.",
            "arguments": {"relation": "optional string", "why": "optional relation and tuple"},
        },
        {
            "name": "query_sql",
            "description": "Run read-only SQL over declared semantic relation tables.",
            "arguments": {"sql": "string", "parameters": "array"},
        },
        {
            "name": "assertion",
            "description": "Assert or retract one BASE semantic tuple.",
            "arguments": {"action": "ASSERT or RETRACT", "relation": "string", "values": "object", "grounding": "array"},
        },
        {
            "name": "rerun",
            "description": "Rerun a registered derivation under its fixture-owned completeness contract.",
            "arguments": {"relation": "string"},
        },
    ],
}
TOOL_SCHEMAS["C"] = [
    {
        "name": "get",
        "description": "Read one named relation, optionally filtered by a single role equality.",
        "arguments": {"relation": "string", "role": "optional role name", "value": "optional value"},
    },
    {
        "name": "select",
        "description": "Read one named relation with filters, order, and limit.",
        "arguments": {"relation": "string", "filters": "array", "order": "array", "limit": "integer or null"},
    },
    {
        "name": "query_sql",
        "description": "Escape hatch: read-only SQL over declared semantic relation tables.",
        "arguments": {"sql": "string", "parameters": "array"},
    },
] + TOOL_SCHEMAS["B"][0:1] + TOOL_SCHEMAS["B"][2:]
TOOL_SCHEMAS["D"] = [
    {
        "name": "query_sql",
        "description": "Run read-only SQL. Compact relation signature and meaning attach on first use at a schema version; dynamic epistemic fields attach on first use and relevant revision/invalidation.",
        "arguments": {"sql": "string", "parameters": "array"},
    },
] + TOOL_SCHEMAS["B"][0:1] + TOOL_SCHEMAS["B"][2:]
TOOL_SCHEMAS["E"] = [
    {
        "name": "snapshot",
        "description": "Return a participant-named bundle of current relation states.",
        "arguments": {"relations": "array of relation names"},
    },
] + TOOL_SCHEMAS["B"]
TOOL_SCHEMAS["E1"] = TOOL_SCHEMAS["E"]
TOOL_SCHEMAS["Eall"] = TOOL_SCHEMAS["E"]
TOOL_SCHEMAS["F"] = [
    {
        "name": "query_sql",
        "description": "Read-only SQL addressed by relation revision. Unchanged relevant state may return not_modified; invalidation never returns not_modified.",
        "arguments": {"sql": "string", "parameters": "array", "if_revision": "optional integer or token"},
    },
] + TOOL_SCHEMAS["A"][0:1] + TOOL_SCHEMAS["A"][2:]


CATEGORIES = (
    "stable_contract",
    "tool_schema",
    "semantic_context",
    "dynamic_row",
    "epistemic",
    "grounding",
    "maintenance",
    "error",
    "envelope",
)


@dataclass
class ChargedItem:
    candidate: str
    level: str
    replicate: int
    phase: int
    operation: str
    kind: str
    body: str
    categories: dict[str, int]
    omitted: bool = False
    not_modified: bool = False
    sql_escape: bool = False
    query_key: str = ""

    @property
    def total(self) -> int:
        return len(self.body.encode("utf-8")) if self.body else 0


def _empty_categories() -> dict[str, int]:
    return {name: 0 for name in CATEGORIES}


def _charge(body: str, mapping: dict[str, int]) -> dict[str, int]:
    out = _empty_categories()
    out.update(mapping)
    total = len(body.encode("utf-8"))
    accounted = sum(out.values())
    if accounted < total:
        out["envelope"] += total - accounted
    return out


def contract_for(episode: EpisodeLedger) -> dict[str, Any]:
    first = next(access for access in episode.accesses if access.relation_meanings)
    relations = []
    for name in sorted(first.relation_meanings):
        item = first.relation_meanings[name]
        relations.append(
            {
                "name": name,
                "roles": item["roles"],
                "meaning": item["meaning"],
                "mode": item["mode"],
                "inputs": item["inputs"],
            }
        )
    return {
        "task_view": "jsonlib-v3-orientation-experiment",
        "schema": episode.schema_revision,
        "relations": relations,
    }


def signature_for(meaning: dict[str, Any]) -> str:
    roles = ", ".join(f"{role['role']}->{role['column']}" for role in meaning["roles"])
    return f"{meaning['name']}({roles})"


def column_to_role(meaning: dict[str, Any], column: str) -> str:
    for role in meaning["roles"]:
        if role["column"] == column or role["role"] == column:
            return role["role"]
    return column


def _serialize_read_payload(access: LogicalAccess) -> str:
    if access.is_error:
        message = access.historical_response_text
        if message.startswith("Error executing tool "):
            return message
        return error_text(access.operation, message or "rejected")
    payload = access.reconstructed_payload
    if isinstance(payload, dict):
        return dumps(payload)
    if access.historical_response_text.startswith("{"):
        parsed = None
        try:
            import json

            parsed = json.loads(access.historical_response_text)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            return dumps(parsed)
    return access.historical_response_text


def _sql_rows(access: LogicalAccess) -> list[dict[str, Any]]:
    return [dict(row) for row in access.returned_rows]


def _coverage(access: LogicalAccess, relation: str) -> dict[str, Any] | None:
    return coverage_payload(
        status=access.completeness_status.get(relation),
        universe=access.completeness_universe.get(relation),
        state=access.completeness_state.get(relation),
    )


def _derivation(access: LogicalAccess, relation: str) -> str | None:
    return access.derivation_state.get(relation) or access.currentness.get(relation)


def _sql_key(access: LogicalAccess) -> str:
    if access.sql is None:
        return f"sql:{access.raw_arguments.get('sql')}"
    return access.sql.query_key()


def _dedup_key(access: LogicalAccess) -> str:
    if access.operation == "query_sql":
        return f"sql|{_sql_key(access)}|{access.relevant_revision_token}"
    if access.operation == "describe":
        return (
            f"describe|{access.describe_kind}|"
            f"{access.raw_arguments.get('relation')}|{access.raw_arguments.get('why')}|"
            f"{access.relevant_revision_token}"
        )
    return f"{access.operation}|{access.sequence}"


class ReplayState:
    def __init__(self) -> None:
        self.vocab_seen: set[str] = set()
        self.epistemic_seen: dict[str, str] = {}
        self.query_seen: dict[str, str] = {}
        self.delivered: set[str] = set()
        self.segment_buffer: list[LogicalAccess] = []
        self.sql_escape_count = 0


def _flush_bundle(
    *,
    candidate: str,
    level: str,
    episode: EpisodeLedger,
    state: ReplayState,
    extra: int | None,
    items: list[ChargedItem],
) -> None:
    buffer = [access for access in state.segment_buffer if access.operation == "query_sql" and not access.is_error]
    state.segment_buffer = []
    if not buffer:
        return
    head = buffer[-1]
    accessed = []
    for access in buffer:
        if access.sql and access.sql.relation and access.sql.relation not in accessed:
            accessed.append(access.sql.relation)
    names = list(accessed)
    declared = list(episode.declared_relations)
    if extra == 0:
        pass
    elif extra is None:
        names = list(declared)
    else:
        unused = [name for name in declared if name not in names]
        unused.sort(
            key=lambda name: (byte_len(row_result(head.all_relation_rows.get(name) or [])), name)
        )
        names.extend(unused[:extra])
    relations: dict[str, Any] = {}
    for name in names:
        body: dict[str, Any] = {
            "rows": head.all_relation_rows.get(name) or [],
            "relation_revision": head.relation_revisions.get(name),
        }
        coverage = _coverage(head, name)
        derivation = _derivation(head, name)
        if coverage:
            body["coverage"] = coverage
        if derivation and derivation != "BASE":
            body["derivation"] = derivation
        relations[name] = body
    payload = bundle_payload(snapshot_revision=int(head.view_revision or 0), relations=relations)
    body = dumps(payload)
    row_obj = {name: relations[name]["rows"] for name in relations}
    epi_obj = {
        name: {key: relations[name][key] for key in ("coverage", "derivation") if key in relations[name]}
        for name in relations
    }
    categories = _charge(
        body,
        split_component_bytes(
            body,
            {"dynamic_row": row_obj, "epistemic": epi_obj, "revision": payload["snapshot_revision"]},
        ),
    )
    if "dynamic_row" not in categories:
        categories["dynamic_row"] = 0
    items.append(
        ChargedItem(
            candidate=candidate,
            level=level,
            replicate=episode.replicate,
            phase=head.phase,
            operation="snapshot",
            kind="bundle",
            body=body,
            categories=categories,
            query_key=",".join(names),
        )
    )


def _should_skip_floor(state: ReplayState, access: LogicalAccess, *, allow_mutation: bool) -> bool:
    if access.operation in {"assertion", "rerun"}:
        return False
    key = _dedup_key(access)
    if key in state.delivered:
        return True
    state.delivered.add(key)
    return False


def replay_episode(
    episode: EpisodeLedger,
    candidate: str,
    level: str,
) -> list[ChargedItem]:
    items: list[ChargedItem] = []
    state = ReplayState()
    extra: int | None
    if candidate == "E":
        extra = 0
    elif candidate == "E1":
        extra = 1
    elif candidate == "Eall":
        extra = None
    else:
        extra = 0

    contract_body = stable_contract_text(contract_for(episode))
    tool_body = dumps(tool_schema_payload(TOOL_SCHEMAS[candidate]))
    if candidate in {"B", "C", "E", "E1", "Eall"} or (candidate == "D"):
        pass
    charge_contract = candidate in {"B", "C", "E", "E1", "Eall"}
    if charge_contract and level != "row_floor":
        items.append(
            ChargedItem(
                candidate=candidate,
                level=level,
                replicate=episode.replicate,
                phase=0,
                operation="contract",
                kind="stable_contract",
                body=contract_body,
                categories=_charge(contract_body, {"stable_contract": len(contract_body.encode("utf-8"))}),
            )
        )
    if level != "row_floor":
        items.append(
            ChargedItem(
                candidate=candidate,
                level=level,
                replicate=episode.replicate,
                phase=0,
                operation="tool_schema",
                kind="tool_schema",
                body=tool_body,
                categories=_charge(tool_body, {"tool_schema": len(tool_body.encode("utf-8"))}),
            )
        )

    if level == "row_floor":
        return items + _row_floor(episode, candidate)

    for access in episode.accesses:
        if candidate in {"E", "E1", "Eall"} and access.operation in {"query_sql", "assertion", "rerun"}:
            if access.operation == "query_sql" and not access.is_error:
                if level == "mechanical_dedup_floor" and _should_skip_floor(state, access, allow_mutation=True):
                    continue
                state.segment_buffer.append(access)
                continue
            _flush_bundle(
                candidate=candidate,
                level=level,
                episode=episode,
                state=state,
                extra=extra,
                items=items,
            )
            if access.operation in {"assertion", "rerun"}:
                items.append(_maintenance_item(episode, candidate, level, access))
                continue

        if level == "mechanical_dedup_floor" and _should_skip_floor(state, access, allow_mutation=True):
            continue

        if access.operation == "describe" and access.describe_kind == "catalog":
            if candidate in {"B", "C", "D", "E", "E1", "Eall"}:
                continue
            items.append(_a_read_item(episode, candidate, level, access, kind="describe_catalog"))
            continue
        if access.operation == "describe":
            items.append(_a_read_item(episode, candidate, level, access, kind=f"describe_{access.describe_kind}"))
            continue
        if access.operation in {"assertion", "rerun"}:
            items.append(_maintenance_item(episode, candidate, level, access))
            continue
        if access.operation == "query_sql":
            items.append(_query_item(episode, candidate, level, access, state))
            continue
    if candidate in {"E", "E1", "Eall"}:
        _flush_bundle(
            candidate=candidate,
            level=level,
            episode=episode,
            state=state,
            extra=extra,
            items=items,
        )
    return items


def _a_read_item(
    episode: EpisodeLedger,
    candidate: str,
    level: str,
    access: LogicalAccess,
    *,
    kind: str,
) -> ChargedItem:
    body = _serialize_read_payload(access)
    if access.is_error:
        categories = _charge(body, {"error": len(body.encode("utf-8"))})
    elif access.describe_kind == "why":
        categories = _charge(body, {"grounding": len(body.encode("utf-8"))})
    elif access.describe_kind == "catalog":
        categories = _charge(body, {"semantic_context": len(body.encode("utf-8"))})
    else:
        # Relation describe mixes vocabulary and epistemic planes.
        meaning = None
        epi = None
        if isinstance(access.reconstructed_payload, dict):
            relation = access.reconstructed_payload.get("relation") or {}
            meaning = {
                "name": relation.get("name"),
                "roles": relation.get("roles"),
                "description": relation.get("description"),
                "mode": relation.get("mode"),
            }
            epi = {
                "state": relation.get("state"),
                "completeness": relation.get("completeness"),
                "derivation": relation.get("derivation"),
            }
        categories = _charge(body, split_component_bytes(body, {"semantic_context": meaning, "epistemic": epi}))
    return ChargedItem(
        candidate=candidate,
        level=level,
        replicate=episode.replicate,
        phase=access.phase,
        operation=access.operation,
        kind=kind,
        body=body,
        categories=categories,
        query_key=_dedup_key(access),
    )


def _maintenance_item(
    episode: EpisodeLedger, candidate: str, level: str, access: LogicalAccess
) -> ChargedItem:
    body = _serialize_read_payload(access)
    bucket = "error" if access.is_error else "maintenance"
    return ChargedItem(
        candidate=candidate,
        level=level,
        replicate=episode.replicate,
        phase=access.phase,
        operation=access.operation,
        kind=access.operation,
        body=body,
        categories=_charge(body, {bucket: len(body.encode("utf-8"))}),
    )


def _query_item(
    episode: EpisodeLedger,
    candidate: str,
    level: str,
    access: LogicalAccess,
    state: ReplayState,
) -> ChargedItem:
    rows = _sql_rows(access)
    relation = access.sql.relation if access.sql else "unknown"
    sql_escape = bool(access.sql and access.sql.sql_escape_required)
    if sql_escape:
        state.sql_escape_count += 1
    if access.is_error:
        body = _serialize_read_payload(access)
        return ChargedItem(
            candidate=candidate,
            level=level,
            replicate=episode.replicate,
            phase=access.phase,
            operation="query_sql",
            kind="error",
            body=body,
            categories=_charge(body, {"error": len(body.encode("utf-8"))}),
            sql_escape=sql_escape,
            query_key=_sql_key(access),
        )

    result = row_result(rows)
    if candidate in {"A", "B", "C"}:
        body = dumps(result)
        categories = _charge(body, {"dynamic_row": byte_len({"rows": rows})})
        return ChargedItem(
            candidate=candidate,
            level=level,
            replicate=episode.replicate,
            phase=access.phase,
            operation="select" if candidate == "C" else "query_sql",
            kind="rows",
            body=body,
            categories=categories,
            sql_escape=sql_escape and candidate == "C",
            query_key=_sql_key(access),
        )

    if candidate == "D":
        meaning = (access.relation_meanings or {}).get(relation or "", {})
        vocab_key = f"{access.schema_revision}:{relation}"
        attach_vocab = vocab_key not in state.vocab_seen
        if attach_vocab:
            state.vocab_seen.add(vocab_key)
        last = state.epistemic_seen.get(relation or "")
        attach_epi = last != access.relevant_revision_token
        if attach_epi:
            state.epistemic_seen[relation or ""] = access.relevant_revision_token
        payload = first_use_payload(
            relation=relation or "",
            signature=signature_for(meaning) if attach_vocab and meaning else None,
            meaning=meaning.get("meaning") if attach_vocab else None,
            revision=access.relation_revisions.get(relation) if attach_epi else None,
            derivation=_derivation(access, relation or "") if attach_epi else None,
            coverage=_coverage(access, relation or "") if attach_epi else None,
            rows=rows,
        )
        body = dumps(payload)
        categories = _charge(
            body,
            split_component_bytes(
                body,
                {
                    "semantic_context": {
                        "signature": payload.get("signature"),
                        "meaning": payload.get("meaning"),
                    }
                    if attach_vocab
                    else None,
                    "epistemic": {
                        "revision": payload.get("revision"),
                        "derivation": payload.get("derivation"),
                        "coverage": payload.get("coverage"),
                    }
                    if attach_epi
                    else None,
                    "dynamic_row": {"rows": rows},
                },
            ),
        )
        return ChargedItem(
            candidate=candidate,
            level=level,
            replicate=episode.replicate,
            phase=access.phase,
            operation="query_sql",
            kind="first_use" if attach_vocab or attach_epi else "rows",
            body=body,
            categories=categories,
            query_key=_sql_key(access),
        )

    # Candidate F
    query_key = _sql_key(access)
    previous = state.query_seen.get(query_key)
    if previous == access.relevant_revision_token:
        payload = not_modified_payload(
            relation=relation or "",
            relation_revision=int(access.relation_revisions.get(relation) or 0),
            derivation=_derivation(access, relation or ""),
            coverage_state=access.completeness_state.get(relation or ""),
            coverage=_coverage(access, relation or ""),
        )
        body = dumps(payload)
        return ChargedItem(
            candidate=candidate,
            level=level,
            replicate=episode.replicate,
            phase=access.phase,
            operation="query_sql",
            kind="not_modified",
            body=body,
            categories=_charge(body, {"epistemic": len(body.encode("utf-8"))}),
            not_modified=True,
            query_key=query_key,
        )
    state.query_seen[query_key] = access.relevant_revision_token
    payload = {
        "relation": relation,
        "relation_revision": access.relation_revisions.get(relation),
        "derivation": _derivation(access, relation or ""),
        "coverage": _coverage(access, relation or ""),
        "rows": rows,
        "row_count": len(rows),
    }
    body = dumps(payload)
    categories = _charge(
        body,
        split_component_bytes(
            body,
            {
                "dynamic_row": {"rows": rows, "row_count": len(rows)},
                "epistemic": {
                    "relation_revision": payload["relation_revision"],
                    "derivation": payload["derivation"],
                    "coverage": payload["coverage"],
                },
            },
        ),
    )
    return ChargedItem(
        candidate=candidate,
        level=level,
        replicate=episode.replicate,
        phase=access.phase,
        operation="query_sql",
        kind="rows",
        body=body,
        categories=categories,
        query_key=query_key,
    )


def _row_floor(episode: EpisodeLedger, candidate: str) -> list[ChargedItem]:
    unique_rows: dict[tuple[Any, ...], dict[str, Any]] = {}
    epi_by_rel: dict[str, dict[str, Any]] = {}
    for access in episode.accesses:
        if access.operation != "query_sql" or access.is_error:
            continue
        relation = access.sql.relation if access.sql else None
        if not relation:
            continue
        revision = access.relation_revisions.get(relation)
        for row, tup in zip(access.returned_rows, access.canonical_tuples or [() for _ in access.returned_rows]):
            unique_rows[(relation, revision, tup)] = dict(row)
        epi_by_rel[(relation, access.relevant_revision_token)] = {
            "derivation": _derivation(access, relation),
            "coverage": _coverage(access, relation),
            "relation_revision": revision,
        }
    relations: dict[str, Any] = {}
    for (relation, revision, _tup), row in unique_rows.items():
        bucket = relations.setdefault(relation, {"rows": [], "relation_revision": revision})
        bucket["rows"].append(row)
    for (relation, _token), epi in epi_by_rel.items():
        relations.setdefault(relation, {"rows": []}).update(
            {key: value for key, value in epi.items() if value is not None}
        )
    payload = bundle_payload(snapshot_revision=0, relations=relations)
    text = dumps(payload)
    row_map = {name: item.get("rows") for name, item in relations.items()}
    epi_map = {
        name: {key: value for key, value in item.items() if key != "rows"}
        for name, item in relations.items()
    }
    return [
        ChargedItem(
            candidate=candidate,
            level="row_floor",
            replicate=episode.replicate,
            phase=0,
            operation="row_floor",
            kind="row_floor",
            body=text,
            categories=_charge(
                text,
                split_component_bytes(
                    text,
                    {"dynamic_row": row_map, "epistemic": epi_map},
                ),
            ),
        )
    ]


def replay_campaign(episodes: Iterable[EpisodeLedger], candidate: str, level: str) -> list[ChargedItem]:
    items: list[ChargedItem] = []
    for episode in episodes:
        items.extend(replay_episode(episode, candidate, level))
    return items
