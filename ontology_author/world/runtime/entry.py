"""Small deterministic construction primitives for project-local Worlds."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ontology_author.world.runtime.commit import RunResult
from ontology_author.world.runtime.project import Project


def create(workspace: Path | str, *, purpose: str | Path | None = None) -> Path:
    """Create a World directory without running construction.

    The optional purpose argument is a convenience for hosts that already have
    a purpose statement. Normal users should let the attached agent maintain
    ``PURPOSE.md`` from the conversation.
    """

    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    if purpose is not None:
        purpose_path = Path(purpose)
        if purpose_path.is_file():
            shutil.copyfile(purpose_path, root / "PURPOSE.md")
        else:
            text = str(purpose).strip()
            (root / "PURPOSE.md").write_text(
                f"# Purpose\n\n{text}\n" if text else "# Purpose\n",
                encoding="utf-8",
            )
    return root


def rebuild(workspace: Path | str, *, construction: Path | str | None = None) -> RunResult:
    """Construct, validate, and replace this World's sealed bundle."""

    project = Project(workspace)
    result = project.run(construction)
    payload = {
        "succeeded": bool(result.succeeded),
        "reason": result.reason,
        "errors": list(result.errors),
    }
    (project.root / "diagnostics.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return result


def open_world(workspace: Path | str):
    return Project(workspace).open_world()


__all__ = ["create", "open_world", "rebuild"]
