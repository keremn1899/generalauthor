"""Resumable Part A / Part B campaign. Composer 2.5 only. Worlds are not rebuilt."""

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

from research.semantic_integration.capability.world_read_programming_v1.agent import run_probe_agent
from research.semantic_integration.capability.world_read_programming_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.capability.world_read_programming_v1.paths import (
    ARMS,
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    HOST_RETRIES,
    PART_A_TIMEOUT,
    PART_A_TRIALS,
    PART_B_TIMEOUT,
    PART_B_TRIALS,
    RUNS,
    t1_accepted,
)
from research.semantic_integration.capability.world_read_programming_v1.prompts import (
    PART_A_PROMPT_A0,
    PART_A_PROMPT_A1,
    PART_B_PROMPT_A0,
    PART_B_PROMPT_A1,
)
from research.semantic_integration.capability.world_read_programming_v1.workspaces import (
    seed_part_a,
    seed_part_b,
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


def diagnostic_questions() -> list[dict]:
    pack = json.loads((EVALUATOR_ONLY / "diagnostic_questions.json").read_text(encoding="utf-8"))
    return list(pack["questions"])


def programming_tasks(domain_id: str) -> list[dict]:
    pack = json.loads((EVALUATOR_ONLY / "programming_tasks.json").read_text(encoding="utf-8"))
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
    reads = exploration.get("reads") or []
    return {
        "n_reads": exploration.get("n_reads"),
        "n_shells": exploration.get("n_shells"),
        "n_writes": exploration.get("n_writes"),
        "catalog_calls": sum(
            1
            for item in shells
            if "inspect_world" in item.lower() or "describe(" in item.lower() or "admission" in item.lower()
        ),
        "schema_inspections": blob.count("pragma") + blob.count("sqlite_master") + blob.count("describe"),
        "select_count": blob.count("select"),
        "join_count": blob.count(" join "),
        "cte_count": blob.count("with "),
        "query_semantic_count": blob.count("query_semantic"),
        "inspect_world_calls": sum(1 for item in shells if "inspect_world" in item.lower()),
        "raw_source_reads": [path for path in reads if "sources/" in path or path.endswith(".csv")],
        "n_sql_hint": blob.count("select") + blob.count("query_semantic"),
    }


def verify_world_hashes(live: Path, *, part: str, domain_id: str | None = None) -> dict[str, str]:
    freeze = json.loads((EVALUATOR_ONLY / "freeze.json").read_text(encoding="utf-8"))
    expected = freeze["worlds_t1_sha256"]
    got: dict[str, str] = {}
    if part == "A":
        for domain in DOMAIN_IDS:
            path = live / "worlds" / domain / "world.sqlite"
            got[domain] = sha256_file(path)
            if got[domain] != expected[domain]:
                raise RuntimeError(f"world hash drift {domain}: {got[domain]} != {expected[domain]}")
    else:
        assert domain_id is not None
        path = live / "world" / "world.sqlite"
        got[domain_id] = sha256_file(path)
        if got[domain_id] != expected[domain_id]:
            raise RuntimeError(f"world hash drift {domain_id}")
    return got


def run_part_a_trial(*, arm: str, trial: str) -> dict:
    sealed = RUNS / "part_a" / arm / trial
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return loadj(summary_path)
    questions = diagnostic_questions()
    live = new_live_workspace()
    try:
        context = seed_part_a(live, arm=arm, questions=questions)
        hashes = verify_world_hashes(live, part="A")
        dump(sealed / "isolation_preflight.json", preflight_isolation(live))
        dump(sealed / "world_hashes.json", hashes)
        dump(sealed / "initial_context.json", context)
        prompt = PART_A_PROMPT_A1 if arm == "A1" else PART_A_PROMPT_A0
        agent = run_host(sealed, live, prompt, timeout=PART_A_TIMEOUT)
        dump(sealed / "world_hashes_after.json", verify_world_hashes(live, part="A"))
        answers = parse_answers(live, agent)
        dump(sealed / "answers.json", answers)
        if (live / "answers.json").exists():
            shutil.copy2(live / "answers.json", sealed / "answers.raw.json")
        summary = {
            "part": "A",
            "arm": arm,
            "trial": trial,
            "status": "ANSWERED",
            "reported_model": agent.get("reported_model"),
            "tools": agent.get("tools"),
            "exploration": agent.get("exploration"),
            "surface": surface_metrics(agent),
            "initial_context": context,
            "world_hashes": hashes,
            "finished_at": now(),
        }
        dump(summary_path, summary)
        return summary
    finally:
        remove_live_workspace(live)


def run_part_b_trial(*, domain_id: str, arm: str, trial: str) -> dict:
    sealed = RUNS / "part_b" / domain_id / arm / trial
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return loadj(summary_path)
    if not (t1_accepted(domain_id) / "world.sqlite").exists():
        raise RuntimeError(f"missing frozen T1 world for {domain_id}")
    live = new_live_workspace()
    try:
        context = seed_part_b(live, domain_id=domain_id, arm=arm, tasks=programming_tasks(domain_id))
        hashes = verify_world_hashes(live, part="B", domain_id=domain_id)
        dump(sealed / "isolation_preflight.json", preflight_isolation(live))
        dump(sealed / "world_hashes.json", hashes)
        dump(sealed / "initial_context.json", context)
        prompt = PART_B_PROMPT_A1 if arm == "A1" else PART_B_PROMPT_A0
        agent = run_host(sealed, live, prompt, timeout=PART_B_TIMEOUT)
        dump(sealed / "world_hashes_after.json", verify_world_hashes(live, part="B", domain_id=domain_id))
        answers = parse_answers(live, agent)
        dump(sealed / "answers.json", answers)
        if (live / "answers.json").exists():
            shutil.copy2(live / "answers.json", sealed / "answers.raw.json")
        for name in ("program.py", "query.sql", "p1.py", "p2.py", "p3.py"):
            if (live / name).exists():
                shutil.copy2(live / name, sealed / name)
        summary = {
            "part": "B",
            "domain": domain_id,
            "arm": arm,
            "trial": trial,
            "status": "ANSWERED",
            "reported_model": agent.get("reported_model"),
            "tools": agent.get("tools"),
            "exploration": agent.get("exploration"),
            "surface": surface_metrics(agent),
            "initial_context": context,
            "world_hashes": hashes,
            "finished_at": now(),
        }
        dump(summary_path, summary)
        return summary
    finally:
        remove_live_workspace(live)


def run_part_a() -> list[dict]:
    out = []
    for arm in ARMS:
        for trial in PART_A_TRIALS:
            print(f"part_a {arm} {trial}", flush=True)
            out.append(run_part_a_trial(arm=arm, trial=trial))
    dump(RUNS / "part_a_index.json", out)
    return out


def run_part_b() -> list[dict]:
    out = []
    for domain_id in DOMAIN_IDS:
        for arm in ARMS:
            for trial in PART_B_TRIALS:
                print(f"part_b {domain_id} {arm} {trial}", flush=True)
                out.append(run_part_b_trial(domain_id=domain_id, arm=arm, trial=trial))
    dump(RUNS / "part_b_index.json", out)
    return out


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in {"part_a", "a", "all"}:
        run_part_a()
    if mode in {"part_b", "b", "all"}:
        run_part_b()


if __name__ == "__main__":
    main()
