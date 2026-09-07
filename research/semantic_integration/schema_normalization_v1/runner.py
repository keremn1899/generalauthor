"""Run Probe B. No LLM. Optional family-hint condition only if B0 identity matching fails."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.schema_normalization_v1.freeze_fixtures import (
    freeze_certified,
    freeze_participants,
)
from research.semantic_integration.schema_normalization_v1.metamorphic import generate_all
from research.semantic_integration.schema_normalization_v1.normalizers.exact_contract import (
    normalize_world,
    project_normalized,
)
from research.semantic_integration.schema_normalization_v1.paths import (
    CERTIFIED,
    METAMORPHIC,
    PARTICIPANT,
    REPORTS,
    SCORING,
)
from research.semantic_integration.schema_normalization_v1.scoring import (
    equivalent,
    identity_preservation,
    purpose_scores,
    raw_project,
)


def run_one(world: Path, vocabulary: Path | None, dispositions: Path | None, family: bool = False) -> dict:
    normalized = normalize_world(world, vocabulary=vocabulary, dispositions=dispositions, use_family_hint=family)
    outputs = project_normalized(normalized)
    scored = purpose_scores(outputs)
    return {
        "normalization": {
            "canonical_relations_recovered": normalized["canonical_relations_recovered"],
            "required_mappings_missed": normalized["required_mappings_missed"],
            "false_mappings": normalized["false_mappings"],
            "used_family_hints": family,
        },
        "world_correctness": scored,
        "identifier_preservation": identity_preservation(outputs),
        "outputs": outputs,
    }


def run_b0() -> dict:
    freeze_participants()
    freeze_certified()
    certified = run_one(CERTIFIED / "world.sqlite", None, None)
    participants = {}
    for trial in sorted(PARTICIPANT.glob("T*")):
        participants[trial.name] = run_one(
            trial / "world.sqlite",
            trial / "01_vocabulary.json" if (trial / "01_vocabulary.json").exists() else None,
            trial / "05_dispositions.json" if (trial / "05_dispositions.json").exists() else None,
        )
        raw = purpose_scores(raw_project(trial / "world.sqlite"))
        participants[trial.name]["raw_projector"] = {
            "all_exact": raw["all_exact"],
            "A_exact": raw["A_exact"],
            "B_exact": raw["B_exact"],
            "C_exact": raw["C_exact"],
            "D_exact": raw["D_exact"],
        }
    return {"certified": certified, "participants": participants}


def run_metamorphic(certified_outputs: dict) -> dict:
    mapping = generate_all(CERTIFIED / "world.sqlite")
    results = {}
    for name, world in mapping.items():
        vocab = None
        result = run_one(world, vocab, None)
        results[name] = {
            "behavioral_equivalence_to_certified_normalized": equivalent(
                result["outputs"], certified_outputs
            ),
            "world_correctness": result["world_correctness"],
            "normalization": result["normalization"],
            "identifier_preservation": result["identifier_preservation"],
        }
        if name == "b7_noise":
            results[name]["false_mappings"] = result["normalization"]["false_mappings"]
            # noise should not appear as identity SAME on the noise pair unless identity contract matched
            noise_pairs = [
                (row["left"], row["right"], row["epistemic"])
                for row in result["outputs"]["b"]["links"]
                if "MATCH" in str(row)
            ]
            results[name]["noise_mapped_as_identity"] = any(
                row.get("epistemic") not in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
                for row in result["outputs"]["b"]["links"]
            )
    return results


def run_all() -> dict:
    b0 = run_b0()
    certified_out = b0["certified"]["outputs"]
    meta = run_metamorphic(certified_out)
    # Family hints only if identity recovery failed on certified B0
    family = None
    if "identity_judgment" in (b0["certified"]["normalization"]["required_mappings_missed"] or []):
        family = run_one(CERTIFIED / "world.sqlite", None, None, family=True)
    payload = {
        "experiment_id": "schema-normalization-v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "b0": {
            "certified": {k: v for k, v in b0["certified"].items() if k != "outputs"},
            "participants": {
                name: {k: v for k, v in item.items() if k != "outputs"}
                for name, item in b0["participants"].items()
            },
        },
        "metamorphic": meta,
        "semantic_family_tested": family is not None,
        "semantic_family": None if family is None else {k: v for k, v in family.items() if k != "outputs"},
    }
    SCORING.mkdir(parents=True, exist_ok=True)
    (SCORING / "mappings.json").write_text(
        json.dumps(
            {
                "certified": b0["certified"]["normalization"],
                "participants": {k: v["normalization"] for k, v in b0["participants"].items()},
            },
            indent=2,
        )
        + "\n"
    )
    (SCORING / "behavioral_equivalence.json").write_text(
        json.dumps({k: v.get("behavioral_equivalence_to_certified_normalized") for k, v in meta.items()}, indent=2)
        + "\n"
    )
    (SCORING / "metamorphic_results.json").write_text(json.dumps(meta, indent=2) + "\n")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "schema_normalization.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2)[:5000])
