"""AXIS C: certified-World projection, no sources, no constructor LLM."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.runtime.projector import (
    write_purpose_outputs,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.validators import (
    validate_purpose_c_kinds,
    validate_world,
)
from research.semantic_integration.domains.diligence.evaluator import (
    load_json,
    score_purpose_a,
    score_purpose_b,
    score_purpose_c,
    score_purpose_d,
)
from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
    build_certified_world,
)

ROOT = Path(__file__).resolve().parent
HIDDEN = ROOT.parent / "hidden"


def run_axis_c(tmp: Path | None = None) -> dict:
    dest = tmp or (ROOT / "axis_c")
    dest.mkdir(parents=True, exist_ok=True)
    world = dest / "world.sqlite"
    build_certified_world(world)
    outputs = write_purpose_outputs(world, dest / "08_outputs")
    scores = {
        "A": score_purpose_a(outputs["a"], load_json(HIDDEN / "expected" / "purpose_a.json")),
        "B": score_purpose_b(outputs["b"], load_json(HIDDEN / "expected" / "purpose_b.json")),
        "C": score_purpose_c(outputs["c"], load_json(HIDDEN / "expected" / "purpose_c.json")),
        "D": score_purpose_d(outputs["d"], load_json(HIDDEN / "expected" / "purpose_d.json")),
    }

    def _exact(letter: str, score: dict) -> bool:
        if letter == "B":
            return bool(score.get("exact"))
        return bool(score.get("pass"))

    b = scores["B"]
    kinds = validate_purpose_c_kinds(outputs["c"]["dependencies"])
    ground = validate_world(world)
    payload = {
        "axis": "C",
        "scores": scores,
        "all_exact": all(_exact(letter, score) for letter, score in scores.items()),
        "fidelity": {
            "candidate_identifiers_preserved": not any(
                row.get("left") in {None, ""} or row.get("right") in {None, ""}
                for row in outputs["b"]["links"]
            ),
            "disposition_mapping_exact": bool(b.get("exact")),
            "identifier_rendering_exact": bool(scores["A"]["pass"] and scores["D"]["pass"]),
            "role_orientation_exact": bool(b.get("exact")),
            "allowed_semantic_kinds_exact": kinds["invalid_purpose_kinds"] == 0 and bool(scores["C"].get("pass")),
            "unexpected_extra_rows": {
                "A": scores["A"].get("extra") or [],
                "B": b.get("extra") or [],
                "C": scores["C"].get("extra") or [],
                "D": scores["D"].get("extra") or [],
            },
            "missing_rows": {
                "A": scores["A"].get("missing") or [],
                "B": b.get("missing_required") or [],
                "C": scores["C"].get("missing") or [],
                "D": scores["D"].get("missing") or [],
            },
        },
        "invalid_kinds": kinds,
        "world_validation": ground,
        "source_reads": 0,
        "sources_present": False,
    }
    (dest / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_axis_c(), indent=2, sort_keys=True))
