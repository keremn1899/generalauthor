"""Project root: PURPOSE.md + construction.py → candidate → World.

``construction.py`` is the current authoring shape, not ontology. Evidence is
the ordinary project tree.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ontology_author.world.core.model import RelationMode, Role, RoleType

from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import (
    RunResult,
    discard_candidate,
    _replace_candidate,
    validate_world_base_source,
    write_sidecars,
)
from ontology_author.world.runtime.purpose import Purpose, ensure_failure_relation
from ontology_author.world.runtime.source_helpers import Source
from ontology_author.world.runtime.world import (
    ConstructionError,
    ConstructionWorld,
    GroundingError,
)

WORLD_ID = "v0"


class Project:
    def __init__(self, root: Path | str, *, project_root: Path | str | None = None) -> None:
        self.root = Path(root)
        self.project_root = (
            Path(project_root)
            if project_root is not None
            else self._infer_project_root(self.root)
        )
        self.candidate_dir = self.root / "candidate"
        self.world_dir = self.root / "world"

    @staticmethod
    def _infer_project_root(root: Path) -> Path:
        resolved = root.resolve()
        return resolved.parent.parent if resolved.parent.name == ".worlds" else resolved

    @property
    def world_path(self) -> Path:
        return self.world_dir / "world.sqlite"

    def run(self, construction: Path | str | None = None) -> RunResult:
        construction_path = Path(construction) if construction else self.root / "construction.py"
        purpose_text = ""
        purpose_file = self.root / "PURPOSE.md"
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
            source = Source(self.project_root)
            namespace = _construction_namespace(source, world, purpose)
            if not construction_path.exists():
                raise ConstructionError("construction.py missing")
            code = construction_path.read_text(encoding="utf-8")
            import_roots = [str(self.root.resolve()), str(self.project_root.resolve())]
            inserted = [path for path in import_roots if path not in sys.path]
            for path in reversed(inserted):
                sys.path.insert(0, path)
            try:
                exec(compile(code, str(construction_path), "exec"), namespace, namespace)
                construct = namespace.get("construct")
                if not callable(construct):
                    raise ConstructionError("construction.py must define construct(source, world, purpose)")
                construct(source, world, purpose)
            finally:
                for path in inserted:
                    try:
                        sys.path.remove(path)
                    except ValueError:
                        pass
            write_sidecars(world, purpose.payload())
            report = validate_world_base_source(world)
            world.close()
            world = None  # type: ignore[assignment]
            if not report.ok:
                discard_candidate(self.candidate_dir)
                return RunResult(
                    succeeded=False,
                    reason=report.reason,
                    errors=tuple(
                        f"{item['relation']}:{item['assertion_id']}" for item in report.ungrounded
                    ),
                )
            _replace_candidate(self.candidate_dir, self.world_dir)
            return RunResult(succeeded=True, world_dir=self.world_dir)
        except (GroundingError, ConstructionError, Exception) as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            if isinstance(exc, GroundingError):
                return RunResult(succeeded=False, reason="ungrounded_world_base", errors=(str(exc),))
            if isinstance(exc, ConstructionError):
                return RunResult(succeeded=False, reason="construction_error", errors=(str(exc),))
            return RunResult(
                succeeded=False,
                reason="construction_error",
                errors=(f"{type(exc).__name__}: {exc}",),
            )

    def open_world(self) -> ConstructionWorld:
        if not self.world_path.exists():
            raise ConstructionError("no World has been built")
        return ConstructionWorld.open(self.world_path, world_id=WORLD_ID)


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
