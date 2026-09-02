"""Run the frozen Composer 2.5 RAW vs WORLD substitution campaign."""

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
from research.semantic_integration.domains.bom.llm_world_programming_composer25.agent import (
    MODEL,
    run_agent,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.freeze_manifest import (
    CONDITIONS,
    N_TRIALS,
    TASK_IDS,
    freeze as freeze_manifest,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.isolation import (
    EXPERIMENT_ID,
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.scorer import (
    score_run,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.workspaces import (
    ROOT,
    build_raw_workspace,
    build_world_workspace,
    forbidden_paths_present,
    sha256_file,
)


class IsolationFailed(RuntimeError):
    """Physical isolation did not hold; the campaign must stop."""


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verify_manifest() -> dict[str, Any]:
    path = ROOT / "manifest.json"
    sidecar = ROOT / "manifest.json.sha256"
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
    if loaded["model"] != MODEL:
        raise RuntimeError("frozen model is not composer-2.5")
    if loaded["n_trials"] != N_TRIALS:
        raise RuntimeError("trial count drifted from frozen protocol")
    if loaded["tasks"] != list(TASK_IDS):
        raise RuntimeError("task list drifted from frozen protocol")
    from research.semantic_integration.domains.bom.llm_world_programming_composer25.workspaces import (
        ASSETS,
        FROZEN_WORLD,
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


def run_trial(condition: str, task_id: str, trial: int, *, model: str) -> dict[str, Any]:
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
        agent = run_agent(workspace=live, prompt=prompt, model=model)
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
    with tempfile.TemporaryDirectory(prefix="llm-wp-c25-score-") as clean:
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
    if isolation_leaks:
        raise IsolationFailed(
            f"{condition}/{task_id}/trial_{trial:03d} leaked {isolation_leaks}"
        )
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


def cost_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    monetary = [
        row["usage"].get("monetary_cost_keys")
        for row in records
        if row.get("usage", {}).get("monetary_cost_exposed")
    ]
    return {
        "monetary_cost_exposed": bool(monetary),
        "monetary_cost_keys_seen": monetary,
        "total_campaign_cost": None,
        "cost_by_condition": None,
        "cost_per_successful_run": None,
        "reason_if_unavailable": (
            None
            if monetary
            else (
                "Cursor stream-json result.usage did not expose monetary cost. "
                "Token and cache fields are retained and are not converted into dollars."
            )
        ),
        "cache_read_tokens_sum": sum(
            row["usage"].get("cache_read_tokens") or 0 for row in records
        ),
        "cache_write_tokens_sum": sum(
            row["usage"].get("cache_write_tokens") or 0 for row in records
        ),
        "input_tokens_sum": sum(row["usage"].get("input_tokens") or 0 for row in records),
        "output_tokens_sum": sum(
            row["usage"].get("output_tokens") or 0 for row in records
        ),
        "note": (
            "input/output token fields from stream-json are treated as incomplete "
            "session accounting, as in v1/v3."
        ),
    }


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
            "median_read_calls": median(
                [row["tools"].get("read_calls") for row in subset(condition=condition)]
            ),
            "median_python_executions_guess": median(
                [
                    row["tools"].get("python_executions_guess")
                    for row in subset(condition=condition)
                ]
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
    schema_fields = {
        condition: median(
            [
                len(row["program_burden"].get("source_schema_fields") or [])
                for row in subset(condition=condition)
                if row["program_burden"].get("exists")
            ]
        )
        for condition in CONDITIONS
    }
    relations = {
        condition: median(
            [
                len(row["program_burden"].get("relation_references") or [])
                for row in subset(condition=condition)
                if row["program_burden"].get("exists")
            ]
        )
        for condition in CONDITIONS
    }
    return {
        "experiment_id": manifest["experiment_id"],
        "model": manifest["model"],
        "adapter": manifest["adapter"],
        "manifest_fingerprint": manifest["fingerprint"],
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
        "median_source_schema_fields": schema_fields,
        "median_relation_references": relations,
        "world_increased_success": by_condition["world"]["rate"]
        > by_condition["raw"]["rate"],
        "isolation_leak_runs": isolation_leak_count,
        "isolation_held": isolation_leak_count == 0,
        "cost": cost_summary(records),
        "historical_v3_not_pooled": manifest.get("historical_context_only"),
        "records": records,
    }


def write_isolation_audit(records: list[dict[str, Any]], *, aborted: str | None) -> None:
    audit_records = []
    for row in records:
        trial = f"{row['condition']}/{row['task_id']}/trial_{row['trial']:03d}"
        leaks = row.get("isolation_leaks") or []
        audit_records.append(
            {
                "trial": trial,
                "condition": row["condition"],
                "task_id": row["task_id"],
                "trial_n": row["trial"],
                "pass": row["score"].get("pass"),
                "failure_class": row["score"].get("failure_class"),
                "contaminated": bool(leaks),
                "isolation_leaks": leaks,
                "isolation_preflight_ok": bool(
                    (row.get("isolation_preflight") or {}).get("ok")
                ),
                "unknown_as_false": row["score"].get("unknown_as_false"),
            }
        )
    _write(
        ROOT / "scoring" / "isolation_audit.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "n": len(audit_records),
            "contaminated_trials": sum(1 for row in audit_records if row["contaminated"]),
            "isolation_leak_runs": sum(1 for row in audit_records if row["isolation_leaks"]),
            "aborted": aborted,
            "records": audit_records,
        },
    )


def write_failure_analysis(records: list[dict[str, Any]]) -> None:
    by_run = {}
    by_cell: dict[str, dict[str, int]] = {}
    classes: dict[str, int] = {}
    for row in records:
        cell = f"{row['condition']}:{row['task_id']}"
        klass = row["score"].get("failure_class") or "PASS"
        by_cell.setdefault(cell, {})
        by_cell[cell][klass] = by_cell[cell].get(klass, 0) + 1
        if row["score"].get("failure_class"):
            classes[klass] = classes.get(klass, 0) + 1
            key = f"{row['condition']}/{row['task_id']}/trial_{row['trial']:03d}"
            indoor = row["score"].get("indoor")
            by_run[key] = {
                "failure_class": klass,
                "indoor": indoor,
            }
    _write(
        ROOT / "scoring" / "failure_analysis.json",
        {
            "failure_classes": classes,
            "unknown_as_false_count": sum(
                1 for row in records if row["score"].get("unknown_as_false")
            ),
            "isolation_leak_runs": sum(1 for row in records if row.get("isolation_leaks")),
            "by_cell": by_cell,
            "by_run": by_run,
        },
    )


def run_campaign() -> dict[str, Any]:
    manifest = verify_manifest()
    if manifest["model"] != MODEL:
        raise RuntimeError("refusing to run a non-composer-2.5 frozen campaign")
    records: list[dict[str, Any]] = []
    aborted = None
    try:
        for condition, task_id, trial in all_runs():
            destination = trial_dir(condition, task_id, trial)
            metrics_path = destination / "metrics.json"
            if metrics_path.exists():
                records.append(json.loads(metrics_path.read_text(encoding="utf-8")))
                if records[-1].get("isolation_leaks"):
                    raise IsolationFailed(
                        f"resume found leak in {condition}/{task_id}/trial_{trial:03d}"
                    )
                continue
            records.append(run_trial(condition, task_id, trial, model=MODEL))
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
    except IsolationFailed as exc:
        aborted = str(exc)
        print(json.dumps({"aborted": aborted}, sort_keys=True), flush=True)
        _write(
            ROOT / "ABORTED.json",
            {
                "experiment_id": EXPERIMENT_ID,
                "reason": aborted,
                "completed_runs": len(records),
            },
        )
    report = aggregate(records, manifest)
    if aborted:
        report["aborted"] = aborted
        report["isolation_held"] = False
    scoring = ROOT / "scoring"
    _write(scoring / "run_scores.json", {"records": records})
    write_failure_analysis(records)
    write_isolation_audit(records, aborted=aborted)
    _write(
        ROOT / "report.json",
        {key: value for key, value in report.items() if key != "records"},
    )
    if aborted:
        raise IsolationFailed(aborted)
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
                    "cost": report["cost"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        path = freeze_manifest()
        print(f"froze {path}")
