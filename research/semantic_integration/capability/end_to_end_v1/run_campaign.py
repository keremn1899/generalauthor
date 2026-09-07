"""Resumable construction + consumer campaign. Composer 2.5 only."""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.capability.end_to_end_v1.agent import run_probe_agent
from research.semantic_integration.capability.end_to_end_v1.execute import execute_project, snapshot_accepted
from research.semantic_integration.capability.end_to_end_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.capability.end_to_end_v1.paths import (
    CONSTRUCTION_TRIALS,
    CONSUMER_TIMEOUT_SECONDS,
    CONSUMER_TRIALS,
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    HOST_RETRIES,
    MAX_CONSTRUCT_ITERS,
    RUNS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.capability.end_to_end_v1.prompts import (
    CONSUMER_RAW_TASK,
    CONSUMER_WORLD_TASK,
    FIRST_PROMPT,
    REPAIR_PROMPT,
)
from research.semantic_integration.capability.end_to_end_v1.workspaces import (
    seed_construction_workspace,
    seed_raw_consumer,
    seed_world_consumer,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def loadj(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def questions_for(domain_id: str) -> list[dict]:
    pack = json.loads((EVALUATOR_ONLY / "competency_questions.json").read_text(encoding="utf-8"))
    return list(pack["questions"][domain_id])


def slim_agent(record: dict) -> dict:
    return {
        "adapter": record.get("adapter"),
        "model": record.get("model"),
        "reported_model": record.get("reported_model"),
        "returncode": record.get("returncode"),
        "timed_out": record.get("timed_out"),
        "usage": record.get("usage"),
        "tools": record.get("tools"),
        "exploration": record.get("exploration"),
        "assistant_text": (record.get("assistant_text") or "")[-40000:],
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": (record.get("stdout") or "")[-15000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def agent_failure(agent: dict) -> str | None:
    if agent.get("isolation_leaks"):
        return f"leak:{agent['isolation_leaks']}"
    reported = agent.get("reported_model")
    blob = f"{agent.get('stderr_tail') or ''} {agent.get('stdout_tail') or ''}"
    lowered = blob.lower()
    if "cannot use this model" in lowered or "[unavailable]" in lowered:
        return "model_unavailable"
    if agent.get("timed_out"):
        return "timeout"
    if not reported:
        return "missing_reported_model"
    if "composer" not in str(reported).lower():
        return f"non_composer:{reported}"
    return None


def run_host(sealed: Path, live: Path, prompt: str, *, timeout: int) -> dict:
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / "host.prompt.txt").write_text(prompt, encoding="utf-8")
    last: dict | None = None
    fail = "unknown"
    agent: dict = {}
    for attempt in range(1, HOST_RETRIES + 1):
        try:
            raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=timeout)
            agent = slim_agent(raw)
            agent["attempt"] = attempt
            last = agent
            fail = agent_failure(agent) or ""
            dump(sealed / "host.agent.json", agent)
            (sealed / "host.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
            (sealed / "host.stderr.txt").write_text((raw.get("stderr") or "")[-80000:], encoding="utf-8")
        except RuntimeError as exc:
            msg = str(exc)
            agent = {
                "attempt": attempt,
                "reported_model": None,
                "timed_out": False,
                "stderr_tail": msg,
                "stdout_tail": "",
                "isolation_leaks": [],
            }
            last = agent
            lowered = msg.lower()
            if "cannot use this model" in lowered or "[unavailable]" in lowered or "none" in lowered:
                fail = "model_unavailable"
            elif "non-cursor" in lowered or "non-composer" in lowered:
                fail = f"non_composer:{msg}"
            else:
                fail = f"agent_error:{msg[:240]}"
            dump(sealed / f"host.attempt{attempt}.json", {"failure": fail, "error": msg})
        if not fail:
            return agent
        dump(sealed / f"host.attempt{attempt}.json", {"failure": fail, "stderr_tail": agent.get("stderr_tail")})
        if fail.startswith("leak:") or fail.startswith("non_composer:"):
            break
        time.sleep(min(120, 25 * attempt))
    raise RuntimeError(f"host agent failure: {agent_failure(last or {}) or fail}")


def run_construction_trial(domain_id: str, trial: str) -> dict:
    sealed = RUNS / "construction" / domain_id / trial
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return loadj(summary_path)
    sealed.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    iterations: list[dict] = []
    last_exec: dict | None = None
    try:
        seed_construction_workspace(live, domain_id)
        dump(sealed / "isolation_preflight.json", preflight_isolation(live))
        for iteration in range(1, MAX_CONSTRUCT_ITERS + 1):
            iter_dir = sealed / f"iter{iteration}"
            iter_dir.mkdir(parents=True, exist_ok=True)
            prompt = FIRST_PROMPT if iteration == 1 else REPAIR_PROMPT
            agent = run_host(iter_dir, live, prompt, timeout=TIMEOUT_SECONDS)
            if (live / "construction.py").exists():
                shutil.copy2(live / "construction.py", iter_dir / "construction.py")
            executed = execute_project(live)
            dump(iter_dir / "execute.json", executed)
            if (live / "diagnostics.json").exists():
                shutil.copy2(live / "diagnostics.json", iter_dir / "diagnostics.json")
            last_exec = executed
            iterations.append(
                {
                    "iteration": iteration,
                    "reported_model": agent.get("reported_model"),
                    "accepted": bool(executed.get("accepted")),
                    "reason": executed.get("reason"),
                    "errors": executed.get("errors"),
                }
            )
            if executed.get("accepted"):
                snapshot_accepted(live, sealed / "accepted")
                if (live / "construction.py").exists():
                    shutil.copy2(live / "construction.py", sealed / "construction.py")
                if (live / "relation_inventory.json").exists():
                    shutil.copy2(live / "relation_inventory.json", sealed / "relation_inventory.json")
                break
        summary = {
            "domain": domain_id,
            "trial": trial,
            "build": "ACCEPTED" if last_exec and last_exec.get("accepted") else "NO_ACCEPTED_WORLD",
            "attempts": len(iterations),
            "iterations": iterations,
            "finished_at": now(),
        }
        dump(summary_path, summary)
        return summary
    finally:
        remove_live_workspace(live)


def first_accepted_world(domain_id: str) -> Path | None:
    for trial in CONSTRUCTION_TRIALS:
        accepted = RUNS / "construction" / domain_id / trial / "accepted" / "world.sqlite"
        if accepted.exists():
            return accepted.parent
    return None


def parse_answers(workspace: Path, agent: dict) -> dict:
    path = workspace / "answers.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"_parse_error": True, "raw": path.read_text(encoding="utf-8")[:8000]}
    text = agent.get("assistant_text") or ""
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {"_missing": True}


def run_consumer(*, domain_id: str, kind: str, trial: str) -> dict:
    sealed = RUNS / "consumers" / domain_id / kind / trial
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return loadj(summary_path)
    questions = questions_for(domain_id)
    live = new_live_workspace()
    try:
        if kind == "WORLD":
            accepted = first_accepted_world(domain_id)
            if accepted is None:
                summary = {
                    "domain": domain_id,
                    "kind": kind,
                    "trial": trial,
                    "status": "NO_ACCEPTED_WORLD",
                    "finished_at": now(),
                }
                dump(summary_path, summary)
                return summary
            seed_world_consumer(live, domain_id=domain_id, accepted=accepted, questions=questions)
            prompt = (
                "Read CONSUMER.md, purpose.txt, and QUESTIONS.md. "
                "Inspect the World with python3 inspect_world.py and SQL/Python. "
                "Write answers.json for Q1–Q6. No raw sources."
            )
        else:
            seed_raw_consumer(live, domain_id=domain_id, questions=questions)
            prompt = (
                "Read CONSUMER.md, purpose.txt, QUESTIONS.md, and sources/. "
                "Write answers.json for Q1–Q6. Do not guess unsupported facts."
            )
        dump(sealed / "isolation_preflight.json", preflight_isolation(live))
        agent = run_host(sealed, live, prompt, timeout=CONSUMER_TIMEOUT_SECONDS)
        answers = parse_answers(live, agent)
        dump(sealed / "answers.json", answers)
        if (live / "answers.json").exists():
            shutil.copy2(live / "answers.json", sealed / "answers.raw.json")
        summary = {
            "domain": domain_id,
            "kind": kind,
            "trial": trial,
            "status": "ANSWERED",
            "reported_model": agent.get("reported_model"),
            "tools": agent.get("tools"),
            "exploration": agent.get("exploration"),
            "n_sql_hint": _count_sql(agent),
            "finished_at": now(),
        }
        dump(summary_path, summary)
        return summary
    finally:
        remove_live_workspace(live)


def _count_sql(agent: dict) -> int:
    shells = (agent.get("exploration") or {}).get("shells") or []
    blob = " ".join(shells).lower()
    return blob.count("select") + blob.count("query_semantic")


def run_all_construction() -> list[dict]:
    out = []
    for domain_id in DOMAIN_IDS:
        for trial in CONSTRUCTION_TRIALS:
            print(f"construction {domain_id} {trial}", flush=True)
            out.append(run_construction_trial(domain_id, trial))
    dump(RUNS / "construction_index.json", out)
    return out


def run_all_consumers() -> list[dict]:
    out = []
    for domain_id in DOMAIN_IDS:
        for kind in ("WORLD", "RAW"):
            for trial in CONSUMER_TRIALS:
                print(f"consumer {domain_id} {kind} {trial}", flush=True)
                out.append(run_consumer(domain_id=domain_id, kind=kind, trial=trial))
    dump(RUNS / "consumer_index.json", out)
    return out


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in {"construction", "all"}:
        run_all_construction()
    if mode in {"consumers", "all"}:
        run_all_consumers()


if __name__ == "__main__":
    main()
