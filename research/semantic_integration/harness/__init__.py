"""C0/C1/frontier/C2 experimental stages.  Not a general constructor."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin


TupleKey = tuple[str, tuple[Any, ...]]


@dataclass(frozen=True)
class FrozenOracle:
    oracle_id: str
    roles: Mapping[str, tuple[str, ...]]
    tuples: Mapping[str, set[tuple[Any, ...]]]
    origins: Mapping[TupleKey, ConstructionOrigin]


def load_oracle_document(oracle: Mapping[str, Any]) -> FrozenOracle:
    roles = {
        name: tuple(order) for name, order in oracle.get("role_order", {}).items()
    }
    tuples: dict[str, set[tuple[Any, ...]]] = {}
    origins: dict[TupleKey, ConstructionOrigin] = {}
    for relation, declaration in oracle["relations"].items():
        origin = ConstructionOrigin(declaration["origin"])
        raw = declaration.get("tuples")
        if raw is None:
            raw = [item["tuple"] for item in declaration["assertions"]]
        tuples[relation] = {tuple(item) for item in raw}
        for item in tuples[relation]:
            origins[(relation, item)] = origin
    return FrozenOracle(
        oracle_id=str(oracle["oracle_id"]),
        roles=roles,
        tuples=tuples,
        origins=origins,
    )


def established_tuples(world: SemanticWorld, oracle: FrozenOracle) -> dict[str, set[tuple[Any, ...]]]:
    return {relation: world.relation_tuples(relation) for relation in oracle.tuples}


def frontier(
    oracle: FrozenOracle,
    compiled: Mapping[str, set[tuple[Any, ...]]],
) -> dict[str, set[tuple[Any, ...]]]:
    residual: dict[str, set[tuple[Any, ...]]] = {}
    for relation, expected in oracle.tuples.items():
        missing = expected - compiled.get(relation, set())
        if missing:
            residual[relation] = missing
    return residual


def origin_account(oracle: FrozenOracle) -> dict[str, int]:
    counts = {origin.value: 0 for origin in ConstructionOrigin}
    for origin in oracle.origins.values():
        counts[origin.value] += 1
    return counts


def coverage(oracle: FrozenOracle, compiled: Mapping[str, set[tuple[Any, ...]]]) -> dict[str, Any]:
    c0 = sum(len(rows) for rows in oracle.tuples.values())
    residual = frontier(oracle, compiled)
    c1_established = 0
    semantic_established = 0
    for (relation, item), origin in oracle.origins.items():
        if item not in compiled.get(relation, set()):
            continue
        if origin is ConstructionOrigin.SEMANTIC:
            semantic_established += 1
        else:
            c1_established += 1
    return {
        "c0_tuples": c0,
        "compiled_tuples": sum(len(rows) for rows in compiled.values()),
        "c1_established": c1_established,
        "semantic_established": semantic_established,
        "mechanical_coverage": c1_established / c0 if c0 else 0.0,
        "frontier_tuple_count": sum(len(rows) for rows in residual.values()),
        "c0_by_origin": origin_account(oracle),
        "frontier": {
            name: [list(row) for row in sorted(rows)]
            for name, rows in sorted(residual.items())
        },
    }


Compiler = Callable[..., SemanticWorld]
Selector = Callable[[SemanticWorld, dict[str, set[tuple[Any, ...]]]], list[dict[str, Any]]]
