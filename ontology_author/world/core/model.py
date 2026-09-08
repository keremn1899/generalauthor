"""Small logical vocabulary for the World semantic implementation.

These types describe the logical boundary only.  Semantic relation rows live in
ordinary SQLite tables; these records configure and report that storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RoleType(StrEnum):
    REFERENT = "REFERENT"
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BOOLEAN = "BOOLEAN"


class RelationMode(StrEnum):
    BASE = "BASE"
    DERIVED = "DERIVED"


class AssertionOrigin(StrEnum):
    ASSERTED = "ASSERTED"
    DERIVED = "DERIVED"


class CompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class ExecutionStatus(StrEnum):
    NEVER_RUN = "NEVER_RUN"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    STALE = "STALE"


class GroundingKind(StrEnum):
    SOURCE = "SOURCE"
    WORLD = "WORLD"
    ASSERTION = "ASSERTION"
    DERIVATION = "DERIVATION"


@dataclass(frozen=True)
class Role:
    name: str
    type: RoleType


@dataclass(frozen=True)
class Grounding:
    """A compact pointer, not copied source content."""

    kind: GroundingKind
    reference: str
    detail: str = ""


@dataclass(frozen=True)
class Completeness:
    """An explicit local completeness claim for one derivation run."""

    status: CompletenessStatus
    universe: str
    basis: str = ""
    known_gaps: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssertionRef:
    assertion_id: str
    inserted: bool


@dataclass(frozen=True)
class DerivationResult:
    relation: str
    row_count: int
    result_fingerprint: str
    world_revision: int
    completeness_receipt_id: str


class WorldStoreError(ValueError):
    """The requested operation violates the World storage contract."""


class DerivationError(WorldStoreError):
    """A registered deterministic SQL derivation could not be materialized."""
