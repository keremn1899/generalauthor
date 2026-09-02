#!/usr/bin/env python3
"""Compute replacement state from the workspace's compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def logical_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation rows keyed by their public role names."""
    roles = world.relation_schema(relation)["roles"]
    return [
        {role["name"]: row[role["column"]] for role in roles}
        for row in relation_rows(world, relation)
    ]


def source_evidence(tuple_detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Extract source handles and native locators from tuple provenance."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if tuple_detail is None:
        return evidence

    for grounding in tuple_detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            detail = json.loads(grounding.get("detail", ""))
        except (json.JSONDecodeError, TypeError):
            continue
        source = detail.get("native_handle") or detail.get("source")
        locator = detail.get("native_location") or detail.get(
            "source_native_location"
        )
        if source and locator and (source, locator) not in seen:
            evidence.append({"source": str(source), "locator": str(locator)})
            seen.add((source, locator))
    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = logical_rows(world, "candidate_replacement")
        deployments = logical_rows(world, "deployment_environment")
        eligible = {
            (row["part"], row["bom_item"])
            for row in logical_rows(world, "eligible_part")
        }
        accepted = {
            (row["new_part"], row["old_part"], row["context"])
            for row in logical_rows(world, "acceptable_replacement")
        }
        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
        }

        completeness = world.latest_completeness("eligible_part")
        if (
            completeness is None
            or completeness.get("status") != "COMPLETE"
            or not completeness.get("current")
            or completeness.get("stale")
        ):
            raise RuntimeError(
                "eligible_part lacks a current COMPLETE receipt; "
                "mechanical negatives cannot be established"
            )

        items_by_context: dict[str, list[str]] = {}
        for deployment in deployments:
            items_by_context.setdefault(deployment["environment"], []).append(
                deployment["bom_item"]
            )
        for items in items_by_context.values():
            items.sort()

        cases: list[dict[str, Any]] = []
        for candidate in candidates:
            new_part = candidate["new_part"]
            old_part = candidate["old_part"]
            for context, bom_items in items_by_context.items():
                key = (new_part, old_part, context)
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
                        "bom_items": list(bom_items),
                        "mechanical_state": (
                            "suitable"
                            if all((new_part, item) in eligible for item in bom_items)
                            else "unsuitable"
                        ),
                        "semantic_state": semantic_state,
                        "epistemic": epistemic,
                    }
                )

        cases.sort(key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["context"],
        ))

        support: list[dict[str, Any]] = []
        supported_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"),
            None,
        )
        if supported_case is not None:
            values = {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            }
            evidence = source_evidence(
                world.inspect_tuple("acceptable_replacement", values)
            )
            if evidence:
                support.append(
                    {
                        "claim": (
                            "acceptable_replacement("
                            f"new_part={values['new_part']}, "
                            f"old_part={values['old_part']}, "
                            f"context={values['context']})"
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
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
