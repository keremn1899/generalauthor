"""Run the preregistered isolated A/B RAW vs WORLD coding-agent campaign."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import statistics
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.metrics import (
    program_burden,
)
from research.semantic_integration.domains.bom.llm_world_programming.prompts import (
    participant_prompt,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    run_agent,
    model_is_expensive,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.freeze_manifest import (
    CONDITIONS,
    N_TRIALS,
    TASK_IDS,
    freeze as freeze_manifest,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import (
    EXPERIMENT_ID,
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.scorer import (
    score_run,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.workspaces import (
    ROOT,
    build_raw_workspace,
    build_world_workspace,
    forbidden_paths_present,
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verify_manifest() -> dict[str, Any]:
    path = ROOT / "experiment_manifest.json"
    sidecar = ROOT / "experiment_manifest.json.sha256"
    if not path.exists() or not sidecar.exists():
        raise RuntimeError("manifest is not frozen")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    body = {key: value for key, value in loaded.items() if key != "fingerprint"}
    digest = "sha256:" + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if digest != loaded.get("fingerprint") or sidecar.read_text(
        encoding="utf-8"
    ).strip() != digest:
        raise RuntimeError("manifest fingerprint mismatch")
    if loaded["experiment_id"] != EXPERIMENT_ID:
        raise RuntimeError("unexpected experiment id")
    if loaded["n_trials"] != N_TRIALS:
        raise RuntimeError("trial count drifted from frozen protocol")
    if loaded["tasks"] != list(TASK_IDS):
        raise RuntimeError("task list drifted from frozen protocol")
    from research.semantic_integration.domains.bom.llm_world_programming_v2.workspaces import (
        ASSETS,
        FROZEN_WORLD,
        sha256_file,
    )

    for name, expected in loaded["world_fixture_fingerprint"].items():
        actual = sha256_file(FROZEN_WORLD / name)
        if actual != expected:
            raise RuntimeError(f"world fixture drifted after freeze: {name}")
    api = sha256_file(ASSETS / "world" / "world_surface.py")
    if api != loaded["world_api_fingerprint"]:
        raise RuntimeError("world_surface.py drifted after freeze")
    return loaded


def trial_dir(condition: str, task_id: str, trial: int) -> Path:
    return ROOT / condition / task_id / f"trial_{trial:03d}"


def isolation_leaks_from_events(events: list[dict[str, Any]]) -> list[str]:
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
        if not path.startswith(repo):
            continue
        if isinstance(result, dict) and "success" in result:
            leaks.append(path)
    return leaks


def run_trial(
    condition: str,
    task_id: str,
    trial: int,
    *,
    model: str,
    allow_expensive: bool = False,
) -> dict[str, Any]:
    destination = trial_dir(condition, task_id, trial)
    destination.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        if condition == "raw":
            build_raw_workspace(live)
        else:
            build_world_workspace(live)
        leaks = forbidden_paths_present(live, condition)
        if leaks:
            raise RuntimeError(f"workspace leak before trial: {leaks}")
        preflight = preflight_isolation(live)
        prompt = participant_prompt(condition, task_id)
        (destination / "prompt.txt").write_text(prompt, encoding="utf-8")
        (destination / "live_workspace.txt").write_text(str(live) + "\n", encoding="utf-8")
        agent = run_agent(
            workspace=live,
            prompt=prompt,
            model=model,
            allow_expensive=allow_expensive,
        )
        (destination / "transcript.stdout.txt").write_text(
            agent["stdout"] or "", encoding="utf-8"
        )
        (destination / "transcript.stderr.txt").write_text(
            agent["stderr"] or "", encoding="utf-8"
        )
        isolation_leaks = isolation_leaks_from_events(agent.get("events") or [])
        _write(
            destination / "agent.json",
            {
                "returncode": agent["returncode"],
                "timed_out": agent["timed_out"],
                "usage": agent["usage"],
                "tools": agent["tools"],
                "model": agent["model"],
                "adapter": agent["adapter"],
                "timeout_seconds": agent["timeout_seconds"],
                "isolation_leaks": isolation_leaks,
            },
        )
        analysis = live / "analysis.py"
        if analysis.exists():
            (destination / "final_program.py").write_text(
                analysis.read_text(encoding="utf-8"), encoding="utf-8"
            )
        output = live / "output.json"
        if output.exists():
            (destination / "final_output.json").write_bytes(output.read_bytes())
        saved_workspace = destination / "workspace"
        if saved_workspace.exists():
            shutil.rmtree(saved_workspace)
        shutil.copytree(live, saved_workspace)
    finally:
        remove_live_workspace(live)
    with tempfile.TemporaryDirectory(prefix="llm-wp-v2-score-") as clean:
        score = score_run(
            condition=condition,
            task_id=task_id,
            trial_dir=destination / "workspace",
            clean_root=Path(clean) / "env",
        )
    burden = program_burden(destination / "final_program.py")
    record = {
        "condition": condition,
        "task_id": task_id,
        "trial": trial,
        "score": score,
        "usage": agent["usage"],
        "tools": agent["tools"],
        "timed_out": agent["timed_out"],
        "program_burden": burden,
        "leaks_before": leaks,
        "isolation_preflight": preflight,
        "isolation_leaks": isolation_leaks,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    _write(destination / "metrics.json", record)
    return record


def all_runs() -> list[tuple[str, str, int]]:
    runs: list[tuple[str, str, int]] = []
    for condition in CONDITIONS:
        for task_id in TASK_IDS:
            for trial in range(1, N_TRIALS + 1):
                runs.append((condition, task_id, trial))
    return runs


def median(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return statistics.median(clean)


def wilson(successes: int, n: int) -> tuple[float, float] | None:
    if n <= 0:
        return None
    z = 1.96
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def aggregate(records: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    def subset(condition: str | None = None, task_id: str | None = None):
        rows = records
        if condition:
            rows = [row for row in rows if row["condition"] == condition]
        if task_id:
            rows = [row for row in rows if row["task_id"] == task_id]
        return rows

    def success_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(rows)
        wins = sum(1 for row in rows if row["score"].get("pass"))
        interval = wilson(wins, n)
        return {
            "n": n,
            "pass": wins,
            "rate": (wins / n) if n else 0.0,
            "wilson_95": list(interval) if interval else None,
        }

    failures: dict[str, int] = {}
    for row in records:
        klass = row["score"].get("failure_class")
        if klass:
            failures[klass] = failures.get(klass, 0) + 1
    unknown_as_false = sum(
        1 for row in records if row["score"].get("unknown_as_false")
    )
    provenance = [row for row in records if row["task_id"] == "analysis_a"]
    isolation_leak_count = sum(1 for row in records if row.get("isolation_leaks"))
    by_condition = {
        condition: success_block(subset(condition=condition)) for condition in CONDITIONS
    }
    by_task = {
        f"{condition}:{task_id}": success_block(
            subset(condition=condition, task_id=task_id)
        )
        for condition in CONDITIONS
        for task_id in TASK_IDS
    }
    tokens = {
        condition: {
            "median_input": median(
                [row["usage"].get("input_tokens") for row in subset(condition=condition)]
            ),
            "median_output": median(
                [row["usage"].get("output_tokens") for row in subset(condition=condition)]
            ),
            "median_total": median(
                [row["usage"].get("total_tokens") for row in subset(condition=condition)]
            ),
        }
        for condition in CONDITIONS
    }
    tools = {
        condition: {
            "median_tool_calls": median(
                [row["tools"].get("tool_calls_started") for row in subset(condition=condition)]
            ),
            "median_shell_calls": median(
                [row["tools"].get("shell_calls") for row in subset(condition=condition)]
            ),
        }
        for condition in CONDITIONS
    }
    loc = {
        condition: median(
            [
                row["program_burden"].get("nonempty_lines")
                for row in subset(condition=condition)
                if row["program_burden"].get("exists")
            ]
        )
        for condition in CONDITIONS
    }
    return {
        "experiment_id": manifest["experiment_id"],
        "provider_inference_calls": len(records),
        "success": {
            "overall": success_block(records),
            "by_condition": by_condition,
            "by_task_condition": by_task,
        },
        "failure_classes": failures,
        "unknown_as_false_count": unknown_as_false,
        "provenance_support_rate": (
            sum(1 for row in provenance if row["score"].get("support_present"))
            / len(provenance)
            if provenance
            else None
        ),
        "tokens": tokens,
        "tools": tools,
        "median_nonempty_loc": loc,
        "world_increased_success": by_condition["world"]["rate"] > by_condition["raw"]["rate"],
        "isolation_leak_runs": isolation_leak_count,
        "records": records,
    }


def render_report(report: dict[str, Any]) -> str:
    success = report["success"]
    raw = success["by_condition"]["raw"]
    world = success["by_condition"]["world"]
    lines = [
        "# Isolated A/B replication: RAW sources vs compiled World IR",
        "",
        f"Experiment `{report['experiment_id']}`. Provider/model calls: **{report['provider_inference_calls']}**.",
        "",
        "Primary metric: saved program executes and canonical JSON matches the frozen expected artifact.",
        "",
        "Isolation: bwrap hides the repository, Cursor project directory, and sibling live trials. Live workspaces are under `/tmp/world-experiment`.",
        "",
        "## Success",
        "",
        f"- RAW: {raw['pass']}/{raw['n']} ({raw['rate']:.2%}), Wilson 95% {raw['wilson_95']}",
        f"- WORLD: {world['pass']}/{world['n']} ({world['rate']:.2%}), Wilson 95% {world['wilson_95']}",
        f"- WORLD increased exact success: {report['world_increased_success']}",
        f"- Isolation leak runs (successful repo Reads): {report['isolation_leak_runs']}",
        "",
        "### Per task",
        "",
    ]
    for key, block in sorted(success["by_task_condition"].items()):
        lines.append(f"- `{key}`: {block['pass']}/{block['n']} ({block['rate']:.2%})")
    lines += [
        "",
        "## Failures",
        "",
        f"- classes: {report['failure_classes']}",
        f"- UNRESOLVED treated as false: {report['unknown_as_false_count']}",
        f"- Task A support field present: {report['provenance_support_rate']}",
        "",
        "## Effort",
        "",
        f"- median tokens RAW {report['tokens']['raw']}, WORLD {report['tokens']['world']}",
        f"- median tools RAW {report['tools']['raw']}, WORLD {report['tools']['world']}",
        f"- median nonempty LOC RAW {report['median_nonempty_loc']['raw']}, WORLD {report['median_nonempty_loc']['world']}",
        "",
        "## Conclusions",
        "",
        "### MEASURED",
        "",
        f"- RAW exact success {raw['pass']}/{raw['n']}; WORLD {world['pass']}/{world['n']}.",
        f"- Failure classes: {report['failure_classes']}.",
        f"- UNRESOLVED→false count: {report['unknown_as_false_count']}.",
        f"- Isolation leak runs: {report['isolation_leak_runs']}.",
        "",
        "### OBSERVED",
        "",
        "- Inspect trial programs for case-construction vs SQL/query failures.",
        "- Token fields remain incomplete if the provider reports last-turn usage only.",
        "",
        "### HYPOTHESIS",
        "",
        "- A WORLD win on A/B under isolation supports: compilation removes world-reconstruction from downstream programs.",
        "- Task C, visualization, and a second domain wait on this result.",
        "",
        "## Limitations",
        "",
        "- `ADJUDICATED_FALSE` is not representable.",
        "- One model, one BOM fixture, tasks A and B only.",
        "",
    ]
    return "\n".join(lines) + "\n"


def run_campaign() -> dict[str, Any]:
    manifest = verify_manifest()
    model = str(manifest["model"])
    if model_is_expensive(model):
        print(
            f"warning: frozen campaign {manifest['experiment_id']} uses {model}; "
            "finishing that protocol only. New campaigns default to composer-2.5.",
            flush=True,
        )
    records: list[dict[str, Any]] = []
    for condition, task_id, trial in all_runs():
        destination = trial_dir(condition, task_id, trial)
        metrics_path = destination / "metrics.json"
        if metrics_path.exists():
            records.append(json.loads(metrics_path.read_text(encoding="utf-8")))
            continue
        records.append(
            run_trial(
                condition,
                task_id,
                trial,
                model=model,
                allow_expensive=model_is_expensive(model),
            )
        )
        print(
            json.dumps(
                {
                    "completed": f"{condition}/{task_id}/trial_{trial:03d}",
                    "pass": records[-1]["score"].get("pass"),
                    "failure_class": records[-1]["score"].get("failure_class"),
                    "isolation_leaks": records[-1].get("isolation_leaks"),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    report = aggregate(records, manifest)
    scoring = ROOT / "scoring"
    _write(scoring / "run_scores.json", {"records": records})
    _write(
        scoring / "failure_analysis.json",
        {
            "failure_classes": report["failure_classes"],
            "unknown_as_false_count": report["unknown_as_false_count"],
            "isolation_leak_runs": report["isolation_leak_runs"],
        },
    )
    _write(
        ROOT / "report.json",
        {key: value for key, value in report.items() if key != "records"},
    )
    (ROOT / "report.md").write_text(render_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.freeze_only and args.run:
        raise SystemExit("choose one of --freeze-only or --run")
    if args.run:
        report = run_campaign()
        print(
            json.dumps(
                {
                    "experiment_id": report["experiment_id"],
                    "success": report["success"],
                    "provider_inference_calls": report["provider_inference_calls"],
                    "isolation_leak_runs": report["isolation_leak_runs"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        path = freeze_manifest()
        print(f"froze {path}")
