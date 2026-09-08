"""Filesystem discovery for project-local Worlds.

There is deliberately no registry: a World is a directory under ``.worlds``
whose sealed ``world/`` bundle contains ``world.sqlite``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

WORLD_DIR = ".worlds"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class WorldSelectionError(ValueError):
    """A requested World cannot be selected unambiguously."""


@dataclass(frozen=True)
class WorldRef:
    name: str
    path: Path

    @property
    def world(self) -> Path:
        return self.path / "world" / "world.sqlite"


def project_root(path: Path | str = ".") -> Path:
    return Path(path).expanduser().resolve()


def validate_name(name: str) -> str:
    value = str(name or "").strip()
    if not _NAME.fullmatch(value):
        raise WorldSelectionError(
            "World name must start with a letter or number and contain only "
            "letters, numbers, '.', '_' or '-'."
        )
    return value


def world_ref(project: Path | str, name: str) -> WorldRef:
    root = project_root(project)
    safe = validate_name(name)
    return WorldRef(safe, root / WORLD_DIR / safe)


def discover(project: Path | str = ".") -> list[WorldRef]:
    root = project_root(project) / WORLD_DIR
    if not root.is_dir():
        return []
    return [
        WorldRef(item.name, item)
        for item in sorted(root.iterdir(), key=lambda item: item.name.lower())
        if item.is_dir() and _NAME.fullmatch(item.name) and (item / "world" / "world.sqlite").exists()
    ]


def select(project: Path | str = ".", name: str | None = None) -> WorldRef:
    if name:
        selected = world_ref(project, name)
        if not selected.world.exists():
            raise WorldSelectionError(
                f"World {selected.name!r} has not been built; rebuild it first"
            )
        return selected
    worlds = discover(project)
    if len(worlds) == 1:
        return worlds[0]
    if not worlds:
        raise WorldSelectionError(
            f"no Worlds found under {project_root(project) / WORLD_DIR}"
        )
    names = ", ".join(item.name for item in worlds)
    raise WorldSelectionError(f"several Worlds exist; choose one: {names}")


__all__ = ["WORLD_DIR", "WorldRef", "WorldSelectionError", "discover", "project_root", "select", "validate_name", "world_ref"]
