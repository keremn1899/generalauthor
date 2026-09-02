#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def role_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation rows keyed by semantic role names, not SQL column names."""
    schema = world.relation_schema(relation)
    role_by_column = {role["column"]: role["name"] for role in schema["roles"]}
    return [
        {role_by_column[column]: value for column, value in row.items()}
        for row in relation_rows(world, relation)
    ]


def tuple_set(rows: list[dict[str, Any]], *roles: str) -> set[tuple[Any, ...]]:
    return {tuple(row[role] for role in roles) for row in rows}


def require_complete_current_derivation(world: Any, relation: str) -> None:
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt.get("status") != "COMPLETE"
        or not receipt.get("current")
        or receipt.get("stale")
        or world.is_stale(relation)
    ):
        raise RuntimeError(f"{relation} lacks a current COMPLETE derivation")


def source_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Extract source handles and native locators from tuple provenance."""
    if detail is None:
        return []

    evidence: list[dict[str, str]] = []
    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue

        metadata: dict[str, Any] = {}
        raw_detail = grounding.get("detail")
        if raw_detail:
            try:
                parsed = json.loads(raw_detail)
                if isinstance(parsed, dict):
                    metadata = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        source = metadata.get("native_handle") or metadata.get("source")
        locator = metadata.get("native_location") or metadata.get(
            "source_native_location"
        )
        if not source:
            source = grounding.get("reference", "compiled World")
        if not locator:
            locator = grounding.get("reference", "asserted tuple")

        item = {"source": str(source), "locator": str(locator)}
        if item not in evidence:
            evidence.append(item)

    return evidence


def build_support(world: Any, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Trace one accepted case to the sources grounding its semantic judgment."""
    supported_case = next(
        (case for case in cases if case["semantic_state"] == "accepted"), None
    )
    if supported_case is None:
        return []

    values = {
        "new_part": supported_case["new_part"],
        "old_part": supported_case["old_part"],
        "context": supported_case["context"],
    }
    detail = world.inspect_tuple("acceptable_replacement", values)
    evidence = source_evidence(detail)
    if not evidence:
        raise RuntimeError("accepted replacement has no authoritative source evidence")

    bom_items = ", ".join(supported_case["bom_items"])
    claim = (
        f"{supported_case['new_part']} replaces {supported_case['old_part']} in "
        f"{supported_case['context']} for {bom_items}; mechanical_state="
        f"{supported_case['mechanical_state']}; semantic_state=accepted"
    )
    return [{"claim": claim, "evidence": evidence}]


def compute() -> dict[str, Any]:
    world = open_world()
    try:
        # These complete derived relations allow their missing tuples to be
        # interpreted as mechanical negatives rather than unknown judgments.
        for relation in (
            "temperature_compatible",
            "voltage_compatible",
            "eligible_part",
        ):
            require_complete_current_derivation(world, relation)

        candidates = role_rows(world, "candidate_replacement")
        deployments = role_rows(world, "deployment_environment")
        temperature = tuple_set(
            role_rows(world, "temperature_compatible"), "part", "bom_item"
        )
        voltage = tuple_set(
            role_rows(world, "voltage_compatible"), "part", "bom_item"
        )
        eligible = tuple_set(role_rows(world, "eligible_part"), "part", "bom_item")
        accepted = tuple_set(
            role_rows(world, "acceptable_replacement"),
            "new_part",
            "old_part",
            "context",
        )
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

            # A replacement applies where the old part mechanically matches a
            # represented BOM item. Lifecycle is deliberately excluded here:
            # a discontinued old part still identifies the BOMs it occupies.
            applicable_by_context: dict[str, list[str]] = {}
            for deployment in deployments:
                bom_item = deployment["bom_item"]
                if (
                    (old_part, bom_item) in temperature
                    and (old_part, bom_item) in voltage
                ):
                    applicable_by_context.setdefault(
                        deployment["environment"], []
                    ).append(bom_item)

            for context, context_bom_items in applicable_by_context.items():
                bom_items = sorted(set(context_bom_items))
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
        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": build_support(world, cases),
        }
        return result
    finally:
        world.close()


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(compute(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
