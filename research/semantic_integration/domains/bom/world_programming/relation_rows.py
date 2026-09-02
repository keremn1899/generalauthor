"""Experiment-local relation materialization.  Not a kernel primitive."""

from __future__ import annotations

from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld


def relation_rows(world: SemanticWorld, relation: str) -> list[dict[str, Any]]:
    roles = world.taskview.relation_schema(relation)["roles"]
    columns = [role["column"] for role in roles]
    sql = f"SELECT {', '.join(columns)} FROM {relation}"
    return world.query_semantic(sql)
