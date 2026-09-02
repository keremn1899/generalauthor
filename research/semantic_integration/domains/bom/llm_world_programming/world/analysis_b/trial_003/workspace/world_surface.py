"""Workspace-local World access.  Generic read surface, no domain hints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from taskview import TaskView

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "world.sqlite"
ORIGINS_PATH = ROOT / "world.sqlite.origins.json"
OBLIGATIONS_PATH = ROOT / "obligations.json"


class World:
    """Read access to the compiled semantic World in this workspace."""

    def __init__(self) -> None:
        self.path = DB_PATH
        self._tv = TaskView(self.path, view_id="bom-world-programming-s1")
        self._origins = {}
        if ORIGINS_PATH.exists():
            self._origins = dict(
                json.loads(ORIGINS_PATH.read_text(encoding="utf-8")).get("assertions", {})
            )

    @property
    def taskview(self):
        return self._tv

    def describe(self) -> dict[str, Any]:
        return self._tv.describe()

    def describe_text(self) -> str:
        return self._tv.describe_text()

    def relation_schema(self, relation: str) -> dict[str, Any]:
        return self._tv.relation_schema(relation)

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
        if assertion_id in self._origins:
            detail["construction_origin"] = self._origins[assertion_id]
        elif detail.get("origin") == "DERIVED":
            detail["construction_origin"] = "DERIVED"
        return detail

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        return self._tv.latest_completeness(relation)

    def is_stale(self, relation: str) -> bool:
        return self._tv.is_stale(relation)

    def stale_relations(self) -> list[str]:
        return self._tv.stale_relations()

    def obligations(self) -> list[dict[str, Any]]:
        return json.loads(OBLIGATIONS_PATH.read_text(encoding="utf-8"))["obligations"]

    def close(self) -> None:
        self._tv.close()


def open_world() -> World:
    return World()


def relation_rows(world: World, relation: str) -> list[dict[str, Any]]:
    roles = world.relation_schema(relation)["roles"]
    columns = [role["column"] for role in roles]
    sql = f"SELECT {', '.join(columns)} FROM {relation}"
    return world.query_semantic(sql)
