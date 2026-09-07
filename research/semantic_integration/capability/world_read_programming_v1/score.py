"""Evaluator scoring. Not visible to participants. Does not mutate Worlds."""

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

from research.semantic_integration.capability.world_read_programming_v1.paths import (
    ARMS,
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    PART_A_TRIALS,
    PART_B_TRIALS,
    RUNS,
)


def load_gold() -> dict:
    return json.loads((EVALUATOR_ONLY / "gold.json").read_text(encoding="utf-8"))


def load_questions() -> list[dict]:
    pack = json.loads((EVALUATOR_ONLY / "diagnostic_questions.json").read_text(encoding="utf-8"))
    return list(pack["questions"])


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


def classify_answer(item: dict, spec: dict) -> str:
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


def error_family(qid: str, classification: str, item: dict, spec: dict) -> str | None:
    if classification in {"CORRECT", "UNRESOLVED_CORRECTLY"}:
        return None
    value = item.get("value")
    rationale = str(item.get("rationale") or "").lower()
    family = spec.get("family")
    if qid == "harbor_towing.Q3" and classification == "INCORRECT":
        if normalize_value(value) in {"3"}:
            return "WRONG_GRAIN"
        return "OTHER_REASONING"
    if qid == "harbor_towing.Q6" and classification == "UNSUPPORTED_CLOSURE":
        if normalize_value(value) in {"false", "0", "no"}:
            return "UNRESOLVED_AS_FALSE"
        return "OTHER_REASONING"
    if qid == "seed_grants.Q4" and classification == "UNRESOLVED_INCORRECTLY":
        if "waiver" in rationale:
            return "PROPOSITION_CONTAMINATION"
        return "PROPOSITION_CONTAMINATION"
    if "could not find" in rationale or "no relation" in rationale or "cannot locate" in rationale:
        return "INTERFACE_DISCOVERY"
    if family:
        return family
    return "OTHER_REASONING"


