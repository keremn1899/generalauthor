"""Run the isolated constructor. Stop if isolation fails."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_agent import (
    MODEL,
    run_constructor,
)
from research.semantic_integration.domains.diligence.isolation import (
    EXPERIMENT_ID,
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.workspaces import (
    CONSTRUCTOR_OUT,
    ROOT,
    TASK,
    build_constructor_workspace,
)


def isolation_leaks_from_events(events: list) -> list[str]:
    leaks: list[str] = []
    repo = str(REPO)
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        call = event.get("tool_call") or {}
        kind = next(iter(call), "")
        if kind != "readToolCall":
            continue
        payload = call.get(kind) or {}
        args = payload.get("args") or {}
        result = payload.get("result") or {}
        path = str(args.get("path") or "")
        if path.startswith(repo) and isinstance(result, dict) and "success" in result:
            leaks.append(path)
    return leaks


def run_abc_construction() -> dict:
    manifest_path = ROOT / "experiment_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("fixture is not frozen")
    live = new_live_workspace()
    destination = CONSTRUCTOR_OUT / "abc"
    destination.mkdir(parents=True, exist_ok=True)
    try:
        build_constructor_workspace(live)
        preflight = preflight_isolation(live)
        prompt = (live / "CONSTRUCTION_TASK.md").read_text(encoding="utf-8")
        agent = run_constructor(workspace=live, prompt=prompt)
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        (destination / "transcript.stdout.txt").write_text(agent["stdout"] or "", encoding="utf-8")
        (destination / "transcript.stderr.txt").write_text(agent["stderr"] or "", encoding="utf-8")
        (destination / "agent.json").write_text(
            json.dumps(
                {
                    "returncode": agent["returncode"],
                    "timed_out": agent["timed_out"],
                    "tools": agent["tools"],
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "adapter": agent["adapter"],
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        saved = destination / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
    finally:
        remove_live_workspace(live)
    if leaks:
        raise RuntimeError(f"isolation failed; constructor leaked {leaks}")
    return {"experiment_id": EXPERIMENT_ID, "model": MODEL, "isolation_leaks": leaks}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--construct-abc", action="store_true")
    args = parser.parse_args()
    if args.construct_abc:
        print(json.dumps(run_abc_construction(), indent=2, sort_keys=True))
    else:
        from research.semantic_integration.domains.diligence.freeze_apparatus import freeze

        print(f"froze {freeze()}")
