"""The wheel contains only the current Ontology Author product surface."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _project() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_runtime_dependencies_are_minimal_and_explicit():
    project = _project()["project"]
    assert set(project["dependencies"]) == {"starlette>=0.37,<1", "uvicorn>=0.29"}
    assert set(project["optional-dependencies"]) == {"dev"}


def test_legacy_graph_and_agent_dependencies_are_not_packaged():
    project = _project()
    assert set(project["project"]["scripts"]) == {"author"}
    assert project["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "ontology_author*",
    ]
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in ("ladybug", "mcp", "openrouter", "cursor-sdk", "graphauthor"):
        assert forbidden not in text
def test_ignored_runtime_rule_does_not_hide_world_runtime():
    tracked = {path.as_posix() for path in (ROOT / "ontology_author/world/runtime").rglob("*.py")}
    assert tracked
    assert all(not path.startswith("runtime/") for path in tracked)


def test_historical_store_package_is_not_discoverable():
    packages = {
        path.parent.relative_to(ROOT).as_posix().replace("/", ".")
        for path in ROOT.rglob("__init__.py")
        if ".venv" not in path.parts and "build" not in path.parts
    }
    historical_package = "task" + "view"
    assert historical_package not in packages
    assert all(not package.startswith(historical_package + ".") for package in packages)
