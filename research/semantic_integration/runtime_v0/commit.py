"""Candidate World execution, fail-closed accept validation, atomic publish.

Implements publication integrity and WORLD BASE SOURCE accountability for the
construction boundary. Does not change TaskView.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from research.semantic_integration.runtime_v0.world import ConstructionWorld


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    ungrounded: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class RunResult:
    accepted: bool
    reason: str = ""
    errors: tuple[str, ...] = ()
    accepted_dir: Path | None = None


def source_kinds_for_assertion(world: ConstructionWorld, assertion_id: str) -> list[dict[str, Any]]:
    return world.taskview.query(
        "SELECT kind, reference, detail FROM _tv_groundings "
        "WHERE subject_type = 'ASSERTION' AND subject_id = ?",
        (assertion_id,),
    )


def validate_world_base_source(world: ConstructionWorld) -> ValidationReport:
    """WORLD BASE tuples need SOURCE grounding. PURPOSE tuples do not."""

    ungrounded: list[dict[str, Any]] = []
    for relation, scope in world.admission.items():
        if scope != "WORLD":
            continue
        schema = world.relation_schema(relation)
        if schema["mode"] != "BASE":
            continue
        rows = world.taskview.query(
            "SELECT assertion_id FROM _tv_assertions WHERE relation_name = ?",
            (relation,),
        )
        for row in rows:
            assertion_id = row["assertion_id"]
            grounds = source_kinds_for_assertion(world, assertion_id)
            has_source = any(
                str(item["kind"]) == "SOURCE" and str(item["reference"] or "").strip()
                for item in grounds
            )
            if not has_source:
                ungrounded.append(
                    {
                        "assertion_id": assertion_id,
                        "relation": relation,
                        "scope": scope,
                    }
                )
    if ungrounded:
        return ValidationReport(
            ok=False,
            ungrounded=ungrounded,
            reason="ungrounded_world_base",
        )
    return ValidationReport(ok=True)


def write_sidecars(world: ConstructionWorld, purpose_payload: dict[str, Any]) -> None:
    directory = world.path.parent
    (directory / "world.admission.json").write_text(
        json.dumps(world.admission_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (directory / "world.purpose.json").write_text(
        json.dumps(purpose_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def publish_candidate(candidate: Path, accepted: Path) -> None:
    """Replace accepted with candidate as a directory rename, then drop candidate."""

    candidate = Path(candidate)
    accepted = Path(accepted)
    parent = accepted.parent
    staging = parent / (accepted.name + ".staging")
    previous = parent / (accepted.name + ".previous")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(candidate, staging)
    if previous.exists():
        shutil.rmtree(previous)
    if accepted.exists():
        accepted.rename(previous)
    staging.rename(accepted)
    if previous.exists():
        shutil.rmtree(previous)
    shutil.rmtree(candidate)


def discard_candidate(candidate: Path) -> None:
    path = Path(candidate)
    if path.exists():
        shutil.rmtree(path)


def fingerprint_accepted(accepted: Path) -> dict[str, str]:
    """Byte hashes of published artifacts. Missing files are absent keys."""

    import hashlib

    accepted = Path(accepted)
    out: dict[str, str] = {}
    if not accepted.exists():
        return out
    for path in sorted(accepted.iterdir()):
        if path.is_file():
            out[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out