def answers_by_id(payload: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    rows = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return out
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"])] = row
    return out


def score_part_a_trial(arm: str, trial: str) -> dict[str, Any]:
    sealed = RUNS / "part_a" / arm / trial
    summary = json.loads((sealed / "trial.json").read_text(encoding="utf-8")) if (sealed / "trial.json").exists() else {}
    payload = json.loads((sealed / "answers.json").read_text(encoding="utf-8")) if (sealed / "answers.json").exists() else {}
    by_id = answers_by_id(payload)
    gold = load_gold()["part_a"]
    questions = {row["id"]: row for row in load_questions()}
    classifications = {}
    families = {}
    for qid, spec in questions.items():
        gold_spec = {**spec, **gold[qid]}
        item = by_id.get(qid) or {}
        if not item:
            classifications[qid] = "UNRESOLVED_INCORRECTLY" if spec["establishable"] else "UNRESOLVED_CORRECTLY"
        else:
            classifications[qid] = classify_answer(item, gold_spec)
        families[qid] = error_family(qid, classifications[qid], item, spec)
    return {
        **summary,
        "classifications": classifications,
        "error_families": families,
        "answers": by_id,
    }


def ident_set(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, (str, int, float)):
        values = [values]
    out: set[str] = set()
    if isinstance(values, dict):
        values = list(values.keys()) + list(values.values())
    for item in values:
        text = str(item)
        text = text.replace("job:", "").replace("vessel:", "").replace("award:", "")
        text = text.replace("org:", "").replace("checkout:", "").replace("member:", "")
        text = text.replace("tool:", "")
        token = text.split("/")[-1].split()[0].strip(" ,[]\"'")
        if token:
            out.add(token.upper())
    return out


def number_in(blob: Any, expected: float, *, tol: float = 0.01) -> bool:
    text = json.dumps(blob, default=str)
    target = int(expected) if float(expected).is_integer() else expected
    if re.search(rf"(?<![0-9.]){re.escape(str(target))}(?![0-9.])", text):
        return True
    try:
        for match in re.findall(r"-?\d+(?:\.\d+)?", text):
            if abs(float(match) - float(expected)) <= tol:
                return True
    except ValueError:
        return False
    return False


def mapping_match(blob: Any, expected: dict[str, float]) -> tuple[int, int]:
    hits = 0
    text = json.dumps(blob, default=str).upper()
    for key, value in expected.items():
        key_u = key.upper()
        if key_u in text and number_in(blob, value):
            hits += 1
        elif number_in(blob, value):
            hits += 1
    return hits, len(expected)


def classify_program(domain_id: str, task_id: str, item: dict, gold: dict) -> str:
    status = str(item.get("status") or "").upper()
    result = item.get("result")
    handling = str(item.get("unresolved_handling") or "").lower()
    blob = {"result": result, "status": status, "handling": handling, "code": item.get("code")}
    spec = gold[domain_id][task_id]
    if task_id == "P1":
        mapping = spec.get("charges_by_vessel") or spec.get("remaining_by_org") or spec.get("fees_by_tool") or {}
        hits, n = mapping_match(blob, mapping)
        if hits == n:
            return "CORRECT"
        if hits >= max(1, n - 1):
            return "PARTIAL"
        return "INCORRECT"
    if domain_id == "harbor_towing" and task_id == "P2":
        jobs = ident_set(result) | ident_set(blob)
        if ident_set(spec["jobs"]).issubset(jobs) and ident_set(spec["berths"]).issubset(jobs | ident_set(spec["berths"]) & ident_set(json.dumps(result, default=str))):
            text = json.dumps(result, default=str).upper()
            if all(token in text for token in ["J2", "J5", "B4", "B12"]):
                return "CORRECT"
            return "PARTIAL" if "J2" in text and "J5" in text else "INCORRECT"
        text = json.dumps(result, default=str).upper()
        if all(token in text for token in ["J2", "J5", "B4", "B12"]):
            return "CORRECT"
        if "J2" in text and "J5" in text:
            return "PARTIAL"
        return "INCORRECT"
    if domain_id == "seed_grants" and task_id == "P2":
        text = json.dumps(result, default=str).upper()
        need = ["ORG-MEADOW", "A-101", "A-103"]
        if all(token in text for token in need) and number_in(blob, 50000):
            return "CORRECT"
        if all(token in text for token in need):
            return "PARTIAL"
        return "INCORRECT"
    if domain_id == "makerspace_checkout" and task_id == "P2":
        text = json.dumps(result, default=str).upper()
        checks = all(token in text for token in ["C1", "C3", "C6", "C7"])
        tools = "LASER-A" in text and "SAW-1" in text
        if checks and tools:
            return "CORRECT"
        if checks or tools:
            return "PARTIAL"
        return "INCORRECT"
    if task_id == "P3":
        text = json.dumps(blob, default=str).upper()
        handling_l = handling
        closed_false = any(
            token in handling_l or token in json.dumps(result, default=str).lower()
            for token in ["not an emergency", "was not a documented", "false"]
        )
        if domain_id == "harbor_towing":
            jobs_ok = "J5" in text and "J7" in text
            unresolved_ok = jobs_ok and (
                status == "UNRESOLVED"
                or "INSUFFICIENT" in text
                or "UNRESOLVED" in text
                or "CANNOT" in text
            )
            established_empty = (
                number_in(blob, 0)
                or "ESTABLISHED_JOB" in text
                or result in (None, {}, [])
            )
            if closed_false and "FALSE" in text and not unresolved_ok:
                return "UNSUPPORTED_CLOSURE"
            if jobs_ok and unresolved_ok:
                return "CORRECT"
            if jobs_ok:
                return "PARTIAL"
            return "INCORRECT"
        if domain_id == "seed_grants":
            total_ok = number_in(blob, 15000)
            sibling_ok = "A-105" in text
            if "A-104" in text and not sibling_ok:
                return "PARTIAL"
            if total_ok and sibling_ok:
                return "CORRECT"
            if total_ok or sibling_ok:
                return "PARTIAL"
            return "INCORRECT"
        if domain_id == "makerspace_checkout":
            fee_ok = number_in(blob, 108)
            pending_ok = "C5" in text
            if fee_ok and pending_ok:
                return "CORRECT"
            if fee_ok or pending_ok:
                return "PARTIAL"
            return "INCORRECT"
    return "INCORRECT"


def dominant_mechanism(item: dict, agent: dict) -> str:
    code = str(item.get("code") or "").lower()
    shells = "\n".join((agent.get("exploration") or {}).get("shells") or []).lower()
    blob = code + "\n" + shells
    graphish = any(token in blob for token in ["bfs", "dfs", "networkx", "nx.", "reachable", "queue", "stack", "visited"])
    sql_join = " join " in blob or blob.count("select") >= 2
    cte = "with " in blob and "recursive" in blob
    python = "for " in code or "dict" in code or "set(" in code
    if cte:
        return "SQL_RECURSIVE"
    if graphish and python:
        return "PYTHON_GRAPH"
    if sql_join and python:
        return "MIXED_SQL_PYTHON"
    if sql_join:
        return "SQL_MULTI_RELATION"
    if python and ("group" in blob or "sum(" in blob or "join" in blob):
        return "PYTHON_RELATIONAL"
    if "select" in blob and blob.count("select") <= 2 and " join " not in blob:
        return "SINGLE_RELATION_READ"
    if not code and "select" not in blob:
        return "MODEL_SIDE_COMPOSITION"
    return "MIXED_SQL_PYTHON"


def score_part_b_trial(domain_id: str, arm: str, trial: str) -> dict[str, Any]:
    sealed = RUNS / "part_b" / domain_id / arm / trial
    summary = json.loads((sealed / "trial.json").read_text(encoding="utf-8")) if (sealed / "trial.json").exists() else {}
    payload = json.loads((sealed / "answers.json").read_text(encoding="utf-8")) if (sealed / "answers.json").exists() else {}
    gold = load_gold()["part_b"]
    tasks = {}
    if isinstance(payload, dict):
        rows = payload.get("tasks") or payload.get("answers") or []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("id"):
                    tasks[str(row["id"]).upper()] = row
        for key in ("P1", "P2", "P3"):
            if key in payload and key not in tasks:
                tasks[key] = payload[key] if isinstance(payload[key], dict) else {"id": key, "result": payload[key]}
    classifications = {}
    mechanisms = {}
    for task_id in ("P1", "P2", "P3"):
        item = tasks.get(task_id) or {}
        classifications[task_id] = classify_program(domain_id, task_id, item, gold)
        mechanisms[task_id] = dominant_mechanism(item, summary)
    return {
        **summary,
        "classifications": classifications,
        "mechanisms": mechanisms,
        "tasks": tasks,
    }


def aggregate() -> dict[str, Any]:
    part_a = []
    for arm in ARMS:
        for trial in PART_A_TRIALS:
            path = RUNS / "part_a" / arm / trial / "trial.json"
            if path.exists():
                part_a.append(score_part_a_trial(arm, trial))
    part_b = []
    for domain_id in DOMAIN_IDS:
        for arm in ARMS:
            for trial in PART_B_TRIALS:
                path = RUNS / "part_b" / domain_id / arm / trial / "trial.json"
                if path.exists():
                    part_b.append(score_part_b_trial(domain_id, arm, trial))
    return {"part_a": part_a, "part_b": part_b}


def main() -> None:
    payload = aggregate()
    (RUNS / "score.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"n_part_a": len(payload["part_a"]), "n_part_b": len(payload["part_b"])}))


if __name__ == "__main__":
    main()
