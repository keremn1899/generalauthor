"""Resumable E0/E1 campaign. Worlds are not rebuilt."""

from __future__ import annotations

import hashlib
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

from research.semantic_integration.capability.autonomous_world_exploration_v1.agent import run_probe_agent
from research.semantic_integration.capability.autonomous_world_exploration_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.capability.autonomous_world_exploration_v1.paths import (
    ARMS,
    DOMAIN_IDS,
    E0_TIMEOUT,
    E1_ORIENT_TIMEOUT,
    E1_TASK_TIMEOUT,
    EVALUATOR_ONLY,
    HOST_RETRIES,
    RUNS,
    TRIALS,
)
from research.semantic_integration.capability.autonomous_world_exploration_v1.prompts import (
    E0_PROMPT,
    E1_ORIENT_PROMPT,
    E1_TASK_PROMPT,
)
from research.semantic_integration.capability.autonomous_world_exploration_v1.workspaces import (
    reveal_tasks,
    seed_e0,
    seed_e1_orient,
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def downstream_tasks(domain_id: str) -> list[dict]:
    pack = json.loads((EVALUATOR_ONLY / "downstream_tasks.json").read_text(encoding="utf-8"))
    return list(pack["tasks"][domain_id])


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


def surface_metrics(agent: dict) -> dict:
    exploration = agent.get("exploration") or {}
    shells = exploration.get("shells") or []
    blob = "\n".join(shells).lower()
    reads = [str(item).lower() for item in (exploration.get("reads") or [])]
    return {
        "n_reads": exploration.get("n_reads"),
        "n_shells": exploration.get("n_shells"),
        "n_writes": exploration.get("n_writes"),
        "header_rereads": sum(1 for path in reads if path.endswith("header.md")),
        "schema_description_calls": blob.count("describe(") + blob.count("describe()"),
        "select_count": blob.count("select"),
        "join_count": blob.count(" join "),
        "query_semantic_count": blob.count("query_semantic"),
        "grounding_inspections": blob.count("grounding") + blob.count("_tv_ground"),
        "failure_inspections": blob.count("purpose_requirement_failure"),
        "raw_source_reads": [path for path in reads if "sources/" in path],
    }


def expected_hash(domain_id: str) -> str:
    freeze = json.loads((EVALUATOR_ONLY / "freeze.json").read_text(encoding="utf-8"))
    return freeze["worlds_t1_sha256"][domain_id]


def verify_world(live: Path, domain_id: str) -> str:
    digest = sha256_file(live / "world" / "world.sqlite")
    if digest != expected_hash(domain_id):
        raise RuntimeError(f"world hash drift {domain_id}")
    return digest


def run_episode(*, domain_id: str, arm: str, trial: str) -> dict:
    sealed = RUNS / domain_id / arm / trial
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return loadj(summary_path)
    tasks = downstream_tasks(domain_id)
    live = new_live_workspace()
    try:
        if arm == "E0":
            context = seed_e0(live, domain_id=domain_id, tasks=tasks)
            digest = verify_world(live, domain_id)
            dump(sealed / "isolation_preflight.json", preflight_isolation(live))
            dump(sealed / "world_hash.json", {"sha256": digest})
            dump(sealed / "initial_context.json", context)
            shutil.copy2(live / "HEADER.md", sealed / "HEADER.md")
            agent = run_host(sealed / "task", live, E0_PROMPT, timeout=E0_TIMEOUT)
            dump(sealed / "world_hash_after.json", {"sha256": verify_world(live, domain_id)})
            answers = parse_answers(live, agent)
            dump(sealed / "answers.json", answers)
            if (live / "answers.json").exists():
                shutil.copy2(live / "answers.json", sealed / "answers.raw.json")
            summary = {
                "domain": domain_id,
                "arm": arm,
                "trial": trial,
                "status": "ANSWERED",
                "reported_model": agent.get("reported_model"),
                "task_surface": surface_metrics(agent),
                "task_exploration": agent.get("exploration"),
                "task_tools": agent.get("tools"),
                "initial_context": context,
                "finished_at": now(),
            }
            dump(summary_path, summary)
            return summary

        context = seed_e1_orient(live, domain_id=domain_id)
        digest = verify_world(live, domain_id)
        dump(sealed / "isolation_preflight.json", preflight_isolation(live))
        dump(sealed / "world_hash.json", {"sha256": digest})
        dump(sealed / "initial_context.json", context)
        shutil.copy2(live / "HEADER.md", sealed / "HEADER.md")
        if (live / "TASKS.md").exists():
            raise RuntimeError("E1 orientation workspace leaked TASKS.md")
        orient = run_host(sealed / "orient", live, E1_ORIENT_PROMPT, timeout=E1_ORIENT_TIMEOUT)
        if (live / "NOTES.md").exists():
            shutil.copy2(live / "NOTES.md", sealed / "NOTES.md")
        reveal_tasks(live, tasks=tasks)
        task_agent = run_host(sealed / "task", live, E1_TASK_PROMPT, timeout=E1_TASK_TIMEOUT)
        dump(sealed / "world_hash_after.json", {"sha256": verify_world(live, domain_id)})
        answers = parse_answers(live, task_agent)
        dump(sealed / "answers.json", answers)
        if (live / "answers.json").exists():
            shutil.copy2(live / "answers.json", sealed / "answers.raw.json")
        summary = {
            "domain": domain_id,
            "arm": arm,
            "trial": trial,
            "status": "ANSWERED",
            "reported_model": task_agent.get("reported_model"),
            "orient_model": orient.get("reported_model"),
            "orient_surface": surface_metrics(orient),
            "orient_exploration": orient.get("exploration"),
            "orient_tools": orient.get("tools"),
            "task_surface": surface_metrics(task_agent),
            "task_exploration": task_agent.get("exploration"),
            "task_tools": task_agent.get("tools"),
            "initial_context": context,
            "finished_at": now(),
        }
        dump(summary_path, summary)
        return summary
    finally:
        remove_live_workspace(live)


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    wanted = sys.argv[1:] or ["all"]
    out = []
    for domain_id in DOMAIN_IDS:
        for arm in ARMS:
            for trial in TRIALS:
                key = f"{domain_id}/{arm}/{trial}"
                if wanted != ["all"] and not any(token in key for token in wanted):
                    continue
                print(key, flush=True)
                out.append(run_episode(domain_id=domain_id, arm=arm, trial=trial))
    dump(RUNS / "index.json", out)


if __name__ == "__main__":
    main()
