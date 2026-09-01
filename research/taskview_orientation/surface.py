"""Experiment-only TaskView surface with fixture-owned completeness contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from taskview import CompletenessStatus, TaskView, TaskViewAgentSurface, TaskViewError

from research.taskview_orientation.fixture import COMPLETENESS_CONTRACTS


PARTICIPANT_RERUN_RELATIONS = frozenset({"verification_gap"})


class ExperimentTaskViewSurface:
    """Frozen four-category surface; rerun accepts no completeness claims."""

    def __init__(self, view: TaskView) -> None:
        self.view = view
        self._surface = TaskViewAgentSurface(view)

    def describe(
        self,
        *,
        relation: str | None = None,
        why: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._surface.describe(relation=relation, why=why)

    def query_sql(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> dict[str, Any]:
        return self._surface.query_sql(sql, parameters)

    def assertion(
        self,
        *,
        action: str,
        relation: str,
        values: Mapping[str, Any],
        grounding: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        return self._surface.assertion(
            action=action,
            relation=relation,
            values=values,
            grounding=grounding,
        )

    def rerun(self, relation: str, **attempted_contract: Any) -> dict[str, Any]:
        if attempted_contract:
            names = ", ".join(sorted(attempted_contract))
            raise TaskViewError(
                f"completeness contract is fixture-owned; rejected arguments: {names}"
            )
        if relation not in PARTICIPANT_RERUN_RELATIONS:
            raise TaskViewError(f"no participant-visible frozen contract for {relation!r}")
        contract = COMPLETENESS_CONTRACTS[relation]
        if contract.status == CompletenessStatus.COMPLETE and not self.view.universe_is_sufficient(
            contract.universe
        ):
            raise TaskViewError(
                f"frozen COMPLETE contract rejected: universe {contract.universe!r} "
                "is not current and complete"
            )
        return self._surface.rerun(
            relation,
            universe=contract.universe,
            status=contract.status,
            basis=contract.basis,
            known_gaps=contract.known_gaps,
        )
