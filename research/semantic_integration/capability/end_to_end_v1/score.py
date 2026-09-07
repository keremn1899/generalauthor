"""Evaluator scoring. Not visible to hosts. Does not mutate Worlds."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.capability.end_to_end_v1.paths import (
    CONSTRUCTION_TRIALS,
    CONSUMER_TRIALS,
    DOMAIN_IDS,
    EVALUATOR_ONLY,
    RUNS,
)
from research.semantic_integration.capability.end_to_end_v1.run_campaign import questions_for
from research.semantic_integration.runtime_v0.world import ConstructionWorld


def load_pack() -> dict:
    return json.loads((EVALUATOR_ONLY / "competency_questions.json").read_text(encoding="utf-8"))


def load_est() -> dict:
    return json.loads((EVALUATOR_ONLY / "establishability.json").read_text(encoding="utf-8"))


def dump_world_text(accepted_dir: Path) -> str:
    db = accepted_dir / "world.sqlite"
    if not db.exists():
        return ""
    world = ConstructionWorld.open(db)
    try:
        chunks = [json.dumps(world.admission), json.dumps(world.taskview.describe(), default=str)]
        for name in world.admission:
            try:
                rows = world.query_semantic(f'SELECT * FROM "{name}"')
            except Exception:
                rows = []
            chunks.append(json.dumps({name: rows}, default=str))
        return "\n".join(chunks)
    finally:
        world.close()


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


def construction_inventory(accepted_dir: Path) -> dict[str, Any]:
    db = accepted_dir / "world.sqlite"
    world = ConstructionWorld.open(db)
    try:
        n_assert = world.taskview.query("SELECT COUNT(*) AS n FROM _tv_assertions")[0]["n"]
        n_derived = world.taskview.query(
            "SELECT COUNT(*) AS n FROM _tv_assertions WHERE origin = 'DERIVED'"
        )[0]["n"]
        n_source = world.taskview.query(
            "SELECT COUNT(*) AS n FROM _tv_groundings WHERE kind = 'SOURCE'"
        )[0]["n"]
        failures = []
        if "purpose_requirement_failure" in world.admission:
            failures = world.query_semantic("SELECT * FROM purpose_requirement_failure")
        purpose = {}
        purpose_path = accepted_dir / "world.purpose.json"
        if purpose_path.exists():
            purpose = json.loads(purpose_path.read_text(encoding="utf-8"))
        return {
            "relation_count": len(world.admission),
            "admission": world.admission,
            "n_assertions": n_assert,
            "n_derived": n_derived,
            "n_source_groundings": n_source,
            "n_failures": len(failures),
            "failures": failures[:40],
            "n_requirements": len(purpose.get("requirements") or []),
        }
    finally:
        world.close()


def score_construction_trial(domain_id: str, trial: str) -> dict[str, Any]:
    sealed = RUNS / "construction" / domain_id / trial
    summary = json.loads((sealed / "trial.json").read_text(encoding="utf-8")) if (sealed / "trial.json").exists() else {}
    accepted = sealed / "accepted"
    pack = {row["id"]: row for row in questions_for(domain_id)}
    est = load_est()
    markers = est["unsupported_closure_markers"].get(domain_id) or []
    construction_src = ""
    if (sealed / "construction.py").exists():
        construction_src = (sealed / "construction.py").read_text(encoding="utf-8")
    hardcoded = []
    for spec in pack.values():
        q = spec["question"]
        if q in construction_src:
            hardcoded.append(spec["id"])
        for allowed in spec.get("allowed") or []:
            if spec["establishable"] and str(allowed) in construction_src and spec["id"] in ("Q5", "Q6"):
                hardcoded.append(spec["id"])
    closures = [marker for marker in markers if marker.lower() in construction_src.lower()]
    if not (accepted / "world.sqlite").exists():
        return {
            **summary,
            "build": summary.get("build") or "NO_ACCEPTED_WORLD",
            "coverage": {},
            "unsupported_closure_hits": closures,
            "hardcoded_question_strings": hardcoded,
        }
    blob = dump_world_text(accepted)
    coverage = {}
    for qid, spec in pack.items():
        if spec["establishable"]:
            present = any(str(item) in blob for item in (spec.get("allowed") or []))
            coverage[qid] = "PRESENT" if present else "MISSING"
        else:
            failure_hit = "purpose_requirement_failure" in blob and (
                "UNRESOLVED" in blob or "EXPLICIT_UNRESOLVED" in blob or "UNINTERPRETED" in blob
            )
            invented = any(marker.lower() in blob.lower() for marker in markers)
            if invented:
                coverage[qid] = "UNSUPPORTED"
            elif failure_hit:
                coverage[qid] = "EXPLICITLY_UNRESOLVED"
            else:
                coverage[qid] = "MISSING"
    inventory = construction_inventory(accepted)
    return {
        **summary,
        "build": "ACCEPTED",
        "coverage": coverage,
        "unsupported_closure_hits": closures,
        "hardcoded_question_strings": hardcoded,
        "inventory": inventory,
        "source_independent": True,
    }


def answers_list(payload: dict) -> list[dict]:
    if isinstance(payload.get("answers"), list):
        return payload["answers"]
    return []


def score_consumer(domain_id: str, kind: str, trial: str) -> dict[str, Any]:
    sealed = RUNS / "consumers" / domain_id / kind / trial
    summary = json.loads((sealed / "trial.json").read_text(encoding="utf-8")) if (sealed / "trial.json").exists() else {}
    pack = {row["id"]: row for row in questions_for(domain_id)}
    answers_path = sealed / "answers.json"
    payload = json.loads(answers_path.read_text(encoding="utf-8")) if answers_path.exists() else {}
    by_id = {}
    for row in answers_list(payload):
        if isinstance(row, dict) and row.get("id"):
            by_id[str(row["id"]).upper()] = row
    classifications = {}
    for qid, spec in pack.items():
        item = by_id.get(qid) or {}
        if summary.get("status") == "NO_ACCEPTED_WORLD":
            classifications[qid] = "UNRESOLVED_INCORRECTLY" if spec["establishable"] else "UNRESOLVED_CORRECTLY"
            continue
        if not item:
            classifications[qid] = "UNRESOLVED_INCORRECTLY" if spec["establishable"] else "UNRESOLVED_CORRECTLY"
            continue
        classifications[qid] = classify_answer(item, spec)
    return {**summary, "classifications": classifications, "answers": by_id}


def aggregate() -> dict[str, Any]:
    construction = []
    for domain_id in DOMAIN_IDS:
        for trial in CONSTRUCTION_TRIALS:
            path = RUNS / "construction" / domain_id / trial / "trial.json"
            if path.exists():
                construction.append(score_construction_trial(domain_id, trial))
    consumers = []
    for domain_id in DOMAIN_IDS:
        for kind in ("WORLD", "RAW"):
            for trial in CONSUMER_TRIALS:
                path = RUNS / "consumers" / domain_id / kind / trial / "trial.json"
                if path.exists():
                    consumers.append(score_consumer(domain_id, kind, trial))
    return {"construction": construction, "consumers": consumers}


def main() -> None:
    payload = aggregate()
    (RUNS / "score.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"n_construction": len(payload["construction"]), "n_consumers": len(payload["consumers"])}))


if __name__ == "__main__":
    main()
