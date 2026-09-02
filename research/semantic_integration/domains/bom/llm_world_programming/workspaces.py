"""Build physically isolated RAW and WORLD trial workspaces."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
)
from research.taskview_bom.experiment import FIXTURES, SOURCE_NAMES

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
ASSETS = ROOT / "workspace_assets"
FROZEN_WORLD = ROOT / "fixtures"
TASKVIEW_SRC = REPO / "taskview"
EXPECTED = ROOT.parent / "world_programming" / "expected"


def sha256_file(path: Path) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_world_fixture() -> dict[str, str]:
    FROZEN_WORLD.mkdir(parents=True, exist_ok=True)
    db_path = FROZEN_WORLD / "world.sqlite"
    sidecar = Path(str(db_path) + ".origins.json")
    if db_path.exists():
        db_path.unlink()
    if sidecar.exists():
        sidecar.unlink()
    experimental = construct_experimental_world(db_path)
    obligations = {"obligations": experimental.obligations}
    experimental.world.close()
    obligations_path = FROZEN_WORLD / "obligations.json"
    obligations_path.write_text(
        json.dumps(obligations, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "world.sqlite": sha256_file(db_path),
        "world.sqlite.origins.json": sha256_file(Path(str(db_path) + ".origins.json")),
        "obligations.json": sha256_file(obligations_path),
    }


def _copy_taskview(destination: Path) -> None:
    dest = destination / "taskview"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        shutil.copy2(TASKVIEW_SRC / name, dest / name)


def build_raw_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    sources = destination / "sources"
    sources.mkdir()
    for name in SOURCE_NAMES:
        shutil.copy2(FIXTURES / name, sources / name)
    shutil.copy2(ASSETS / "raw" / "README.md", destination / "README.md")


def build_world_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    _copy_taskview(destination)
    shutil.copy2(ASSETS / "world" / "world_surface.py", destination / "world_surface.py")
    shutil.copy2(ASSETS / "world" / "WORLD_API.md", destination / "WORLD_API.md")
    shutil.copy2(ASSETS / "world" / "README.md", destination / "README.md")
    shutil.copy2(FROZEN_WORLD / "world.sqlite", destination / "world.sqlite")
    shutil.copy2(
        FROZEN_WORLD / "world.sqlite.origins.json",
        destination / "world.sqlite.origins.json",
    )
    shutil.copy2(FROZEN_WORLD / "obligations.json", destination / "obligations.json")


def forbidden_paths_present(workspace: Path, condition: str) -> list[str]:
    hits: list[str] = []
    forbidden_names = {
        "oracle.json",
        "expected",
        "analysis_a.py",
        "frontier_packets.json",
        "c2_campaign_report.json",
        "operational_frontier.json",
    }
    if condition == "world":
        forbidden_names.update(SOURCE_NAMES)
    if condition == "raw":
        forbidden_names.update({"world.sqlite", "WORLD_API.md", "world_surface.py"})
    for path in workspace.rglob("*"):
        if path.name in forbidden_names or path.name.startswith("analysis_"):
            if path.name in {"analysis.py"}:
                continue
            rel = str(path.relative_to(workspace))
            if "taskview" in path.parts:
                continue
            hits.append(rel)
    return hits
