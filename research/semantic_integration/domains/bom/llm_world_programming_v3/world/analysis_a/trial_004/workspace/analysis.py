#!/usr/bin/env python3
"""Compute replacement states from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuple_key(row: dict[str, Any], *columns: str) -> tuple[str, ...]:
    return tuple(str(row[column]) for column in columns)


def evidence_for(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Convert authoritative SOURCE groundings to the requested compact form."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for grounding in (detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            metadata = json.loads(grounding.get("detail", ""))
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        source = metadata.get("native_handle") or metadata.get("source")
        locator = metadata.get("native_location") or metadata.get(
            "source_native_location"
        )
        if not source or not locator:
            continue
        key = (str(source), str(locator))
        if key not in seen:
            seen.add(key)
            evidence.append({"source": key[0], "locator": key[1]})
    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployments = relation_rows(world, "deployment_environment")
        requirements = relation_rows(world, "requires_type")
        part_types = relation_rows(world, "part_type")
        eligible_rows = relation_rows(world, "eligible_part")
        acceptance_rows = relation_rows(world, "acceptable_replacement")
        obligations = world.obligations()

        completeness = world.latest_completeness("eligible_part")
        if (
            world.is_stale("eligible_part")
            or completeness is None
            or completeness.get("status") != "COMPLETE"
            or not completeness.get("current", False)
        ):
            raise RuntimeError(
                "eligible_part lacks a current COMPLETE derivation receipt"
            )

        type_by_part = {
            str(row["part_id"]): str(row["part_type"]) for row in part_types
        }
        required_type = {
            str(row["bom_item_id"]): str(row["part_type"]) for row in requirements
        }
        context_by_bom = {
            str(row["bom_item_id"]): str(row["environment_id"])
            for row in deployments
        }
        eligible = {
            tuple_key(row, "part_id", "bom_item_id") for row in eligible_rows
        }
        accepted = {
            tuple_key(row, "new_part_id", "old_part_id", "context_id")
            for row in acceptance_rows
        }
        unresolved = {
            (
                str(item["values"]["new_part"]),
                str(item["values"]["old_part"]),
                str(item["values"]["context"]),
            )
            for item in obligations
            if item.get("relation") == "acceptable_replacement"
        }

        # A candidate applies to BOM items requiring the old part's type.  Grouping
        # those items by deployment environment gives the candidate/context cases.
        grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for candidate in candidates:
            new_part = str(candidate["new_part_id"])
            old_part = str(candidate["old_part_id"])
            old_type = type_by_part[old_part]
            for bom_item, item_type in required_type.items():
                if item_type == old_type and bom_item in context_by_bom:
                    context = context_by_bom[bom_item]
                    grouped[(new_part, old_part, context)].add(bom_item)

        cases: list[dict[str, Any]] = []
        for key in sorted(grouped):
            new_part, old_part, context = key
            bom_items = sorted(grouped[key])
            mechanically_suitable = all(
                (new_part, bom_item) in eligible for bom_item in bom_items
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
        for case in cases:
            if case["semantic_state"] != "accepted":
                continue
            values = {
                "new_part": case["new_part"],
                "old_part": case["old_part"],
                "context": case["context"],
            }
            evidence = evidence_for(
                world.inspect_tuple("acceptable_replacement", values)
            )
            if evidence:
                support.append(
                    {
                        "claim": (
                            f"{case['new_part']} replacing {case['old_part']} in "
                            f"{case['context']} is semantically accepted for "
                            f"{', '.join(case['bom_items'])}"
                        ),
                        "evidence": evidence,
                    }
                )
                break

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
