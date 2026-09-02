"""Deterministic evaluator. No inference. Hidden artifacts stay sealed from the constructor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
HIDDEN = ROOT / "hidden"
ABC_WORKSPACE = ROOT / "constructor_run" / "abc" / "workspace"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def score_purpose_a(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {
        (
            row.get("invoice_id"),
            row.get("contract_id"),
            row.get("association"),
        )
        for row in actual.get("invoices") or []
    }
    want = {
        (row["invoice_id"], row["contract_id"], row["association"])
        for row in expected["invoices"]
    }
    return {
        "pass": got == want,
        "missing": sorted(want - got),
        "extra": sorted(got - want),
    }


def score_purpose_b(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {
        (row.get("left"), row.get("right"), row.get("epistemic"))
        for row in actual.get("links") or []
    }
    want = {
        (row["left"], row["right"], row["epistemic"]) for row in expected["links"]
    }
    required_unresolved = {
        (row["left"], row["right"])
        for row in expected["links"]
        if row["epistemic"] == "UNRESOLVED"
    }
    got_unresolved = {
        (left, right) for left, right, epistemic in got if epistemic == "UNRESOLVED"
    }
    distinct_ok = all(
        (row["left"], row["right"], "SAME_ENTITY") not in got
        for row in expected["links"]
        if row["epistemic"] == "DISTINCT"
    )
    return {
        "pass": required_unresolved <= got_unresolved and want <= got and distinct_ok,
        "missing_required": sorted(want - got),
        "unresolved_missing": sorted(required_unresolved - got_unresolved),
        "extra": sorted(got - want),
        "exact": got == want,
    }


def score_purpose_c(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    def key(row: dict) -> tuple:
        return (
            row.get("contract_id"),
            row.get("status"),
            tuple(sorted(row.get("obligation_kinds") or [])),
        )
    got = {key(row) for row in actual.get("dependencies") or []}
    want = {key(row) for row in expected["dependencies"]}
    return {"pass": got == want, "missing": sorted(want - got), "extra": sorted(got - want)}


def score_purpose_d(actual: dict | None, expected: dict) -> dict[str, Any]:
    if not isinstance(actual, dict):
        return {"pass": False, "reason": "missing output"}
    got = {
        (row.get("invoice_id"), row.get("contract_id"), row.get("status"))
        for row in actual.get("cases") or []
    }
    want = {
        (row["invoice_id"], row["contract_id"], row["status"]) for row in expected["cases"]
    }
    return {"pass": got == want, "missing": sorted(want - got), "extra": sorted(got - want)}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_abc() -> dict[str, Any]:
    expected_a = load_json(HIDDEN / "expected" / "purpose_a.json")
    expected_b = load_json(HIDDEN / "expected" / "purpose_b.json")
    expected_c = load_json(HIDDEN / "expected" / "purpose_c.json")
    workspace = ABC_WORKSPACE
    actual_a = load_json(workspace / "purpose_ir" / "a" / "output.json")
    actual_b = load_json(workspace / "purpose_ir" / "b" / "output.json")
    actual_c = load_json(workspace / "purpose_ir" / "c" / "output.json")
    world = workspace / "world" / "world.sqlite"
    vocab = load_json(workspace / "construction" / "vocabulary.json")
    return {
        "purpose_a": score_purpose_a(actual_a, expected_a),
        "purpose_b": score_purpose_b(actual_b, expected_b),
        "purpose_c": score_purpose_c(actual_c, expected_c),
        "world_sqlite": world.exists(),
        "world_fingerprint": sha256_file(world),
        "vocabulary": vocab,
        "d_present_in_workspace": (workspace / "purpose_ir" / "d").exists()
        or (workspace / "purposes" / "visible_d.md").exists(),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_abc(), indent=2, sort_keys=True))
