"""Build physically isolated RAW and WORLD trial workspaces for v2."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from research.taskview_bom.experiment import FIXTURES, SOURCE_NAMES

ROOT = Path(__file__).resolve().parent.parent / "llm_world_programming_v3"
CODE_ROOT = Path(__file__).resolve().parent
REPO = CODE_ROOT.parents[4]
ASSETS = CODE_ROOT / "workspace_assets"
FROZEN_WORLD = ROOT / "fixtures"
V1_FIXTURES = CODE_ROOT.parent / "llm_world_programming" / "fixtures"
V2_FIXTURES = CODE_ROOT / "fixtures"
TASKVIEW_SRC = REPO / "taskview"
EXPECTED = CODE_ROOT.parent / "world_programming" / "expected"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def copy_frozen_world_fixture(*, force: bool = False) -> dict[str, str]:
    """Reuse the v1 compiled World bytes.  Do not reconstruct."""

    FROZEN_WORLD.mkdir(parents=True, exist_ok=True)
    names = ("world.sqlite", "world.sqlite.origins.json", "obligations.json")
    for name in names:
        source = V2_FIXTURES / name if (V2_FIXTURES / name).exists() else V1_FIXTURES / name
        if not source.exists():
            raise RuntimeError(f"v1 world fixture missing: {source}")
        destination = FROZEN_WORLD / name
        if destination.exists() and force:
            destination.chmod(0o644)
            destination.unlink()
        if force or not destination.exists():
            shutil.copy2(source, destination)
    return {name: sha256_file(FROZEN_WORLD / name) for name in names}


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
    for name in ("world.sqlite", "world.sqlite.origins.json", "obligations.json"):
        (destination / name).chmod(0o644)


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
            if "taskview" in path.parts:
                continue
            hits.append(str(path.relative_to(workspace)))
    return hits
