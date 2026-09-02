#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"


def tuples(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation rows keyed by semantic role names."""
    schema = world.relation_schema(relation)
    roles = schema["roles"]
    return [
        {role["name"]: row[role["column"]] for role in roles}
        for row in relation_rows(world, relation)
    ]


def source_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Extract source handles and native locators from tuple provenance."""
    evidence: list[dict[str, str]] = []
    if detail is None:
        return evidence

    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        metadata: dict[str, Any] = {}
        raw_detail = grounding.get("detail")
        if raw_detail:
            try:
                metadata = json.loads(raw_detail)
            except (TypeError, json.JSONDecodeError):
                metadata = {}

        reference = str(grounding.get("reference", ""))
        source = str(
            metadata.get("native_handle")
            or metadata.get("source")
            or reference.split("://", 1)[-1].split("@", 1)[0]
        )
        locator = str(
            metadata.get("native_location")
            or metadata.get("source_native_location")
            or reference
        )
        item = {"source": source, "locator": locator}
        if item not in evidence:
            evidence.append(item)
    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = tuples(world, "candidate_replacement")
        deployments = tuples(world, "deployment_environment")
        required_types = {
            row["bom_item"]: row["part_type"]
            for row in tuples(world, "requires_type")
        }
        part_types = {
            row["part"]: row["part_type"] for row in tuples(world, "part_type")
        }
        voltage_compatible = {
            (row["part"], row["bom_item"])
            for row in tuples(world, "voltage_compatible")
        }
        temperature_compatible = {
            (row["part"], row["bom_item"])
            for row in tuples(world, "temperature_compatible")
        }
        eligible = {
            (row["part"], row["bom_item"])
            for row in tuples(world, "eligible_part")
        }
        accepted = {
            (row["new_part"], row["old_part"], row["context"])
            for row in tuples(world, "acceptable_replacement")
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

        cases: list[dict[str, Any]] = []
        for candidate in candidates:
            new_part = candidate["new_part"]
            old_part = candidate["old_part"]

            # A candidate applies to BOM items for which the replaced part has
            # the required type and represented mechanical compatibility.
            applicable_items = {
                deployment["bom_item"]
                for deployment in deployments
                if required_types.get(deployment["bom_item"])
                == part_types.get(old_part)
                and (old_part, deployment["bom_item"]) in voltage_compatible
                and (old_part, deployment["bom_item"]) in temperature_compatible
            }

            contexts = sorted(
                {
                    deployment["environment"]
                    for deployment in deployments
                    if deployment["bom_item"] in applicable_items
                }
            )
            for context in contexts:
                bom_items = sorted(
                    deployment["bom_item"]
                    for deployment in deployments
                    if deployment["environment"] == context
                    and deployment["bom_item"] in applicable_items
                )
                semantic_key = (new_part, old_part, context)
                if semantic_key in accepted:
                    semantic_state = "accepted"
                    epistemic = "ASSERTED_TRUE"
                elif semantic_key in unresolved:
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
                            "suitable"
                            if all((new_part, item) in eligible for item in bom_items)
                            else "unsuitable"
                        ),
                        "semantic_state": semantic_state,
                        "epistemic": epistemic,
                    }
                )

        cases.sort(
            key=lambda case: (
                case["new_part"],
                case["old_part"],
                case["context"],
            )
        )

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
            support.append(
                {
                    "claim": (
                        f"{supported_case['new_part']} is an accepted, "
                        f"mechanically {supported_case['mechanical_state']} "
                        f"replacement for {supported_case['old_part']} in "
                        f"{supported_case['context']} for "
                        f"{', '.join(supported_case['bom_items'])}"
                    ),
                    "evidence": evidence,
                }
            )

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
