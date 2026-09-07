"""Probe B scoring: normalization vs world-correctness, metamorphic equivalence."""

from __future__ import annotations

import json
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v2.runtime.projector import (
    project_tables,
)
from research.semantic_integration.domains.diligence.evaluator import (
    load_json,
    score_purpose_a,
    score_purpose_b,
    score_purpose_c,
    score_purpose_d,
)
from research.semantic_integration.schema_normalization_v1.paths import HIDDEN

from research.semantic_integration.schema_normalization_v1.catalog import dict_tables


def purpose_scores(outputs: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "A": load_json(HIDDEN / "expected" / "purpose_a.json"),
        "B": load_json(HIDDEN / "expected" / "purpose_b.json"),
        "C": load_json(HIDDEN / "expected" / "purpose_c.json"),
        "D": load_json(HIDDEN / "expected" / "purpose_d.json"),
    }
    scores = {
        "A": score_purpose_a(outputs["a"], expected["A"]),
        "B": score_purpose_b(outputs["b"], expected["B"]),
        "C": score_purpose_c(outputs["c"], expected["C"]),
        "D": score_purpose_d(outputs["d"], expected["D"]),
    }

    def exact(letter: str, score: dict) -> bool:
        if letter == "B":
            return bool(score.get("exact"))
        return bool(score.get("pass"))

    return {
        "scores": scores,
        "all_exact": all(exact(letter, scores[letter]) for letter in scores),
        "A_exact": exact("A", scores["A"]),
        "B_exact": exact("B", scores["B"]),
        "C_exact": exact("C", scores["C"]),
        "D_exact": exact("D", scores["D"]),
    }


def raw_project(world) -> dict[str, Any]:
    return project_tables(dict_tables(world))


def equivalent(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def identity_preservation(outputs: dict[str, Any]) -> dict[str, Any]:
    empty = 0
    for row in outputs.get("b", {}).get("links") or []:
        if not row.get("left") or not row.get("right"):
            empty += 1
    return {"unresolved_candidate_id_loss": empty, "identifier_preservation": empty == 0}
