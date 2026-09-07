"""Resumable 5-trial campaign. Composer 2.5 only. Host compiles outside bwrap."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.agent import (
    parse_program_from_stdout,
    run_probe_agent,
)
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.compiler import (
    compile_path,
    public_diagnostics,
)
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.paths import (
    FROZEN,
    MAX_COMPILE_ITERS,
    MODEL,
    N_TRIALS,
    REPORTS,
    RUNS,
)
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.prompts import (
    FIRST_PROMPT,
    REPAIR_PROMPT,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.workspaces import (
    freeze_input_manifest,
    seed_workspace,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def slim_agent(record: dict) -> dict:
    stdout = record.get("stdout") or ""
    return {
        "adapter": record.get("adapter"),
        "model": record.get("model"),
        "reported_model": record.get("reported_model"),
        "returncode": record.get("returncode"),
        "timed_out": record.get("timed_out"),
        "usage": record.get("usage"),
        "tools": record.get("tools"),
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": stdout[-20000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def _capture_program(live: Path, raw: dict) -> dict | None:
    path = live / "program.json"
    if path.exists():
        try:
            from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.compiler import (
                load_program,
            )

            return load_program(path)
        except Exception:
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    return parse_program_from_stdout(raw.get("stdout") or "")


def run_trial(index: int) -> dict:
    sealed = RUNS / f"T{index}"
    sealed.mkdir(parents=True, exist_ok=True)
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))

    live = new_live_workspace()
    iterations: list[dict] = []
    try:
        seed_workspace(live)
        preflight = preflight_isolation(live)
        dump(sealed / "isolation_preflight.json", preflight)
        last_compile: dict | None = None
        for iteration in range(1, MAX_COMPILE_ITERS + 1):
            iter_dir = sealed / f"iter{iteration}"
            iter_dir.mkdir(parents=True, exist_ok=True)
            prompt = FIRST_PROMPT if iteration == 1 else REPAIR_PROMPT
            (iter_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
            raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
            agent = slim_agent(raw)
            dump(iter_dir / "agent.json", agent)
            (iter_dir / "transcript.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
            (iter_dir / "transcript.stderr.txt").write_text((raw.get("stderr") or "")[-80000:], encoding="utf-8")
            if agent["isolation_leaks"]:
                dump(sealed / "LEAK.json", {"leaks": agent["isolation_leaks"]})
                raise RuntimeError(f"isolation leak: {agent['isolation_leaks']}")
            reported = agent.get("reported_model")
            if reported and "composer" not in str(reported).lower():
                dump(sealed / "MODEL_FAIL.json", {"reported_model": reported})
                raise RuntimeError(f"non-Composer model {reported!r}")
            program = _capture_program(live, raw)
            if program is not None:
                dump(live / "program.json", program)
                dump(iter_dir / "program.json", program)
            else:
                dump(iter_dir / "program.json", {"missing": True})
            compile_result = compile_path(live / "program.json", live / "sources")
            public = public_diagnostics(compile_result)
            dump(iter_dir / "diagnostics_public.json", public)
            slim_compile = {
                "ok": compile_result.get("ok"),
                "structurally_valid": compile_result.get("structurally_valid"),
                "errors": compile_result.get("errors"),
                "spine": compile_result.get("spine"),
                "n_trigger_instances": compile_result.get("n_trigger_instances"),
                "n_trigger_groups": compile_result.get("n_trigger_groups"),
                "trigger_groups": compile_result.get("trigger_groups"),
                "relation_row_counts": compile_result.get("relation_row_counts"),
                "referent_counts": compile_result.get("referent_counts"),
            }
            dump(iter_dir / "compile.json", slim_compile)
            dump(iter_dir / "trigger_instances.json", compile_result.get("trigger_instances") or [])
            dump(live / "diagnostics.json", public)
            last_compile = compile_result
            iterations.append(
                {
                    "iteration": iteration,
                    "structurally_valid": bool(compile_result.get("structurally_valid")),
                    "errors": compile_result.get("errors") or [],
                    "n_trigger_groups": compile_result.get("n_trigger_groups"),
                    "n_trigger_instances": compile_result.get("n_trigger_instances"),
                    "timed_out": agent.get("timed_out"),
                    "reported_model": agent.get("reported_model"),
                    "usage": agent.get("usage"),
                }
            )
            if compile_result.get("structurally_valid"):
                break
        accepted = next((row for row in reversed(iterations) if row["structurally_valid"]), None)
        trial = {
            "trial": f"T{index}",
            "model": MODEL,
            "n_iterations": len(iterations),
            "accepted": bool(accepted),
            "iterations": iterations,
            "final": {
                "structurally_valid": bool((last_compile or {}).get("structurally_valid")),
                "errors": (last_compile or {}).get("errors") or [],
                "spine": (last_compile or {}).get("spine") or {},
                "n_trigger_groups": (last_compile or {}).get("n_trigger_groups") or 0,
                "n_trigger_instances": (last_compile or {}).get("n_trigger_instances") or 0,
                "trigger_groups": (last_compile or {}).get("trigger_groups") or [],
                "relation_row_counts": (last_compile or {}).get("relation_row_counts") or {},
                "referent_counts": (last_compile or {}).get("referent_counts") or {},
            },
            "finished_at": now(),
        }
        dump(summary_path, trial)
        if last_compile is not None:
            dump(sealed / "final_compile.json", trial["final"])
        return trial
    finally:
        remove_live_workspace(live)


def freeze_if_needed() -> None:
    manifest_path = FROZEN / "input_manifest.json"
    if not manifest_path.exists():
        dump(manifest_path, freeze_input_manifest())
    REPORTS.mkdir(parents=True, exist_ok=True)
    freeze_md = REPORTS / "triggerability_freeze.md"
    if not freeze_md.exists():
        shutil.copy2(FROZEN / "triggerability.md", freeze_md)


def main() -> None:
    freeze_if_needed()
    trials = []
    for index in range(1, N_TRIALS + 1):
        print(f"=== T{index} ===", flush=True)
        trial = run_trial(index)
        trials.append(trial)
        print(
            f"T{index} valid={trial['final']['structurally_valid']} "
            f"iters={trial['n_iterations']} groups={trial['final']['n_trigger_groups']}",
            flush=True,
        )
    from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.score import score_campaign
    from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.report import write_reports

    scored = score_campaign()
    dump(RUNS / "score.json", scored)
    write_reports(scored)
    print("sealed reports written", flush=True)


if __name__ == "__main__":
    main()
