"""Fail-closed construction wrap over SemanticWorld. Does not change TaskView.

WORLD BASE requires SOURCE grounding; PURPOSE-scoped rows may omit it.
Admission scope is a sidecar mechanism for the WORLD vs PURPOSE invariant.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from taskview import Completeness, RelationMode, Role, RoleType

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation

Scope = Literal["WORLD", "PURPOSE"]


class GroundingError(ValueError):
    """WORLD BASE was asserted without SOURCE grounding."""


class ConstructionError(ValueError):
    """construction.py is malformed or did not produce a World."""


def view_id_of(db_path: Path | str) -> str:
    connection = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ConstructionError(f"{db_path} is not a TaskView world")
    return str(row[0])


def has_source_grounding(grounding: AssertionGrounding | None) -> bool:
    if grounding is None:
        return False
    for observation in grounding.observations:
        if not isinstance(observation, SourceObservation):
            continue
        if str(observation.native_handle or "").strip() and str(
            observation.source_revision or ""
        ).strip():
            return True
    return False


class ConstructionWorld:
    """SemanticWorld plus relation scope and WORLD-BASE SOURCE enforcement."""

    def __init__(self, inner: SemanticWorld) -> None:
        self._inner = inner
        self.admission: dict[str, Scope] = {}

    @classmethod
    def create(cls, path: Path | str, *, world_id: str) -> "ConstructionWorld":
        return cls(SemanticWorld(path, world_id=world_id))

    @classmethod
    def open(cls, path: Path | str, *, world_id: str | None = None) -> "ConstructionWorld":
        db_path = Path(path)
        inner = SemanticWorld(db_path, world_id=world_id or view_id_of(db_path))
        world = cls(inner)
        admission_path = db_path.parent / "world.admission.json"
        if admission_path.exists():
            world.load_admission(admission_path)
        return world

    @property
    def path(self) -> Path:
        return self._inner.path

    @property
    def world_id(self) -> str:
        return self._inner.world_id

    @property
    def taskview(self):
        return self._inner.taskview

    def close(self) -> None:
        self._inner.close()

    def add_referent(
        self,
        referent_id: str,
        *,
        label: str = "",
        observations: Iterable[SourceObservation] = (),
    ) -> str:
        return self._inner.add_referent(
            referent_id, label=label, observations=observations
        )

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
        scope: Scope = "WORLD",
    ) -> str:
        if scope not in ("WORLD", "PURPOSE"):
            raise ConstructionError(f"scope must be WORLD or PURPOSE, got {scope!r}")
        declared = self._inner.declare_relation(
            name, roles, mode=mode, description=description
        )
        self.admission[declared] = scope
        return declared

    def assert_tuple(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        origin: ConstructionOrigin,
        grounding: AssertionGrounding | None = None,
    ):
        scope = self._scope(relation)
        mode = self._inner.taskview.relation_schema(relation)["mode"]
        if mode == RelationMode.DERIVED.value:
            raise ConstructionError(
                f"derived relation {relation!r} cannot be asserted; use register_derivation"
            )
        if scope == "WORLD" and not has_source_grounding(grounding):
            raise GroundingError(
                f"WORLD BASE {relation!r} requires SOURCE grounding with a non-empty reference"
            )
        return self._inner.assert_tuple(
            relation, values, origin=origin, grounding=grounding
        )

    def retract_tuple(self, relation: str, values: Mapping[str, Any]) -> bool:
        return self._inner.retract_tuple(relation, values)

    def register_derivation(
        self, relation: str, *, sql: str, inputs: Sequence[str]
    ) -> None:
        self._inner.register_derivation(relation, sql=sql, inputs=inputs)

    def rerun(self, relation: str, *, completeness: Completeness):
        return self._inner.rerun(relation, completeness=completeness)

    def query_semantic(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return self._inner.query_semantic(sql, parameters)

    def relation_schema(self, relation: str) -> dict[str, Any]:
        return self._inner.taskview.relation_schema(relation)

    def relation_rows(self, relation: str) -> list[dict[str, Any]]:
        schema = self.relation_schema(relation)
        column_to_role = {role["column"]: role["name"] for role in schema["roles"]}
        physical = self.query_semantic(f'SELECT * FROM "{relation}"')
        rows = []
        for row in physical:
            rows.append(
                {column_to_role.get(key, key): value for key, value in row.items()}
            )
        return rows

    def load_admission(self, path: Path | str) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        relations = payload.get("relations") or {}
        self.admission = {
            str(name): ("PURPOSE" if str(scope) == "PURPOSE" else "WORLD")
            for name, scope in relations.items()
        }

    def admission_payload(self) -> dict[str, Any]:
        return {"relations": dict(sorted(self.admission.items()))}

    def _scope(self, relation: str) -> Scope:
        if relation not in self.admission:
            raise ConstructionError(
                f"relation {relation!r} has no admission scope; declare_relation first"
            )
        return self.admission[relation]


def role_text(name: str) -> Role:
    return Role(name, RoleType.TEXT)


def role_referent(name: str) -> Role:
    return Role(name, RoleType.REFERENT)
