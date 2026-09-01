"""Condition-specific TaskView surface. Semantic tuples stay fixture-identical."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from research.taskview_orientation.bounded_reliance.grounding import annotate_groundings
from research.taskview_orientation.surface import ExperimentTaskViewSurface


class BoundedRelianceSurface:
    """Delegates every semantic op; optionally annotates grounding receipts."""

    def __init__(
        self,
        inner: ExperimentTaskViewSurface,
        *,
        condition: str,
        source_root: Path,
    ) -> None:
        self.inner = inner
        self.view = inner.view
        self.condition = condition
        self.source_root = Path(source_root)
        self.emit_freshness = condition in {"T01", "T11"}

    def describe(
        self,
        *,
        relation: str | None = None,
        why: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.inner.describe(relation=relation, why=why)
        if not self.emit_freshness:
            return payload
        if why is None or not isinstance(payload.get("why"), dict):
            return payload
        why_payload = dict(payload["why"])
        grounds = list(why_payload.get("grounding") or [])
        annotated, state = annotate_groundings(grounds, self.source_root)
        why_payload["grounding"] = annotated
        why_payload["grounding_state"] = state
        return {**payload, "why": why_payload}

    def query_sql(self, sql: str, parameters: Sequence[Any] = ()) -> dict[str, Any]:
        return self.inner.query_sql(sql, parameters)

    def assertion(
        self,
        *,
        action: str,
        relation: str,
        values: Mapping[str, Any],
        grounding: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        payload = self.inner.assertion(
            action=action,
            relation=relation,
            values=values,
            grounding=grounding,
        )
        if not self.emit_freshness or "grounding" not in payload:
            return payload
        annotated, state = annotate_groundings(
            list(payload.get("grounding") or []), self.source_root
        )
        return {**payload, "grounding": annotated, "grounding_state": state}

    def rerun(self, relation: str, **attempted_contract: Any) -> dict[str, Any]:
        return self.inner.rerun(relation, **attempted_contract)


def wrap_surface(
    inner: ExperimentTaskViewSurface,
    *,
    condition: str,
    source_root: Path,
) -> ExperimentTaskViewSurface | BoundedRelianceSurface:
    if condition in {"T00", "T10", "T01", "T11"}:
        return BoundedRelianceSurface(inner, condition=condition, source_root=source_root)
    return inner
