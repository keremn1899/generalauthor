"""Stable, serialisable protocol types for the relational-materialization pilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Heterogeneity(StrEnum):
    PRESTRUCTURED = "H0"
    MIXED = "H2"


class Novelty(StrEnum):
    STANDARD = "N0"
    TASK_SPECIFIC = "N2"


class Arm(StrEnum):
    ORDINARY = "A"
    RELATION_STORE = "B"
    GRAPHAUTHOR_FORCED = "C"
    GRAPHAUTHOR_OPTIONAL = "D"


@dataclass(frozen=True)
class Cell:
    heterogeneity: Heterogeneity
    novelty: Novelty
    reuse: int

    @property
    def id(self) -> str:
        return f"{self.heterogeneity}-{self.novelty}-R{self.reuse}"


@dataclass(frozen=True)
class Operation:
    id: str
    prompt: str
    answer_ids: tuple[str, ...]
    relation: str

    def to_json(self) -> dict[str, Any]:
        result = asdict(self)
        result["answer_ids"] = list(self.answer_ids)
        return result


@dataclass(frozen=True)
class LatentWorld:
    """Evaluator-only facts. Never copy this object into an agent workspace."""

    seed: int
    resources: tuple[dict[str, Any], ...]
    teams: tuple[dict[str, Any], ...]
    services: tuple[dict[str, Any], ...]
    tests: tuple[dict[str, Any], ...]
    runbooks: tuple[dict[str, Any], ...]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)
