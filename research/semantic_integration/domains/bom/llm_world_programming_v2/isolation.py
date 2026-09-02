"""Physical isolation: trial live dirs live under /tmp and cannot see the repo."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

EXPERIMENT_ID = "bom-llm-world-programming-v3"
LIVE_ROOT = Path("/tmp/world-experiment") / EXPERIMENT_ID
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO = PACKAGE_ROOT.parents[4]


def cursor_project_dirs() -> list[Path]:
    """Hide Cursor project indexes that can leak this repository or prior trials."""

    root = Path.home() / ".cursor" / "projects"
    return [root] if root.is_dir() else []


def hidden_paths() -> list[Path]:
    paths = [REPO, LIVE_ROOT, *cursor_project_dirs()]
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def canary_paths() -> list[Path]:
    world_programming = (
        REPO
        / "research"
        / "semantic_integration"
        / "domains"
        / "bom"
        / "world_programming"
    )
    v1 = PACKAGE_ROOT.parent / "llm_world_programming"
    return [
        REPO / "CLAUDE.md",
        world_programming / "expected" / "analysis_a.json",
        world_programming / "expected" / "analysis_b.json",
        world_programming / "raw" / "analysis_a.py",
        world_programming / "raw" / "analysis_b.py",
        world_programming / "world" / "analysis_a.py",
        world_programming / "world" / "analysis_b.py",
        v1 / "report.md",
        v1 / "experiment_manifest.json",
    ]


def new_live_workspace() -> Path:
    LIVE_ROOT.mkdir(parents=True, exist_ok=True)
    destination = LIVE_ROOT / secrets.token_hex(16)
    destination.mkdir(parents=True)
    return destination


def bwrap_command(workspace: Path, argv: list[str]) -> list[str]:
    if not workspace.is_dir():
        raise RuntimeError(f"live workspace missing: {workspace}")
    command = [
        "bwrap",
        "--die-with-parent",
        "--bind",
        "/",
        "/",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
    ]
    for path in hidden_paths():
        command.extend(["--tmpfs", str(path)])
    command.extend(
        [
            "--bind",
            str(workspace),
            str(workspace),
            "--chdir",
            str(workspace),
            "--",
            *argv,
        ]
    )
    return command


def isolated_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Drop repo-local virtualenv paths so Python remains visible after tmpfs."""

    env = dict(base if base is not None else os.environ)
    repo = str(REPO)
    for key in ("VIRTUAL_ENV", "UV_PROJECT", "UV_PROJECT_DIR", "PYTHONHOME"):
        env.pop(key, None)
    path_parts = []
    for part in env.get("PATH", "").split(":"):
        if not part:
            continue
        try:
            resolved = str(Path(part).resolve())
        except OSError:
            resolved = part
        if resolved == repo or resolved.startswith(repo + os.sep):
            continue
        path_parts.append(part)
    env["PATH"] = ":".join(path_parts) or "/usr/bin:/bin:/usr/local/bin"
    pythonpath = []
    for part in env.get("PYTHONPATH", "").split(":"):
        if not part:
            continue
        try:
            resolved = str(Path(part).resolve())
        except OSError:
            resolved = part
        if resolved == repo or resolved.startswith(repo + os.sep):
            continue
        pythonpath.append(part)
    if pythonpath:
        env["PYTHONPATH"] = ":".join(pythonpath)
    else:
        env.pop("PYTHONPATH", None)
    return env


def host_python() -> str:
    for candidate in ("/usr/bin/python3", "/home/kerem/miniconda3/bin/python3"):
        path = Path(candidate)
        if path.exists() and not str(path.resolve()).startswith(str(REPO)):
            return candidate
    raise RuntimeError("no Python interpreter outside the repository")


def run_isolated(
    workspace: Path,
    argv: list[str],
    *,
    timeout: int | None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        bwrap_command(workspace, argv),
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=isolated_env(env),
    )


PREFLIGHT_SOURCE = r"""
import json
import os
from pathlib import Path

workspace = Path(os.environ["ISOLATION_WORKSPACE"])
canaries = json.loads(os.environ["ISOLATION_CANARIES"])
sibling = Path(os.environ["ISOLATION_SIBLING"])
failures = []

if not (workspace / "README.md").is_file():
    failures.append("workspace README missing")

repo = Path(os.environ["ISOLATION_REPO"])
try:
    names = list(repo.iterdir())
except OSError as error:
    names = [error]
if names:
    failures.append(f"repo listings visible: {names[:8]!r}")

for raw in canaries:
    path = Path(raw)
    if path.exists():
        failures.append(f"canary exists: {path}")

if sibling.exists():
    failures.append(f"sibling trial visible: {sibling}")

print(json.dumps({"ok": not failures, "failures": failures}))
if failures:
    raise SystemExit(1)
"""


def preflight_isolation(workspace: Path) -> dict[str, Any]:
    sibling = LIVE_ROOT / "sibling-canary" / "secret.json"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    if not sibling.exists():
        sibling.write_text('{"leak": true}\n', encoding="utf-8")
    env = os.environ.copy()
    env["ISOLATION_WORKSPACE"] = str(workspace)
    env["ISOLATION_REPO"] = str(REPO)
    env["ISOLATION_CANARIES"] = json.dumps([str(path) for path in canary_paths()])
    env["ISOLATION_SIBLING"] = str(sibling)
    completed = run_isolated(
        workspace,
        [host_python(), "-c", PREFLIGHT_SOURCE],
        timeout=30,
        env=env,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError, ValueError):
        payload = {
            "ok": False,
            "failures": [
                f"preflight did not return JSON (code={completed.returncode})",
                completed.stdout[-1000:],
                completed.stderr[-1000:],
            ],
        }
    if completed.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(f"isolation preflight failed: {payload}")
    return payload


def remove_live_workspace(workspace: Path) -> None:
    if workspace.exists() and LIVE_ROOT in workspace.parents:
        shutil.rmtree(workspace)
