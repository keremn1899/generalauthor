"""Evaluator scoring. Not visible to participants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.capability.autonomous_world_exploration_v1.paths import (
    ARMS,
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    RUNS,
    TRIALS,
)


def load_gold() -> dict:
    return json.loads((EVALUATOR_ONLY / "gold.json").read_text(encoding="utf-8"))


def load_targets() -> dict:
    return json.loads((EVALUATOR_ONLY / "discovery_targets.json").read_text(encoding="utf-8"))


def load_tasks() -> dict:
    return json.loads((EVALUATOR_ONLY / "downstream_tasks.json").read_text(encoding="utf-8"))


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return str(value)
    text = str(value).strip()
    try:
        number = float(text.replace(",", ""))
        if number.is_integer():
            return str(int(number))
        return str(number)
    except ValueError:
        return text.lower()


def allowed_match(value: Any, allowed: list[Any] | None) -> bool:
    if allowed is None:
        return False
    got = normalize_value(value)
    return any(got == normalize_value(item) for item in allowed)


def classify_simple(item: dict, spec: dict) -> str:
    status = str(item.get("status") or "").upper()
    value = item.get("value")
    establishable = bool(spec["establishable"])
    if establishable:
        if status == "UNRESOLVED":
            return "UNRESOLVED_INCORRECTLY"
        if allowed_match(value, spec.get("allowed")):
            return "CORRECT"
        return "INCORRECT"
    if status == "UNRESOLVED" or value in (None, "", "unknown"):
        return "UNRESOLVED_CORRECTLY"
    return "UNSUPPORTED_CLOSURE"


def text_has_all(blob: str, tokens: list[str]) -> bool:
    return all(token.lower() in blob for token in tokens)


def score_discovery(blob: str, target: dict) -> str:
    lowered = blob.lower()
    for group in target.get("cues_misinterpreted") or []:
        if group and text_has_all(lowered, group):
            return "MISINTERPRETED"
    for group in target.get("cues_discovered") or []:
        if group and text_has_all(lowered, group):
            return "DISCOVERED"
    for group in target.get("cues_partial") or []:
        if group and text_has_all(lowered, group):
            return "PARTIAL"
    return "NOT_DISCOVERED"


def structured_ok(tid: str, item: dict, spec: dict) -> bool:
    blob = json.dumps({"value": item.get("value"), "rationale": item.get("rationale")}, default=str).upper()
    if tid == "T3" and "jobs" in spec:
        return all(token in blob for token in spec["jobs"]) and all(token in blob for token in spec["berths"])
    if tid == "T3" and "organization" in spec:
        return spec["organization"].upper() in blob and all(token in blob for token in spec["awards"])
    if tid == "T3" and "tools" in spec:
        return all(token in blob for token in spec["tools"])
    return False


def classify_task(tid: str, item: dict, spec: dict) -> str:
    if spec.get("allowed") is not None or spec.get("establishable") is False:
        result = classify_simple(item, spec)
        if result == "INCORRECT" and tid == "T4" and allowed_match(item.get("value"), spec.get("grain_wrong") or []):
            return "INCORRECT"
        return result
    status = str(item.get("status") or "").upper()
    if spec["establishable"] is False:
        return classify_simple(item, spec)
    if status == "UNRESOLVED":
        return "UNRESOLVED_INCORRECTLY"
    return "CORRECT" if structured_ok(tid, item, spec) else "INCORRECT"


def error_tag(tid: str, kind: str, classification: str, item: dict) -> str | None:
    if classification in {"CORRECT", "UNRESOLVED_CORRECTLY"}:
        return None
    if kind == "grain" and classification == "INCORRECT":
        return "GRAIN_ERROR"
    if kind == "unresolved" and classification == "UNSUPPORTED_CLOSURE":
        if normalize_value(item.get("value")) in {"false", "0", "no"}:
            return "UNRESOLVED_AS_FALSE"
        return "UNSUPPORTED_CLOSURE"
    if classification == "UNRESOLVED_INCORRECTLY" and tid == "T4":
        return "PROPOSITION_CONTAMINATION"
    return classification


def answers_by_id(payload: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    rows = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return out
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"]).upper()] = row
    return out


def classify_ops(agent_or_summary: dict) -> dict[str, int]:
    exploration = agent_or_summary.get("exploration") or agent_or_summary.get("task_exploration") or {}
    shells = "\n".join(exploration.get("shells") or []).lower()
    reads = "\n".join(exploration.get("reads") or []).lower()
    blob = shells + "\n" + reads
    return {
        "catalog_schema": int("describe" in blob or "admission" in blob or "sqlite_master" in blob or "pragma" in blob),
        "sample_rows": int("select *" in blob or "limit " in blob),
        "filtered_read": int(" where " in blob),
        "join_hypothesis": int(" join " in blob),
        "multi_relation_sql": int(blob.count("select") >= 2 or " join " in blob),
        "aggregate": int(any(token in blob for token in ["sum(", "count(", "group by"])),
        "python_exploration": int("constructionworld" in blob or "python3" in blob),
        "grounding_inspection": int("grounding" in blob or "_tv_ground" in blob),
        "failure_state": int("purpose_requirement_failure" in blob),
    }


def orient_blob(sealed: Path) -> str:
    chunks: list[str] = []
    notes = sealed / "NOTES.md"
    if notes.exists():
        chunks.append(notes.read_text(encoding="utf-8"))
    agent_path = sealed / "orient" / "host.agent.json"
    if agent_path.exists():
        agent = json.loads(agent_path.read_text(encoding="utf-8"))
        chunks.append(str(agent.get("assistant_text") or ""))
        chunks.append(json.dumps(agent.get("exploration") or {}, default=str))
    return "\n".join(chunks)


def score_episode(domain_id: str, arm: str, trial: str) -> dict[str, Any]:
    sealed = RUNS / domain_id / arm / trial
    summary = json.loads((sealed / "trial.json").read_text(encoding="utf-8")) if (sealed / "trial.json").exists() else {}
    payload = json.loads((sealed / "answers.json").read_text(encoding="utf-8")) if (sealed / "answers.json").exists() else {}
    by_id = answers_by_id(payload)
    gold = load_gold()["downstream"][domain_id]
    tasks = {row["id"]: row for row in load_tasks()["tasks"][domain_id]}
    classifications = {}
    tags = {}
    for tid, meta in tasks.items():
        spec = {**meta, **gold[tid]}
        item = by_id.get(tid) or {}
        classifications[tid] = classify_task(tid, item, spec)
        tags[tid] = error_tag(tid, meta["kind"], classifications[tid], item)
    discovery = {}
    if arm == "E1":
        blob = orient_blob(sealed)
        for target in load_targets()["targets"][domain_id]:
            discovery[target["id"]] = score_discovery(blob, target)
    task_agent = {}
    task_path = sealed / "task" / "host.agent.json"
    if task_path.exists():
        task_agent = json.loads(task_path.read_text(encoding="utf-8"))
    orient_ops = {}
    if arm == "E1" and (sealed / "orient" / "host.agent.json").exists():
        orient_ops = classify_ops(json.loads((sealed / "orient" / "host.agent.json").read_text(encoding="utf-8")))
    return {
        **summary,
        "classifications": classifications,
        "error_tags": tags,
        "discovery": discovery,
        "task_ops": classify_ops(task_agent),
        "orient_ops": orient_ops,
        "answers": by_id,
    }


def aggregate() -> dict[str, Any]:
    episodes = []
    for domain_id in DOMAIN_IDS:
        for arm in ARMS:
            for trial in TRIALS:
                path = RUNS / domain_id / arm / trial / "trial.json"
                if path.exists():
                    episodes.append(score_episode(domain_id, arm, trial))
    return {"episodes": episodes}


def main() -> None:
    payload = aggregate()
    (RUNS / "score.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"n": len(payload["episodes"])}))


if __name__ == "__main__":
    main()
