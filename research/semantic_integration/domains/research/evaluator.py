"""Deterministic evaluator. No inference. Hidden artifacts stay sealed from the constructor."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
HIDDEN = ROOT / "hidden"
ABC_WORKSPACE = ROOT / "constructor_run" / "abc" / "workspace"
D_WORKSPACE = ROOT / "constructor_run" / "d" / "workspace"
D_WORLD_ONLY = ROOT / "constructor_run" / "d_world_only" / "workspace"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _pub(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def score_purpose_a(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {
        (row.get("registry_id"), _pub(row.get("publication_id")), row.get("correspondence"))
        for row in actual.get("studies") or []
    }
    want = {
        (row["registry_id"], _pub(row.get("publication_id")), row["correspondence"])
        for row in expected["studies"]
    }
    return {
        "pass": got == want,
        "missing": sorted(want - got, key=str),
        "extra": sorted(got - want, key=str),
    }


def _link_key(row: dict) -> tuple[str, str, str]:
    left = str(row.get("left") or "")
    right = str(row.get("right") or "")
    a, b = sorted((left, right))
    return (a, b, str(row.get("epistemic") or ""))


def score_purpose_b(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {_link_key(row) for row in actual.get("links") or []}
    want = {_link_key(row) for row in expected["links"]}
    required_unresolved = {
        tuple(sorted((row["left"], row["right"])))
        for row in expected["links"]
        if row["epistemic"] == "UNRESOLVED"
    }
    got_unresolved = {
        (left, right) for left, right, epistemic in got if epistemic == "UNRESOLVED"
    }
    distinct_violations = []
    for row in expected["links"]:
        if row["epistemic"] != "DISTINCT":
            continue
        a, b = sorted((row["left"], row["right"]))
        if (a, b, "SAME_STUDY") in got:
            distinct_violations.append((a, b))
    return {
        "pass": got == want,
        "missing": sorted(want - got, key=str),
        "extra": sorted(got - want, key=str),
        "unresolved_missing": sorted(required_unresolved - got_unresolved, key=str),
        "distinct_asserted_same": distinct_violations,
        "required_covered": want <= got and not distinct_violations,
    }


def score_purpose_c(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {
        (row.get("registry_id"), _pub(row.get("dataset_id")), row.get("status"))
        for row in actual.get("studies") or []
    }
    want = {
        (row["registry_id"], _pub(row.get("dataset_id")), row["status"])
        for row in expected["studies"]
    }
    return {
        "pass": got == want,
        "missing": sorted(want - got, key=str),
        "extra": sorted(got - want, key=str),
    }


def score_purpose_d(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    if actual.get("insufficient_world"):
        return {
            "pass": False,
            "reason": "insufficient_world",
            "detail": actual.get("reason"),
        }
    got = {
        (
            row.get("registry_id"),
            _pub(row.get("publication_id")),
            _pub(row.get("dataset_id")),
            row.get("status"),
        )
        for row in actual.get("cases") or []
    }
    want = {
        (
            row["registry_id"],
            _pub(row.get("publication_id")),
            _pub(row.get("dataset_id")),
            row["status"],
        )
        for row in expected["cases"]
    }
    return {
        "pass": got == want,
        "missing": sorted(want - got, key=str),
        "extra": sorted(got - want, key=str),
    }


def inspect_world(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        referents = db.execute("SELECT COUNT(*) FROM _tv_referents").fetchone()[0]
        relations = [
            dict(row)
            for row in db.execute(
                "SELECT name, description, mode FROM _tv_relations ORDER BY name"
            )
        ]
        assertions = db.execute("SELECT COUNT(*) FROM _tv_assertions").fetchone()[0]
        grounded = db.execute(
            """
            SELECT COUNT(DISTINCT subject_id) FROM _tv_groundings
            WHERE subject_type = 'ASSERTION'
            """
        ).fetchone()[0]
        base_assertions = db.execute(
            """
            SELECT COUNT(*) FROM _tv_assertions a
            JOIN _tv_relations r ON r.name = a.relation_name
            WHERE r.mode = 'BASE'
            """
        ).fetchone()[0]
        base_grounded = db.execute(
            """
            SELECT COUNT(DISTINCT a.assertion_id) FROM _tv_assertions a
            JOIN _tv_relations r ON r.name = a.relation_name
            JOIN _tv_groundings g
              ON g.subject_type = 'ASSERTION' AND g.subject_id = a.assertion_id
            WHERE r.mode = 'BASE'
            """
        ).fetchone()[0]
        ungrounded_base = db.execute(
            """
            SELECT COUNT(*) FROM _tv_assertions a
            JOIN _tv_relations r ON r.name = a.relation_name
            WHERE r.mode = 'BASE'
              AND NOT EXISTS (
                SELECT 1 FROM _tv_groundings g
                WHERE g.subject_type = 'ASSERTION' AND g.subject_id = a.assertion_id
              )
            """
        ).fetchone()[0]
        derived_assertions = assertions - base_assertions
        return {
            "exists": True,
            "referents": referents,
            "relations": relations,
            "relation_count": len(relations),
            "assertions": assertions,
            "grounded_assertions": grounded,
            "base_assertions": base_assertions,
            "base_grounded": base_grounded,
            "ungrounded_base": ungrounded_base,
            "derived_assertions": derived_assertions,
        }
    finally:
        db.close()


def classify_a_failures(score: dict[str, Any], annotations: dict) -> list[dict]:
    causes = []
    expected = {
        (row["registry_id"], _pub(row.get("publication_id"))): row["disposition"]
        for row in annotations.get("outcome_correspondence") or []
    }
    for item in score.get("missing") or []:
        registry_id, publication_id, correspondence = item
        gold = expected.get((registry_id, publication_id))
        causes.append(
            {
                "kind": "purpose_a_mismatch",
                "row": item,
                "gold_outcome_disposition": gold,
                "semantic_cause": (
                    "unresolved_identity_or_correspondence_dropped_or_wrong"
                    if correspondence == "unresolved"
                    else "outcome_correspondence_or_identity_error"
                ),
            }
        )
    return causes


def classify_b_failures(score: dict[str, Any]) -> list[dict]:
    causes = []
    for item in score.get("unresolved_missing") or []:
        causes.append(
            {
                "kind": "identity_unresolved_not_preserved",
                "row": item,
                "semantic_cause": "cross_authority_identity",
            }
        )
    for item in score.get("distinct_asserted_same") or []:
        causes.append(
            {
                "kind": "distinct_collapsed_to_same",
                "row": item,
                "semantic_cause": "cross_authority_identity",
            }
        )
    for item in score.get("missing") or []:
        if item[2] == "UNRESOLVED":
            continue
        causes.append(
            {
                "kind": "identity_link_missing_or_wrong",
                "row": item,
                "semantic_cause": "cross_authority_identity",
            }
        )
    return causes


def classify_c_failures(score: dict[str, Any]) -> list[dict]:
    causes = []
    for item in score.get("missing") or []:
        registry_id, dataset_id, status = item
        if status == "unresolved":
            cause = "study_or_dataset_identity_unresolved_not_preserved"
        elif status == "insufficient":
            cause = "measurement_correspondence_collapsed_or_ignored"
        else:
            cause = "measurement_or_identity_error"
        causes.append(
            {
                "kind": "purpose_c_mismatch",
                "row": item,
                "semantic_cause": cause,
            }
        )
    return causes


def evaluate_abc() -> dict[str, Any]:
    expected_a = load_json(HIDDEN / "expected" / "purpose_a.json")
    expected_b = load_json(HIDDEN / "expected" / "purpose_b.json")
    expected_c = load_json(HIDDEN / "expected" / "purpose_c.json")
    annotations = load_json(HIDDEN / "annotations" / "dispositions.json") or {}
    workspace = ABC_WORKSPACE
    actual_a = load_json(workspace / "purpose_ir" / "a" / "output.json")
    actual_b = load_json(workspace / "purpose_ir" / "b" / "output.json")
    actual_c = load_json(workspace / "purpose_ir" / "c" / "output.json")
    world = workspace / "world" / "world.sqlite"
    vocab = load_json(workspace / "construction" / "vocabulary.json")
    obligations = load_json(workspace / "world" / "obligations.json")
    if obligations is None:
        obligations = load_json(workspace / "construction" / "semantic_frontier" / "obligations.json")
    score_a = score_purpose_a(actual_a, expected_a)
    score_b = score_purpose_b(actual_b, expected_b)
    score_c = score_purpose_c(actual_c, expected_c)
    world_info = inspect_world(world)
    vocab_rows = vocab if isinstance(vocab, list) else (vocab or {}).get("relations") or []
    world_rels = [
        row.get("name")
        for row in vocab_rows
        if str(row.get("admission") or "").upper() == "WORLD"
    ]
    purpose_rels = [
        row.get("name")
        for row in vocab_rows
        if str(row.get("admission") or "").upper() == "PURPOSE"
    ]
    mechanical = [
        row.get("name")
        for row in vocab_rows
        if str(row.get("construction") or row.get("construction_class") or "").upper()
        == "MECHANICAL"
    ]
    semantic = [
        row.get("name")
        for row in vocab_rows
        if str(row.get("construction") or row.get("construction_class") or "").upper()
        == "SEMANTIC"
    ]
    return {
        "label": "PRE_REPAIR_CONSTRUCTOR_BASELINE",
        "purpose_a": score_a,
        "purpose_b": score_b,
        "purpose_c": score_c,
        "failure_causes": {
            "a": classify_a_failures(score_a, annotations),
            "b": classify_b_failures(score_b),
            "c": classify_c_failures(score_c),
        },
        "world_sqlite": world.exists(),
        "world_fingerprint": sha256_file(world),
        "world_inspect": world_info,
        "vocabulary": vocab,
        "vocabulary_split": {
            "world": world_rels,
            "purpose": purpose_rels,
            "mechanical": mechanical,
            "semantic": semantic,
        },
        "obligations": obligations,
        "obligation_count": len(obligations) if isinstance(obligations, list) else None,
        "d_present_in_workspace": (workspace / "purpose_ir" / "d").exists()
        or (workspace / "purposes" / "visible_d.md").exists(),
    }


def evaluate_d() -> dict[str, Any]:
    expected = load_json(HIDDEN / "expected" / "purpose_d.json")
    actual = load_json(D_WORKSPACE / "purpose_ir" / "d" / "output.json")
    abc_fp = sha256_file(ABC_WORKSPACE / "world" / "world.sqlite")
    d_fp = sha256_file(D_WORKSPACE / "world" / "world.sqlite")
    return {
        "purpose_d": score_purpose_d(actual, expected),
        "abc_world_fingerprint": abc_fp,
        "d_world_fingerprint": d_fp,
        "world_unchanged": abc_fp is not None and abc_fp == d_fp,
        "d_world_inspect": inspect_world(D_WORKSPACE / "world" / "world.sqlite"),
    }


def evaluate_d_world_only() -> dict[str, Any]:
    expected = load_json(HIDDEN / "expected" / "purpose_d.json")
    actual = load_json(D_WORLD_ONLY / "purpose_ir" / "d" / "output.json")
    agent = load_json(ROOT / "constructor_run" / "d_world_only" / "agent.json") or {}
    return {
        "purpose_d_world_only": score_purpose_d(actual, expected),
        "world_mutated": agent.get("world_mutated"),
        "world_fingerprint_before": agent.get("world_fingerprint_before"),
        "world_fingerprint_after": agent.get("world_fingerprint_after"),
        "sources_present": bool(list(D_WORLD_ONLY.rglob("study_registry.csv")))
        if D_WORLD_ONLY.exists()
        else None,
    }


def evaluate_all() -> dict[str, Any]:
    payload = evaluate_abc()
    if (D_WORKSPACE / "purpose_ir" / "d" / "output.json").exists():
        payload["heldout_d"] = evaluate_d()
    if (D_WORLD_ONLY / "purpose_ir" / "d" / "output.json").exists():
        payload["d_world_only"] = evaluate_d_world_only()
    return payload


if __name__ == "__main__":
    print(json.dumps(evaluate_all(), indent=2, sort_keys=True))
