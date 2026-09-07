"""Execute construction.py with frozen runtime_v0 (not the in-memory PFPS World)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import host_python
from research.semantic_integration.capability.end_to_end_v1.isolation import run_isolated


def execute_project(workspace: Path, *, timeout: int = 120) -> dict[str, Any]:
    completed = run_isolated(
        workspace,
        [host_python(), str(workspace / "run_world.py")],
        timeout=timeout,
    )
    payload: dict[str, Any]
    diagnostics = workspace / "diagnostics.json"
    if diagnostics.exists():
        try:
            payload = json.loads(diagnostics.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"accepted": False, "reason": "diagnostics_parse_error"}
    else:
        payload = {"accepted": False, "reason": "no_diagnostics"}
    payload["returncode"] = completed.returncode
    payload["stdout_tail"] = (completed.stdout or "")[-4000:]
    payload["stderr_tail"] = (completed.stderr or "")[-4000:]
    return payload


def snapshot_accepted(workspace: Path, dest: Path) -> None:
    src = workspace / "accepted"
    if dest.exists():
        shutil.rmtree(dest)
    if src.exists():
        shutil.copytree(src, dest)
