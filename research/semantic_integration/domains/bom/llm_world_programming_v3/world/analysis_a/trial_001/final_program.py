#!/usr/bin/env python3
"""Compute contextual replacement states from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuples(rows: list[dict[str, Any]], *columns: str) -> set[tuple[str, ...]]:
    return {tuple(str(row[column]) for column in columns) for row in rows}


def source_evidence(detail: dict[str, Any]) -> list[dict[str, str]]:
    """Convert tuple SOURCE groundings to the requested provenance shape."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue

        source = str(grounding.get("reference", ""))
        locator = str(grounding.get("detail", ""))
        try:
            metadata = json.loads(locator)
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        source = str(
            metadata.get("native_handle")
            or metadata.get("source")
            or source
        )
        locator = str(
            metadata.get("native_location")
            or metadata.get("source_native_location")
            or locator
        )

        key = (source, locator)
        if key not in seen:
            evidence.append({"source": source, "locator": locator})
            seen.add(key)
    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = sorted(
            tuples(
                relation_rows(world, "candidate_replacement"),
                "new_part_id",
                "old_part_id",
            )
        )

        context_boms: dict[str, list[str]] = {}
        for row in relation_rows(world, "deployment_environment"):
            context = str(row["environment_id"])
            context_boms.setdefault(context, []).append(str(row["bom_item_id"]))
        for bom_items in context_boms.values():
            bom_items.sort()

        eligible = tuples(
            relation_rows(world, "eligible_part"), "part_id", "bom_item_id"
        )
        accepted = tuples(
            relation_rows(world, "acceptable_replacement"),
            "new_part_id",
            "old_part_id",
            "context_id",
        )
        unresolved = {
            (
                str(item["values"]["new_part"]),
                str(item["values"]["old_part"]),
                str(item["values"]["context"]),
            )
            for item in world.obligations()
            if item.get("relation") == "acceptable_replacement"
        }

        cases: list[dict[str, Any]] = []
        for new_part, old_part in candidates:
            for context, bom_items in sorted(context_boms.items()):
                case_key = (new_part, old_part, context)
                if case_key in accepted:
                    semantic_state = "accepted"
                    epistemic = "ASSERTED_TRUE"
                elif case_key in unresolved:
                    semantic_state = "unresolved"
                    epistemic = "UNRESOLVED"
                else:
                    semantic_state = "not_established"
                    epistemic = "NOT_KNOWN"

                mechanically_suitable = all(
                    (new_part, bom_item) in eligible for bom_item in bom_items
                )
                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "context": context,
                        "bom_items": list(bom_items),
                        "mechanical_state": (
                            "suitable" if mechanically_suitable else "unsuitable"
                        ),
                        "semantic_state": semantic_state,
                        "epistemic": epistemic,
                    }
                )

        cases.sort(key=lambda case: (
            case["new_part"], case["old_part"], case["context"]
        ))

        # Trace the first accepted case through its authoritative source
        # groundings. The case itself is selected from computed World tuples.
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
            detail = world.inspect_tuple("acceptable_replacement", values)
            if detail is not None:
                support.append(
                    {
                        "claim": (
                            f"{supported_case['new_part']} is accepted as a "
                            f"replacement for {supported_case['old_part']} in "
                            f"{supported_case['context']}"
                        ),
                        "evidence": source_evidence(detail),
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
