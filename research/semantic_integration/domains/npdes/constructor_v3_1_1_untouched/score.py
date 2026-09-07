"""Evaluator scoring for untouched NPDES Constructor v3.1.1. Not visible to constructor workspaces."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
EVAL = NPDES / "fixture" / "evaluator_only"
TRIALS = ROOT / "trials"
GOLD_S_IDS = {
    "time-staged",
    "when-discharging",
    "report-only",
    "no-discharge",
    "special-study",
    "conditional",
    "seasonal",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def snapshot(trial: int, pass_id: str) -> Path:
    return TRIALS / f"T{trial}" / "passes" / pass_id / "workspace_snapshot"


def agent_record(trial: int, pass_id: str) -> dict[str, Any]:
    path = TRIALS / f"T{trial}" / "passes" / pass_id / "agent.json"
    return load_json(path) or {}


def walk_strings(obj: Any) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(walk_strings(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(walk_strings(v) for v in obj)
    return str(obj)


def score_frontier(trial: int) -> dict[str, Any]:
    gold_s = load_json(EVAL / "gold_s.json") or {}
    clauses = gold_s.get("clauses") or []
    obligations = load_json(snapshot(trial, "p3") / "03_obligations.json") or []
    if isinstance(obligations, dict):
        obligations = obligations.get("obligations") or obligations.get("items") or []
    blob = walk_strings(obligations).lower()
    hits = []
    misses = []
    for clause in clauses:
        cid = clause.get("id")
        concept = str(clause.get("concept_governed") or "").lower()
        keys = [cid.lower() if cid else "", concept]
        found = any(token and token in blob for token in keys if len(token) >= 8)
        # concept-level keywords
        keywords = [w for w in concept.replace("/", " ").replace("-", " ").split() if len(w) > 4]
        found = found or (keywords and all(k in blob for k in keywords[:2]))
        record = {"id": cid, "concept": clause.get("concept_governed"), "found": found}
        (hits if found else misses).append(record)
    return {
        "n_obligations": len(obligations) if isinstance(obligations, list) else 0,
        "required_clauses": len(clauses),
        "hits": hits,
        "misses": misses,
        "recall": (len(hits) / len(clauses)) if clauses else None,
    }


def world_stats(world: Path) -> dict[str, Any]:
    if not world.exists():
        return {"missing": True}
    conn = sqlite3.connect(str(world))
    try:
        n_assert = conn.execute("SELECT count(*) FROM _tv_assertions").fetchone()[0]
        n_rel = conn.execute("SELECT count(*) FROM _tv_relations").fetchone()[0]
        by_origin = dict(
            conn.execute("SELECT COALESCE(origin,''), count(*) FROM _tv_assertions GROUP BY 1").fetchall()
        )
        n_ground = conn.execute("SELECT count(*) FROM _tv_groundings").fetchone()[0]
    except sqlite3.Error as exc:
        return {"error": str(exc)}
    finally:
        conn.close()
    return {
        "assertions": n_assert,
        "relations": n_rel,
        "by_origin": by_origin,
        "groundings": n_ground,
    }


def score_trial(trial: int) -> dict[str, Any]:
    passes = {}
    leaks = []
    timeouts = []
    models = []
    for pass_id in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"):
        rec = agent_record(trial, pass_id)
        if not rec:
            continue
        passes[pass_id] = {
            "returncode": rec.get("returncode"),
            "timed_out": rec.get("timed_out"),
            "model": rec.get("model"),
            "reported_model": rec.get("reported_model"),
            "isolation_leaks": rec.get("isolation_leaks") or [],
        }
        leaks.extend(rec.get("isolation_leaks") or [])
        if rec.get("timed_out"):
            timeouts.append(pass_id)
        models.append(rec.get("reported_model") or rec.get("model"))
    p6 = snapshot(trial, "p6")
    p8 = snapshot(trial, "p8")
    vocab = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or load_json(p6 / "01_vocabulary.json")
    relations = vocab.get("relations") if isinstance(vocab, dict) else vocab or []
    provenance = load_json(p6 / "06_provenance.json") or {}
    abi = load_json(p8 / "08_abi_completeness.json") or load_json(p6 / "08_abi_completeness.json") or {}
    dispositions = load_json(snapshot(trial, "p5") / "05_dispositions.json") or []
    if isinstance(dispositions, dict):
        dispositions = dispositions.get("dispositions") or []
    disp_counts = Counter(str(r.get("disposition") or "").upper() for r in dispositions if isinstance(r, dict))
    world = p6 / "06_world" / "world.sqlite"
    if not world.exists():
        world = p6 / "world" / "world.sqlite"
    return {
        "trial": trial,
        "passes": passes,
        "isolation_leaks": leaks,
        "timeouts": timeouts,
        "models": models,
        "n_relations": len(relations) if isinstance(relations, list) else None,
        "world": world_stats(world),
        "provenance": provenance,
        "abi": {
            "ok": abi.get("ok"),
            "satisfied": abi.get("satisfied"),
            "unsatisfied": abi.get("unsatisfied"),
            "ambiguous": abi.get("ambiguous"),
            "unsatisfied_reasons": abi.get("unsatisfied_reasons"),
        },
        "dispositions": dict(disp_counts),
        "frontier": score_frontier(trial),
        "outputs": {
            "a": load_json(p8 / "08_outputs" / "a.json") or load_json(p8 / "purpose_ir" / "a" / "output.json"),
            "b": load_json(p8 / "08_outputs" / "b.json") or load_json(p8 / "purpose_ir" / "b" / "output.json"),
            "c": load_json(p8 / "08_outputs" / "c.json") or load_json(p8 / "purpose_ir" / "c" / "output.json"),
        },
    }


def score_all() -> dict[str, Any]:
    trials = {f"T{i}": score_trial(i) for i in range(1, 6)}
    return {"trials": trials}


if __name__ == "__main__":
    print(json.dumps(score_all(), indent=2)[:4000])
