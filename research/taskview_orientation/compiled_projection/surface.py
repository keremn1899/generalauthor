"""ATOMIC vs COMPILED presentation wrapper. Canonical tuples stay fixture-identical."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from research.taskview_orientation.compiled_projection import MIGRATION_SURFACE_RELATION
from research.taskview_orientation.compiled_projection.projection import (
    atomic_payload,
    compiled_payload,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface


class CompiledProjectionSurface:
    def __init__(self, inner: ExperimentTaskViewSurface, *, condition: str) -> None:
        if condition not in {"ATOMIC", "COMPILED"}:
            raise ValueError(f"unknown condition {condition}")
        self.inner = inner
        self.view = inner.view
        self.condition = condition

    def _presentation(self) -> dict[str, Any]:
        if self.condition == "COMPILED":
            return compiled_payload(self.inner)
        return atomic_payload(self.inner)

    def describe(
        self,
        *,
        relation: str | None = None,
        why: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if why is None and relation == MIGRATION_SURFACE_RELATION:
            return self._presentation()
        return self.inner.describe(relation=relation, why=why)

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
        if self.condition != "COMPILED":
            return payload
        return {**payload, MIGRATION_SURFACE_RELATION: self._presentation()}

    def rerun(self, relation: str, **attempted_contract: Any) -> dict[str, Any]:
        payload = self.inner.rerun(relation, **attempted_contract)
        if self.condition != "COMPILED":
            return payload
        return {**payload, MIGRATION_SURFACE_RELATION: self._presentation()}


def wrap_surface(
    inner: ExperimentTaskViewSurface, *, condition: str
) -> ExperimentTaskViewSurface | CompiledProjectionSurface:
    if condition in {"ATOMIC", "COMPILED"}:
        return CompiledProjectionSurface(inner, condition=condition)
    return inner
