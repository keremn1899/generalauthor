#!/usr/bin/env python3
"""Report replacement state from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def source_evidence(tuple_detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Convert tuple grounding pointers to the requested evidence shape."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for grounding in (tuple_detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue

        try:
            detail = json.loads(grounding.get("detail", ""))
        except (TypeError, json.JSONDecodeError):
            detail = {}

        source = (
            detail.get("native_handle")
            or detail.get("source")
            or grounding.get("reference")
        )
        locator = (
            detail.get("native_location")
            or detail.get("source_native_location")
            or grounding.get("reference")
        )
        if source and locator and (source, locator) not in seen:
            evidence.append({"source": str(source), "locator": str(locator)})
            seen.add((source, locator))

    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployments = relation_rows(world, "deployment_environment")
        requirements = relation_rows(world, "requires_type")
        part_types = relation_rows(world, "part_type")
        eligible = relation_rows(world, "eligible_part")
        accepted_rows = relation_rows(world, "acceptable_replacement")
        obligations = world.obligations()

        types_by_part: dict[str, set[str]] = defaultdict(set)
        for row in part_types:
            types_by_part[row["part_id"]].add(row["part_type"])

        required_type_by_bom: dict[str, set[str]] = defaultdict(set)
        for row in requirements:
            required_type_by_bom[row["bom_item_id"]].add(row["part_type"])

        eligible_pairs = {
            (row["part_id"], row["bom_item_id"]) for row in eligible
        }
        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in accepted_rows
        }
        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in obligations
            if obligation.get("relation") == "acceptable_replacement"
            and {"new_part", "old_part", "context"}
            <= obligation.get("values", {}).keys()
        }

        grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for candidate in candidates:
            new_part = candidate["new_part_id"]
            old_part = candidate["old_part_id"]
            old_types = types_by_part[old_part]
            for deployment in deployments:
                bom_item = deployment["bom_item_id"]
                if old_types & required_type_by_bom[bom_item]:
                    grouped[
                        (new_part, old_part, deployment["environment_id"])
                    ].add(bom_item)

        cases: list[dict[str, Any]] = []
        for (new_part, old_part, context), bom_set in sorted(grouped.items()):
            bom_items = sorted(bom_set)
            key = (new_part, old_part, context)
            mechanically_suitable = all(
                (new_part, bom_item) in eligible_pairs for bom_item in bom_items
            )

            if key in accepted:
                semantic_state = "accepted"
                epistemic = "ASSERTED_TRUE"
            elif key in unresolved:
                semantic_state = "unresolved"
                epistemic = "UNRESOLVED"
            else:
                semantic_state = "not_established"
                epistemic = "NOT_KNOWN"

            cases.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "context": context,
                    "bom_items": bom_items,
                    "mechanical_state": (
                        "suitable" if mechanically_suitable else "unsuitable"
                    ),
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        support: list[dict[str, Any]] = []
        supported_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"),
            None,
        )
        if supported_case is not None:
            detail = world.inspect_tuple(
                "acceptable_replacement",
                {
                    "new_part": supported_case["new_part"],
                    "old_part": supported_case["old_part"],
                    "context": supported_case["context"],
                },
            )
            evidence = source_evidence(detail)
            if evidence:
                support.append(
                    {
                        "claim": (
                            "acceptable_replacement("
                            f"new_part={supported_case['new_part']}, "
                            f"old_part={supported_case['old_part']}, "
                            f"context={supported_case['context']})"
                        ),
                        "evidence": evidence,
                    }
                )

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
