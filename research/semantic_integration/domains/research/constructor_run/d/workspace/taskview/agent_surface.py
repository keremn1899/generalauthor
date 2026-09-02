"""The four-operation agent surface for TaskView v0.1.

This is intentionally a small Python adapter, not a new Graphauthor or MCP
product surface.  Relation and referent schema creation remain fixture/build
responsibilities for the first experiment.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from taskview.model import (
    Completeness,
    CompletenessStatus,
    Grounding,
    GroundingKind,
    TaskViewError,
)
from taskview.store import TaskView


AssertionAction = Literal["ASSERT", "RETRACT"]
TASKVIEW_SURFACE_VERSION = "0.1"


def _grounds(records: Sequence[Grounding | Mapping[str, Any]]) -> list[Grounding]:
    out: list[Grounding] = []
    for record in records:
        if isinstance(record, Grounding):
            out.append(record)
            continue
        try:
            out.append(
                Grounding(
                    kind=GroundingKind(str(record["kind"]).upper()),
                    reference=str(record["reference"]),
                    detail=str(record.get("detail") or ""),
                )
            )
        except (KeyError, ValueError) as exc:
            raise TaskViewError(
                "grounding requires kind, reference, and optional detail"
            ) from exc
    return out


class TaskViewAgentSurface:
    """Describe, query SQL, edit one assertion, or rerun one derivation.

    v0.1 keeps the logical operation categories fixed while making description
    payloads proportional to the requested scope.
    """

    def __init__(self, task_view: TaskView) -> None:
        self.task_view = task_view

    def describe(
        self,
        *,
        relation: str | None = None,
        why: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a catalog, one relation, or one tuple's grounding.

        The store retains its complete internal description for maintenance and
        fixture tooling.  This method is the consumption surface: its default
        response deliberately omits row counts, grounding, SQL, and full
        derivation/completeness receipts.
        """

        if relation is not None and why is not None:
            raise TaskViewError("describe accepts relation or why, not both")

        view = self._view_identity()
        if why is not None:
            relation_name = str(why.get("relation") or "")
            values = why.get("tuple")
            if not relation_name or not isinstance(values, Mapping):
                raise TaskViewError("describe why requires relation and tuple")
            return {
                "surface_version": TASKVIEW_SURFACE_VERSION,
                "task_view": view,
                "why": self.task_view.inspect_tuple(relation_name, values),
            }

        if relation is not None:
            return {
                "surface_version": TASKVIEW_SURFACE_VERSION,
                "task_view": view,
                "relation": self._relation_detail(relation),
            }

        description = self.task_view.describe()
        base: list[dict[str, Any]] = []
        derived: list[dict[str, Any]] = []
        completeness: list[dict[str, Any]] = []

        for relation in description["relations"]:
            compact = {
                "name": relation["name"],
                # Bare role names are REFERENT roles.  Non-default role types
                # use ``name:TYPE``; targeted relation description exposes the
                # full role/column records when that extra detail is needed.
                "roles": [
                    role["name"]
                    if role["type"] == "REFERENT"
                    else f"{role['name']}:{role['type']}"
                    for role in relation["roles"]
                ],
            }
            if relation["mode"] == "BASE":
                base.append(compact)
            else:
                state = self._state(relation["derivation"]["state"])
                if state != "CURRENT":
                    compact["state"] = state
                derived.append(compact)
            receipt = relation["completeness"]
            if receipt:
                summary = {
                    "target": relation["name"],
                    "universe": receipt["universe_relation"],
                    "status": receipt["status"],
                }
                state = self.task_view.completeness_state(relation["name"])
                if state != "CURRENT":
                    summary["state"] = state
                completeness.append(summary)

        out: dict[str, Any] = {
            "surface_version": TASKVIEW_SURFACE_VERSION,
            "task_view": view,
            "relations": {"BASE": base, "DERIVED": derived},
            "completeness": completeness,
        }
        return out

    def _view_identity(self) -> dict[str, Any]:
        description = self.task_view.describe()
        return description["view"]

    @staticmethod
    def _state(state: str) -> str:
        return "CURRENT" if state == "SUCCEEDED" else state

    def _relation_detail(self, relation: str) -> dict[str, Any]:
        schema = self.task_view.relation_schema(relation)
        detail: dict[str, Any] = {
            **schema,
            "roles": [
                {
                    "name": role["name"],
                    "type": role["type"],
                    "column": role["column"],
                }
                for role in schema["roles"]
            ],
            "state": (
                "CURRENT"
                if schema["mode"] == "BASE"
                else self._state(self.task_view.derivation_state(relation))
            ),
        }
        if schema["mode"] == "DERIVED":
            internal = self.task_view.describe()
            record = next(
                item for item in internal["relations"] if item["name"] == relation
            )
            detail["derivation"] = {
                "inputs": record["derivation"]["inputs"],
                "state": detail["state"],
            }
        receipt = self.task_view.latest_completeness(relation)
        if receipt:
            detail["completeness"] = {
                "target": relation,
                "universe": receipt["universe_relation"],
                "status": receipt["status"],
                "state": self.task_view.completeness_state(relation),
                "basis": receipt["basis"],
                "known_gaps": receipt["known_gaps"],
            }
        return detail

    def _normalize_assertion_values(
        self, relation: str, values: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Accept a role name or its exposed physical column alias once."""

        schema = self.task_view.relation_schema(relation)
        aliases = {
            alias: role["name"]
            for role in schema["roles"]
            for alias in (role["name"], role["column"])
        }
        normalized: dict[str, Any] = {}
        for key, value in values.items():
            role = aliases.get(str(key), str(key))
            if role in normalized and normalized[role] != value:
                raise TaskViewError(
                    f"assertion values provide conflicting aliases for role {role!r}"
                )
            normalized[role] = value
        return normalized

    def query_sql(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> dict[str, Any]:
        """Execute normal read-only SQLite over semantic relation tables only."""

        try:
            rows = self.task_view.query_semantic(sql, parameters)
        except TaskViewError as exc:
            raise TaskViewError(f"query_sql rejected: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            raise TaskViewError(f"query_sql rejected: {exc}") from exc
        return {"rows": rows, "row_count": len(rows)}

    def assertion(
        self,
        *,
        action: AssertionAction,
        relation: str,
        values: Mapping[str, Any],
        grounding: Sequence[Grounding | Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        """Assert or retract one BASE tuple using semantic role values."""

        normalized_action = str(action).upper()
        normalized_values = self._normalize_assertion_values(relation, values)
        if normalized_action == "ASSERT":
            result = self.task_view.assert_tuple(
                relation,
                normalized_values,
                grounding=_grounds(grounding),
            )
            return {
                "action": "ASSERT",
                "relation": relation,
                "tuple": normalized_values,
                "inserted": result.inserted,
                "grounding": self.task_view.groundings(
                    "ASSERTION", result.assertion_id
                ),
                "task_view_revision": self.task_view.revision,
                "stale_relations": self.task_view.stale_relations(),
            }
        if normalized_action == "RETRACT":
            if grounding:
                raise TaskViewError("RETRACT does not accept grounding")
            removed = self.task_view.retract_tuple(relation, normalized_values)
            return {
                "action": "RETRACT",
                "relation": relation,
                "tuple": normalized_values,
                "removed": removed,
                "task_view_revision": self.task_view.revision,
                "stale_relations": self.task_view.stale_relations(),
            }
        raise TaskViewError("assertion action must be ASSERT or RETRACT")

    def rerun(
        self,
        relation: str,
        *,
        universe: str,
        status: CompletenessStatus | str,
        basis: str,
        known_gaps: Sequence[str] = (),
    ) -> dict[str, Any]:
        """Explicitly rematerialize one registered SQL derivation."""

        try:
            completeness_status = CompletenessStatus(status)
        except ValueError as exc:
            raise TaskViewError(
                "completeness status must be COMPLETE, INCOMPLETE, or UNKNOWN"
            ) from exc
        result = self.task_view.run_derivation(
            relation,
            completeness=Completeness(
                completeness_status,
                universe=universe,
                basis=basis,
                known_gaps=tuple(str(gap) for gap in known_gaps),
            ),
        )
        receipt = self.task_view.latest_completeness(relation)
        return {
            "relation": relation,
            "row_count": result.row_count,
            "result_fingerprint": result.result_fingerprint,
            "task_view_revision": result.view_revision,
            "completeness": {
                "target": relation,
                "universe": receipt["universe_relation"],
                "status": receipt["status"],
                "state": self.task_view.completeness_state(relation),
                "basis": receipt["basis"],
                "known_gaps": receipt["known_gaps"],
                "input_versions": receipt["input_versions"],
            },
            "stale_relations": self.task_view.stale_relations(),
        }
