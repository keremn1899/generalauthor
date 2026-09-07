"""Five isolated full Constructor v3 trials. P8 is normalize then deterministic project."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v3.admit import admit_workspace
from research.semantic_integration.domains.diligence.constructor_v3.agent import (
    MODEL,
    run_v3_agent,
)
from research.semantic_integration.domains.diligence.constructor_v3.isolation import (
    EXPERIMENT_ID,
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.constructor_v3.prompts import (
    PASS_ORDER,
    PROMPTS,
    TIMEOUTS,
)
from research.semantic_integration.domains.diligence.constructor_v3.runtime.projector import (
    write_workspace_outputs,
)
from research.semantic_integration.domains.diligence.constructor_v3.workspaces import (
    TRIALS,
    install_pass_task,
    restore_frozen_artifacts,
    seed_ordinary_workspace,
    snapshot_pass,
)

ROOT = Path(__file__).resolve().parent


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


def trial_dir(index: int) -> Path:
    return TRIALS / f"T{index}"


def pass_done(sealed: Path, pass_id: str) -> bool:
    return (sealed / "passes" / pass_id / "agent.json").exists()


def abort(reason: str) -> None:
    payload = {
        "aborted": True,
        "reason": reason,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    (ROOT / "axis_d" / "ABORTED.json").write_text(json.dumps(payload, indent=2) + "\n")
    raise RuntimeError(reason)


def run_one_pass(trial_index: int, pass_id: str) -> dict:
    sealed = trial_dir(trial_index)
    sealed.mkdir(parents=True, exist_ok=True)
    if pass_done(sealed, pass_id):
        return json.loads((sealed / "passes" / pass_id / "agent.json").read_text())
    live = new_live_workspace()
    out = sealed / "passes" / pass_id
    out.mkdir(parents=True, exist_ok=True)
    try:
        seed_ordinary_workspace(live)
        restore_frozen_artifacts(live, sealed, pass_id)
        if pass_id == "p8":
            preflight = preflight_isolation(live)
            write_workspace_outputs(live)
            record = {
                "trial": trial_index,
                "pass_id": pass_id,
                "returncode": 0,
                "timed_out": False,
                "model": "deterministic-projector",
                "reported_model": None,
                "adapter": "constructor-v3-projector",
                "isolation_leaks": [],
                "isolation_preflight": preflight,
                "tools": {"mentioned_paths": []},
                "source_reads": 0,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
            (out / "agent.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            snapshot_pass(live, sealed, pass_id)
            return record
        install_pass_task(live, pass_id)
        preflight = preflight_isolation(live)
        agent = run_v3_agent(
            workspace=live,
            prompt=PROMPTS[pass_id],
            timeout_seconds=TIMEOUTS[pass_id],
        )
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        stdout_text = agent["stdout"] or ""
        stderr_text = agent["stderr"] or ""
        (out / "transcript.stdout.txt").write_text(stdout_text[:2_000_000])
        (out / "transcript.stderr.txt").write_text(stderr_text[:500_000])
        if pass_id == "p5":
            admit_workspace(live)
        record = {
            "trial": trial_index,
            "pass_id": pass_id,
            "returncode": agent["returncode"],
            "timed_out": agent["timed_out"],
            "model": agent["model"],
            "reported_model": agent.get("reported_model"),
            "adapter": agent["adapter"],
            "isolation_leaks": leaks,
            "isolation_preflight": preflight,
            "tools": agent["tools"],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        (out / "agent.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        snapshot_pass(live, sealed, pass_id)
        if leaks:
            abort(f"isolation failed T{trial_index} {pass_id}: {leaks}")
        return record
    finally:
        remove_live_workspace(live)


def run_trial(trial_index: int) -> dict:
    results = []
    for pass_id in PASS_ORDER:
        results.append(run_one_pass(trial_index, pass_id))
    return {"trial": trial_index, "passes": [row["pass_id"] for row in results]}


def run_all_trials() -> dict:
    summaries = []
    for index in range(1, 6):
        summaries.append(run_trial(index))
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "model": MODEL,
        "trials": summaries,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    dest = ROOT / "axis_d"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "campaign.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=int)
    parser.add_argument("--pass-id")
    parser.add_argument("--run-ordinary", action="store_true")
    args = parser.parse_args()
    if args.trial and args.pass_id:
        print(json.dumps(run_one_pass(args.trial, args.pass_id), indent=2, sort_keys=True))
    elif args.trial:
        print(json.dumps(run_trial(args.trial), indent=2, sort_keys=True))
    elif args.run_ordinary:
        print(json.dumps(run_all_trials(), indent=2, sort_keys=True))
    else:
        parser.error("specify --run-ordinary or --trial")
