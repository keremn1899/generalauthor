"""Canonical logical-access ledger over the sealed v0.1 TASKVIEW trajectories."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import VIEW_ID, copy_frozen_task_view
from research.taskview_orientation.freeze import sha256_file
from research.taskview_orientation.read_surface_replay import (
    AUTHORIZED_MANIFEST_PATH,
    EXPECTED_SQL_FACTS,
    SEALED_CAMPAIGN_ID,
    SEALED_RESULTS_ROOT,
)
from research.taskview_orientation.read_surface_replay.sql_parse import (
    RestrictedQuery,
    classify_sql_corpus,
    parse_sql,
)
from research.taskview_orientation.runtime_accounting import (
    _content_texts,
    canonical_tool_arguments,
    observations_from_trajectory,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.v01_report import analyze
from taskview import TaskViewError


TASKVIEW_OPS = frozenset({"describe", "query_sql", "assertion", "rerun"})


class ReplayValidityError(RuntimeError):
    """The sealed corpus cannot support an exact reconstruction."""


@dataclass
class LogicalAccess:
    episode: str
    replicate: int
    phase: int
    sequence: int
    operation: str
    raw_arguments: dict[str, Any]
    normalized_arguments: dict[str, Any]
    relations_referenced: tuple[str, ...]
    schema_revision: str
    view_revision: int | None
    relation_revisions: dict[str, int]
    projection: str | None
    filters: tuple[Any, ...]
    order: tuple[Any, ...]
    limit: int | None
    sql: RestrictedQuery | None
    returned_rows: list[dict[str, Any]]
    canonical_tuples: list[tuple[Any, ...]]
    result_status: str
    derivation_state: dict[str, str]
    currentness: dict[str, str]
    completeness_status: dict[str, str | None]
    completeness_universe: dict[str, str | None]
    completeness_state: dict[str, str | None]
    grounding: Any
    assertion_since_previous: bool
    rerun_since_previous: bool
    historical_response_bytes: int
    historical_response_text: str
    reconstructed_rows: list[dict[str, Any]]
    reconstructed_payload: Any
    row_reconciliation: str
    is_error: bool
    describe_kind: str | None = None
    relevant_revision_token: str = ""
    all_relation_rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    relation_meanings: dict[str, dict[str, Any]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.sql is not None:
            payload["sql"] = asdict(self.sql)
        return payload


@dataclass
class EpisodeLedger:
    episode_id: str
    replicate: int
    arm: str
    seal_sha256: str
    accesses: list[LogicalAccess]
    historical_taskview_visible_bytes: int
    historical_taskview_post_bytes: int
    repository_o_post: int
    raw_o_post: int
    schema_revision: str
    declared_relations: list[str]
    reconstruction_ok: bool
    reconstruction_notes: list[str] = field(default_factory=list)


@dataclass
class CampaignLedger:
    campaign_id: str
    campaign_seal_sha256: str
    manifest_sha256: str
    sql_facts: dict[str, int]
    episodes: list[EpisodeLedger]
    budgets: dict[int, int]
    matched_pairs: list[dict[str, Any]]


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def describe_kind(arguments: dict[str, Any]) -> str:
    if arguments.get("why"):
        return "why"
    if arguments.get("relation"):
        return "relation"
    return "catalog"


def _schema_token(surface: ExperimentTaskViewSurface) -> tuple[str, list[dict[str, Any]], list[str]]:
    description = surface.view.describe()
    records = []
    for relation in description["relations"]:
        records.append(
            {
                "name": relation["name"],
                "mode": relation["mode"],
                "meaning": relation["description"],
                "roles": [
                    {
                        "role": role["name"],
                        "column": role["column"],
                        "type": role["type"],
                    }
                    for role in relation["roles"]
                ],
                "inputs": list((relation.get("derivation") or {}).get("inputs") or []),
            }
        )
    records.sort(key=lambda item: item["name"])
    encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return digest, records, [item["name"] for item in records]


def _role_map(surface: ExperimentTaskViewSurface, relation: str) -> list[dict[str, Any]]:
    return surface.view.relation_schema(relation)["roles"]


def canonical_tuples(
    surface: ExperimentTaskViewSurface, relation: str, rows: list[dict[str, Any]]
) -> list[tuple[Any, ...]]:
    roles = _role_map(surface, relation)
    out = []
    for row in rows:
        values = []
        for role in roles:
            if role["column"] in row:
                values.append(row[role["column"]])
            elif role["name"] in row:
                values.append(row[role["name"]])
            else:
                values.append(None)
        out.append(tuple(values))
    return out


def _relation_versions(surface: ExperimentTaskViewSurface) -> dict[str, int]:
    return {
        item["name"]: int(item["relation_version"])
        for item in surface.view.describe()["relations"]
    }


def _epistemic_for(
    surface: ExperimentTaskViewSurface, relations: tuple[str, ...]
) -> dict[str, Any]:
    derivation: dict[str, str] = {}
    currentness: dict[str, str] = {}
    completeness_status: dict[str, str | None] = {}
    completeness_universe: dict[str, str | None] = {}
    completeness_state: dict[str, str | None] = {}
    versions = _relation_versions(surface)
    relation_revisions: dict[str, int] = {}
    for name in relations:
        schema = surface.view.relation_schema(name)
        relation_revisions[name] = versions[name]
        if schema["mode"] == "DERIVED":
            state = surface.view.derivation_state(name)
            derivation[name] = (
                "CURRENT" if state == "SUCCEEDED" else state
            )
            currentness[name] = derivation[name]
            receipt = surface.view.latest_completeness(name)
            completeness_status[name] = None if receipt is None else receipt["status"]
            completeness_universe[name] = (
                None if receipt is None else receipt["universe_relation"]
            )
            completeness_state[name] = surface.view.completeness_state(name)
        else:
            derivation[name] = "BASE"
            currentness[name] = "CURRENT"
            completeness_status[name] = None
            completeness_universe[name] = None
            completeness_state[name] = None
    return {
        "derivation_state": derivation,
        "currentness": currentness,
        "completeness_status": completeness_status,
        "completeness_universe": completeness_universe,
        "completeness_state": completeness_state,
        "relation_revisions": relation_revisions,
        "view_revision": surface.view.revision,
    }


def relevant_revision_token(
    surface: ExperimentTaskViewSurface, relations: tuple[str, ...]
) -> str:
    epi = _epistemic_for(surface, relations)
    payload = {
        "view": epi["view_revision"],
        "relations": epi["relation_revisions"],
        "derivation": epi["derivation_state"],
        "completeness_status": epi["completeness_status"],
        "completeness_state": epi["completeness_state"],
        "universe": epi["completeness_universe"],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _historical_text(message: Any) -> str:
    texts = _content_texts(message.get("result") if isinstance(message, dict) else None)
    if not texts and isinstance(message, dict):
        result = message.get("result") or {}
        value = result.get("value") or {}
        content = value.get("content") or []
        texts = []
        for item in content:
            text = item.get("text") if isinstance(item, dict) else None
            if isinstance(text, str):
                texts.append(text)
            elif isinstance(text, dict) and isinstance(text.get("text"), str):
                texts.append(text["text"])
    return "".join(texts)


def _complete_by_call(trajectory: list[dict[str, Any]]) -> dict[str, Any]:
    complete: dict[str, Any] = {}
    for observation in observations_from_trajectory(trajectory):
        message = observation.message
        if str(message.get("status", "")) != "completed":
            continue
        call_id = str(message.get("call_id") or "")
        if call_id:
            complete[call_id] = message
    return complete


def _parse_json_object(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None
    return None


def _apply_mutation(surface: ExperimentTaskViewSurface, operation: str, arguments: dict[str, Any]) -> Any:
    if operation == "assertion":
        return surface.assertion(
            action=str(arguments.get("action") or ""),
            relation=str(arguments.get("relation") or ""),
            values=dict(arguments.get("values") or {}),
            grounding=tuple(arguments.get("grounding") or ()),
        )
    if operation == "rerun":
        return surface.rerun(str(arguments.get("relation") or ""))
    raise ReplayValidityError(f"not a mutation: {operation}")


def _execute_read(surface: ExperimentTaskViewSurface, operation: str, arguments: dict[str, Any]) -> Any:
    if operation == "describe":
        return surface.describe(
            relation=arguments.get("relation"),
            why=arguments.get("why"),
        )
    if operation == "query_sql":
        return surface.query_sql(
            str(arguments.get("sql") or ""),
            tuple(arguments.get("parameters") or ()),
        )
    raise ReplayValidityError(f"not a read: {operation}")


def _referenced_relations(
    surface: ExperimentTaskViewSurface,
    operation: str,
    arguments: dict[str, Any],
    parsed: RestrictedQuery | None,
) -> tuple[str, ...]:
    if operation == "query_sql" and parsed is not None and parsed.relation:
        return (parsed.relation,)
    if operation in {"assertion", "rerun"} and arguments.get("relation"):
        return (str(arguments["relation"]),)
    if operation == "describe":
        if arguments.get("relation"):
            return (str(arguments["relation"]),)
        if isinstance(arguments.get("why"), dict) and arguments["why"].get("relation"):
            return (str(arguments["why"]["relation"]),)
        return tuple(item["name"] for item in surface.view.describe()["relations"])
    return ()


def build_episode_ledger(
    episode_root: Path,
    *,
    raw_o_post: int,
    seal_sha256: str,
) -> EpisodeLedger:
    record = json.loads((episode_root / "record.json").read_text(encoding="utf-8"))
    events = _jsonl(episode_root / "telemetry.jsonl")
    trajectory = _jsonl(episode_root / "provider_trajectory.jsonl")
    complete_messages = _complete_by_call(trajectory)
    notes: list[str] = []
    reconstruction_ok = True

    with tempfile.TemporaryDirectory(prefix="tv-replay-") as tmp:
        view = copy_frozen_task_view(Path(tmp) / "taskview.sqlite")
        surface = ExperimentTaskViewSurface(view)
        schema_revision, _records, declared = _schema_token(surface)
        accesses: list[LogicalAccess] = []
        assertion_since = False
        rerun_since = False
        try:
            for event in events:
                if event.get("event_type") not in {"TASKVIEW_TOOL", "TOOL_ERROR"}:
                    continue
                operation = event.get("tool_name")
                if operation not in TASKVIEW_OPS:
                    continue
                arguments = dict(event.get("tool_arguments") or {})
                normalized = canonical_tool_arguments(operation, arguments)
                parsed = parse_sql(str(arguments.get("sql") or "")) if operation == "query_sql" else None
                is_error = event["event_type"] == "TOOL_ERROR"
                call_id = event.get("provider_call_id")
                historical_text = ""
                if call_id and call_id in complete_messages:
                    historical_text = _historical_text(complete_messages[call_id])
                historical_bytes = int(event.get("model_visible_output_bytes") or 0)
                if historical_text and len(historical_text.encode("utf-8")) != historical_bytes:
                    notes.append(
                        f"seq {event['sequence']}: historical text bytes "
                        f"{len(historical_text.encode('utf-8'))} != telemetry {historical_bytes}"
                    )
                    reconstruction_ok = False

                relations = _referenced_relations(surface, operation, arguments, parsed)
                epi = _epistemic_for(surface, relations) if relations else {
                    "derivation_state": {},
                    "currentness": {},
                    "completeness_status": {},
                    "completeness_universe": {},
                    "completeness_state": {},
                    "relation_revisions": {},
                    "view_revision": surface.view.revision,
                }
                token = (
                    relevant_revision_token(surface, relations) if relations else str(surface.view.revision)
                )

                reconstructed_payload: Any = None
                reconstructed_rows: list[dict[str, Any]] = []
                result_status = "error" if is_error else "ok"
                if not is_error and operation in {"describe", "query_sql"}:
                    try:
                        reconstructed_payload = _execute_read(surface, operation, arguments)
                    except TaskViewError as exc:
                        reconstruction_ok = False
                        notes.append(f"seq {event['sequence']}: read reconstruction raised {exc}")
                        reconstructed_payload = {"error": str(exc)}
                    if isinstance(reconstructed_payload, dict):
                        reconstructed_rows = list(reconstructed_payload.get("rows") or [])
                historical_obj = _parse_json_object(historical_text)
                returned_rows = reconstructed_rows
                row_reconciliation = "n/a"
                if operation == "query_sql" and not is_error:
                    historical_rows = []
                    if isinstance(historical_obj, dict):
                        historical_rows = list(historical_obj.get("rows") or [])
                    if historical_rows == reconstructed_rows:
                        row_reconciliation = "match"
                        returned_rows = reconstructed_rows
                    elif historical_rows and not reconstructed_rows:
                        row_reconciliation = "historical_only"
                        returned_rows = historical_rows
                        reconstruction_ok = False
                        notes.append(f"seq {event['sequence']}: reconstructed rows empty, using historical")
                    elif historical_rows != reconstructed_rows:
                        row_reconciliation = "mismatch"
                        reconstruction_ok = False
                        notes.append(
                            f"seq {event['sequence']}: row mismatch reconstructed={reconstructed_rows!r} "
                            f"historical={historical_rows!r}"
                        )
                        returned_rows = historical_rows or reconstructed_rows

                tuples: list[tuple[Any, ...]] = []
                if operation == "query_sql" and parsed and parsed.relation and returned_rows:
                    try:
                        tuples = canonical_tuples(surface, parsed.relation, returned_rows)
                    except Exception as exc:  # noqa: BLE001 — record limitation
                        notes.append(f"seq {event['sequence']}: canonical tuples failed: {exc}")

                all_rows: dict[str, list[dict[str, Any]]] = {}
                meanings: dict[str, dict[str, Any]] = {}
                for item in surface.view.describe()["relations"]:
                    name = item["name"]
                    columns = [role["column"] for role in item["roles"]]
                    order_sql = ", ".join(f'"{column}"' for column in columns)
                    all_rows[name] = surface.view.query_semantic(
                        f'SELECT {order_sql} FROM "{name}" ORDER BY {order_sql}'
                    )
                    meanings[name] = {
                        "name": name,
                        "mode": item["mode"],
                        "meaning": item["description"],
                        "roles": [
                            {
                                "role": role["name"],
                                "column": role["column"],
                                "type": role["type"],
                            }
                            for role in item["roles"]
                        ],
                        "inputs": list((item.get("derivation") or {}).get("inputs") or []),
                    }

                grounding = None
                if operation == "describe" and describe_kind(arguments) == "why":
                    grounding = (
                        reconstructed_payload.get("why")
                        if isinstance(reconstructed_payload, dict)
                        else historical_obj
                    )

                access = LogicalAccess(
                    episode=episode_root.name,
                    replicate=int(record["replicate"]),
                    phase=int(event["phase"]),
                    sequence=int(event["sequence"]),
                    operation=operation,
                    raw_arguments=arguments,
                    normalized_arguments=normalized,
                    relations_referenced=relations,
                    schema_revision=schema_revision,
                    view_revision=epi["view_revision"],
                    relation_revisions=epi["relation_revisions"],
                    projection=parsed.projection if parsed else None,
                    filters=parsed.filters if parsed else (),
                    order=parsed.order if parsed else (),
                    limit=parsed.limit if parsed else None,
                    sql=parsed,
                    returned_rows=returned_rows,
                    canonical_tuples=tuples,
                    result_status=result_status,
                    derivation_state=epi["derivation_state"],
                    currentness=epi["currentness"],
                    completeness_status=epi["completeness_status"],
                    completeness_universe=epi["completeness_universe"],
                    completeness_state=epi["completeness_state"],
                    grounding=grounding,
                    assertion_since_previous=assertion_since,
                    rerun_since_previous=rerun_since,
                    historical_response_bytes=historical_bytes,
                    historical_response_text=historical_text,
                    reconstructed_rows=reconstructed_rows,
                    reconstructed_payload=reconstructed_payload,
                    row_reconciliation=row_reconciliation,
                    is_error=is_error,
                    describe_kind=describe_kind(arguments) if operation == "describe" else None,
                    relevant_revision_token=token,
                    all_relation_rows=all_rows,
                    relation_meanings=meanings,
                )
                accesses.append(access)

                if not is_error and operation in {"assertion", "rerun"}:
                    try:
                        _apply_mutation(surface, operation, arguments)
                    except TaskViewError as exc:
                        reconstruction_ok = False
                        notes.append(f"seq {event['sequence']}: mutation reconstruction raised {exc}")
                    if operation == "assertion":
                        assertion_since = True
                        rerun_since = False
                    else:
                        rerun_since = True
                elif operation == "query_sql" and not is_error:
                    assertion_since = False
                    rerun_since = False
        finally:
            view.close()

    metrics = record["metrics"]
    return EpisodeLedger(
        episode_id=episode_root.name,
        replicate=int(record["replicate"]),
        arm=record["arm"],
        seal_sha256=seal_sha256,
        accesses=accesses,
        historical_taskview_visible_bytes=int(metrics["taskview_visible_bytes"]),
        historical_taskview_post_bytes=int(metrics["taskview_post_bytes"]),
        repository_o_post=int(metrics["O_post"]),
        raw_o_post=raw_o_post,
        schema_revision=schema_revision,
        declared_relations=declared,
        reconstruction_ok=reconstruction_ok,
        reconstruction_notes=notes,
    )


def _sql_facts(episodes: list[EpisodeLedger]) -> dict[str, int]:
    statements = [
        str(access.raw_arguments.get("sql") or "")
        for episode in episodes
        for access in episode.accesses
        if access.operation == "query_sql" and not access.is_error
    ]
    facts = classify_sql_corpus(statements)
    facts["query_sql_error_calls"] = sum(
        1
        for episode in episodes
        for access in episode.accesses
        if access.operation == "query_sql" and access.is_error
    )
    return facts


def build_campaign_ledger(results_root: Path | None = None) -> CampaignLedger:
    root = results_root or SEALED_RESULTS_ROOT
    seal = json.loads((root / "campaign_seal.json").read_text(encoding="utf-8"))
    if seal.get("campaign_id") != SEALED_CAMPAIGN_ID:
        raise ReplayValidityError(f"unexpected campaign id {seal.get('campaign_id')}")
    if seal.get("status") != "SEALED" or seal.get("valid") is not True:
        raise ReplayValidityError("campaign is not valid and sealed")
    report = analyze(root, AUTHORIZED_MANIFEST_PATH)
    raw_by_rep = {pair["replicate"]: pair["RAW_O_post"] for pair in report["matched_pairs"]}
    budgets = {
        pair["replicate"]: pair["RAW_O_post"] - pair["TASKVIEW_O_post"]
        for pair in report["matched_pairs"]
    }
    episodes: list[EpisodeLedger] = []
    for episode_id, episode_seal in sorted(seal["episode_seals"].items()):
        episode_root = root / episode_id
        record = json.loads((episode_root / "record.json").read_text(encoding="utf-8"))
        if record["arm"] != "TASKVIEW":
            continue
        episodes.append(
            build_episode_ledger(
                episode_root,
                raw_o_post=int(raw_by_rep[int(record["replicate"])]),
                seal_sha256=str(episode_seal),
            )
        )
    episodes.sort(key=lambda item: item.replicate)
    facts = _sql_facts(episodes)
    comparable = {key: facts[key] for key in EXPECTED_SQL_FACTS}
    if comparable != EXPECTED_SQL_FACTS:
        raise ReplayValidityError(
            f"SQL ledger facts mismatch: expected {EXPECTED_SQL_FACTS}, got {comparable}"
        )
    if len(episodes) != 4:
        raise ReplayValidityError(f"expected 4 TASKVIEW episodes, got {len(episodes)}")
    return CampaignLedger(
        campaign_id=SEALED_CAMPAIGN_ID,
        campaign_seal_sha256=sha256_file(root / "campaign_seal.json"),
        manifest_sha256=str(seal["manifest_sha256"]),
        sql_facts=facts,
        episodes=episodes,
        budgets=budgets,
        matched_pairs=list(report["matched_pairs"]),
    )
