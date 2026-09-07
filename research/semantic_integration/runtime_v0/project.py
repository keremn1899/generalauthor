"""Project root: sources + construction.py → candidate → accepted TaskView."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskview import RelationMode, Role, RoleType

from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation
from research.semantic_integration.runtime_v0.commit import (
    RunResult,
    discard_candidate,
    publish_candidate,
    validate_world_base_source,
    write_sidecars,
)
from research.semantic_integration.runtime_v0.purpose import Purpose, ensure_failure_relation
from research.semantic_integration.runtime_v0.source_helpers import Source
from research.semantic_integration.runtime_v0.world import (
    ConstructionError,
    ConstructionWorld,
    GroundingError,
)

WORLD_ID = "v0"


class Project:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.sources_dir = self.root / "sources"
        self.candidate_dir = self.root / "candidate"
        self.accepted_dir = self.root / "accepted"

    @property
    def accepted_world(self) -> Path:
        return self.accepted_dir / "world.sqlite"

    def run(self, construction: Path | str | None = None) -> RunResult:
        construction_path = Path(construction) if construction else self.root / "construction.py"
        purpose_text = ""
        purpose_file = self.root / "purpose.txt"
        if purpose_file.exists():
            purpose_text = purpose_file.read_text(encoding="utf-8")

        discard_candidate(self.candidate_dir)
        self.candidate_dir.mkdir(parents=True)
        db_path = self.candidate_dir / "world.sqlite"
        world = ConstructionWorld.create(db_path, world_id=WORLD_ID)
        purpose: Purpose | None = None
        try:
            ensure_failure_relation(world)
            purpose = Purpose(world, text=purpose_text)
            source = Source(self.sources_dir)
            namespace = _construction_namespace(source, world, purpose)
            if not construction_path.exists():
                raise ConstructionError("construction.py missing")
            code = construction_path.read_text(encoding="utf-8")
            exec(compile(code, str(construction_path), "exec"), namespace, namespace)
            construct = namespace.get("construct")
            if not callable(construct):
                raise ConstructionError("construction.py must define construct(source, world, purpose)")
            construct(source, world, purpose)
            write_sidecars(world, purpose.payload())
            report = validate_world_base_source(world)
            world.close()
            world = None  # type: ignore[assignment]
            if not report.ok:
                discard_candidate(self.candidate_dir)
                return RunResult(
                    accepted=False,
                    reason=report.reason,
                    errors=tuple(
                        f"{item['relation']}:{item['assertion_id']}" for item in report.ungrounded
                    ),
                )
            publish_candidate(self.candidate_dir, self.accepted_dir)
            return RunResult(accepted=True, accepted_dir=self.accepted_dir)
        except (GroundingError, ConstructionError, Exception) as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            if isinstance(exc, GroundingError):
                return RunResult(accepted=False, reason="ungrounded_world_base", errors=(str(exc),))
            if isinstance(exc, ConstructionError):
                return RunResult(accepted=False, reason="construction_error", errors=(str(exc),))
            return RunResult(
                accepted=False,
                reason="construction_error",
                errors=(f"{type(exc).__name__}: {exc}",),
            )

    def open_accepted(self) -> ConstructionWorld:
        if not self.accepted_world.exists():
            raise ConstructionError("no accepted World")
        return ConstructionWorld.open(self.accepted_world, world_id=WORLD_ID)


def _construction_namespace(source: Source, world: ConstructionWorld, purpose: Purpose) -> dict[str, Any]:
    return {
        "Source": Source,
        "source": source,
        "world": world,
        "purpose": purpose,
        "Role": Role,
        "RoleType": RoleType,
        "RelationMode": RelationMode,
        "ConstructionOrigin": ConstructionOrigin,
        "AssertionGrounding": AssertionGrounding,
        "SourceObservation": SourceObservation,
        "GroundingError": GroundingError,
        "ConstructionError": ConstructionError,
    }


__all__ = ["Project", "WORLD_ID"]
