"""World IR wrap over ``taskview.TaskView``. Never a fork of TaskView.

The calculus is CONSTITUTION.md. This module is the current kernel *mechanism*:
domain vocabularies live in fixture/config code; construction origin is
recorded beside TaskView, not as a TaskView schema change.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from taskview import Completeness, Grounding, GroundingKind, RelationMode, Role, TaskView

from research.semantic_integration.core.origins import ConstructionOrigin, OriginMetadataError
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation


def _origin_path(db_path: Path) -> Path:
    return Path(str(db_path) + ".origins.json")


class SemanticWorld:
    """One versioned semantic world stored in a TaskView SQLite file."""

    def __init__(self, path: Path | str, *, world_id: str) -> None:
        self.path = Path(path)
        self.world_id = world_id
        self._tv = TaskView(self.path, view_id=world_id, task_spec_ref="")
        self._origins: dict[str, str] = {}
        sidecar = _origin_path(self.path)
        if sidecar.exists():
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self._origins = dict(payload.get("assertions", {}))

    @property
    def taskview(self) -> TaskView:
        return self._tv

    def close(self) -> None:
        self._persist_origins()
        self._tv.close()

    @classmethod
    def wrap(cls, taskview: TaskView, *, world_id: str) -> "SemanticWorld":
        world = cls.__new__(cls)
        world.path = taskview.path
        world.world_id = world_id
        world._tv = taskview
        world._origins = {}
        sidecar = _origin_path(taskview.path)
        if sidecar.exists():
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            world._origins = dict(payload.get("assertions", {}))
        return world

    def _persist_origins(self) -> None:
        _origin_path(self.path).write_text(
            json.dumps(
                {"world_id": self.world_id, "assertions": self._origins},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def add_referent(
        self,
        referent_id: str,
        *,
        label: str = "",
        observations: Iterable[SourceObservation] = (),
    ) -> str:
        return self._tv.add_referent(
            referent_id,
            label=label,
            grounding=_observation_groundings(observations),
        )

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
    ) -> str:
        return self._tv.declare_relation(
            name, roles, mode=mode, description=description
        )

    def assert_tuple(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        origin: ConstructionOrigin,
        grounding: AssertionGrounding | None = None,
    ):
        if origin is ConstructionOrigin.DERIVED:
            raise ValueError("BASE assert cannot use DERIVED origin")
        grounds = list(_assertion_groundings(grounding, origin))
        result = self._tv.assert_tuple(relation, values, grounding=grounds)
        self._origins[result.assertion_id] = origin.value
        self._persist_origins()
        return result

    def retract_tuple(self, relation: str, values: Mapping[str, Any]) -> bool:
        assertion_id = self._tv.assertion_id_for_tuple(relation, values)
        removed = self._tv.retract_tuple(relation, values)
        if removed:
            self._origins.pop(assertion_id, None)
            self._persist_origins()
        return removed

    def register_derivation(
        self, relation: str, *, sql: str, inputs: Sequence[str]
    ) -> None:
        self._tv.register_derivation(relation, sql=sql, inputs=inputs)

    def rerun(self, relation: str, *, completeness: Completeness):
        result = self._tv.run_derivation(relation, completeness=completeness)
        for row in self._tv.query(
            "SELECT assertion_id FROM _tv_assertions WHERE relation_name = ?",
            (relation,),
        ):
            self._origins[row["assertion_id"]] = ConstructionOrigin.DERIVED.value
        self._persist_origins()
        return result

    def is_stale(self, relation: str) -> bool:
        return self._tv.is_stale(relation)

    def stale_relations(self) -> list[str]:
        return self._tv.stale_relations()

    def derivation_state(self, relation: str) -> str:
        return self._tv.derivation_state(relation)

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        return self._tv.latest_completeness(relation)

    def query(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return self._tv.query(sql, parameters)

    def query_semantic(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return self._tv.query_semantic(sql, parameters)

    def inspect_tuple(
        self, relation: str, values: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        detail = self._tv.inspect_tuple(relation, values)
        if detail is None:
            return None
        assertion_id = self._tv.assertion_id_for_tuple(relation, values)
        detail["construction_origin"] = self.origin_for_assertion(assertion_id)
        return detail

    def origin_for_assertion(self, assertion_id: str) -> str:
        if assertion_id in self._origins:
            return self._origins[assertion_id]
        rows = self._tv.query(
            "SELECT origin FROM _tv_assertions WHERE assertion_id = ?",
            (assertion_id,),
        )
        if not rows:
            raise OriginMetadataError(
                f"no assertion {assertion_id!r} has a construction origin"
            )
        if rows[0]["origin"] == "DERIVED":
            return ConstructionOrigin.DERIVED.value
        raise OriginMetadataError(
            f"asserted tuple {assertion_id!r} has no construction origin"
        )

    def origin_account(self) -> dict[str, int]:
        counts = {origin.value: 0 for origin in ConstructionOrigin}
        for row in self._tv.query(
            "SELECT assertion_id FROM _tv_assertions"
        ):
            origin = self.origin_for_assertion(row["assertion_id"])
            counts[origin] = counts.get(origin, 0) + 1
        return counts

    def relation_tuples(self, relation: str) -> set[tuple[Any, ...]]:
        roles = self._tv.relation_schema(relation)["roles"]
        columns = [role["column"] for role in roles]
        rows = self._tv.query(
            f"SELECT {', '.join(columns)} FROM {relation} ORDER BY {', '.join(columns)}"
        )
        return {tuple(row[column] for column in columns) for row in rows}


def _observation_groundings(
    observations: Iterable[SourceObservation],
) -> list[Grounding]:
    grounds = []
    for observation in observations:
        pointer = observation.as_pointer()
        grounds.append(
            Grounding(
                GroundingKind.SOURCE,
                f"{observation.provider}://{observation.native_handle}@{observation.source_revision}",
                json.dumps(pointer, sort_keys=True, separators=(",", ":")),
            )
        )
    return grounds


def _assertion_groundings(
    grounding: AssertionGrounding | None,
    origin: ConstructionOrigin,
) -> list[Grounding]:
    if grounding is None:
        return [
            Grounding(
                GroundingKind.WORLD,
                f"origin:{origin.value}",
                json.dumps(
                    {"construction_origin": origin.value},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
        ]
    grounds = _observation_groundings(grounding.observations)
    payload = {
        "construction_origin": origin.value,
        "construction_method": grounding.construction_method,
        "observations": [item.as_pointer() for item in grounding.observations],
    }
    if grounding.extra:
        payload["extra"] = grounding.extra
    grounds.append(
        Grounding(
            GroundingKind.WORLD,
            f"origin:{origin.value}",
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )
    )
    return grounds
