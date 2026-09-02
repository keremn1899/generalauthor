#!/usr/bin/env python3
"""Determine replacement candidate state under applicable deployment contexts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"

CASES_SQL = """
SELECT
    cr.new_part_id AS new_part,
    cr.old_part_id AS old_part,
    de.environment_id AS context,
    de.bom_item_id AS bom_item
FROM candidate_replacement AS cr
JOIN part_type AS pt_old ON pt_old.part_id = cr.old_part_id
JOIN requires_type AS rt ON rt.part_type = pt_old.part_type
JOIN deployment_environment AS de ON de.bom_item_id = rt.bom_item_id
ORDER BY new_part, old_part, context, bom_item
"""


def group_cases(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in rows:
        key = (row["new_part"], row["old_part"], row["context"])
        grouped[key].append(row["bom_item"])
    cases = []
    for (new_part, old_part, context), bom_items in grouped.items():
        cases.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "context": context,
                "bom_items": sorted(set(bom_items)),
            }
        )
    cases.sort(key=lambda c: (c["new_part"], c["old_part"], c["context"]))
    return cases


def is_mechanically_suitable(
    world, new_part: str, bom_items: list[str]
) -> str:
    for bom_item in bom_items:
        rows = world.query_semantic(
            """
            SELECT 1
            FROM eligible_part
            WHERE part_id = ? AND bom_item_id = ?
            """,
            (new_part, bom_item),
        )
        if not rows:
            return "unsuitable"
    return "suitable"


def obligation_keys(obligations: list[dict]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for obligation in obligations:
        values = obligation["values"]
        keys.add((values["new_part"], values["old_part"], values["context"]))
    return keys


def acceptance_exists(
    world, new_part: str, old_part: str, context: str
) -> bool:
    rows = world.query_semantic(
        """
        SELECT 1
        FROM acceptable_replacement
        WHERE new_part_id = ? AND old_part_id = ? AND context_id = ?
        """,
        (new_part, old_part, context),
    )
    return bool(rows)


def semantic_state_for(
    world,
    new_part: str,
    old_part: str,
    context: str,
    obligated: set[tuple[str, str, str]],
) -> str:
    key = (new_part, old_part, context)
    if acceptance_exists(world, new_part, old_part, context):
        return "accepted"
    if key in obligated:
        return "unresolved"
    return "not_established"


def epistemic_for(semantic: str) -> str:
    if semantic == "accepted":
        return "ASSERTED_TRUE"
    if semantic == "unresolved":
        return "UNRESOLVED"
    return "NOT_KNOWN"


def grounding_evidence(detail: dict) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(source: str, locator: str) -> None:
        key = (source, locator)
        if key in seen:
            return
        seen.add(key)
        evidence.append({"source": source, "locator": locator})

    for item in detail.get("grounding", []):
        if item.get("kind") != "SOURCE":
            continue
        parsed: dict = {}
        raw_detail = item.get("detail")
        if isinstance(raw_detail, str) and raw_detail:
            try:
                parsed = json.loads(raw_detail)
            except json.JSONDecodeError:
                parsed = {}
        source = parsed.get("native_handle") or item.get("reference", "")
        locator = parsed.get("native_location") or ""
        if source and locator:
            add(source, locator)

    return evidence


def build_support(world, case: dict[str, object]) -> list[dict[str, object]]:
    new_part = str(case["new_part"])
    old_part = str(case["old_part"])
    context = str(case["context"])
    semantic = str(case["semantic_state"])

    if semantic == "accepted":
        claim = (
            f"{new_part} is an acceptable replacement for {old_part} "
            f"in {context}"
        )
        detail = world.inspect_tuple(
            "acceptable_replacement",
            {"new_part": new_part, "old_part": old_part, "context": context},
        )
        if detail is None:
            return []
        return [{"claim": claim, "evidence": grounding_evidence(detail)}]

    if semantic == "unresolved":
        claim = (
            f"Semantic acceptance of {new_part} replacing {old_part} "
            f"in {context} is required but not established"
        )
        detail = world.inspect_tuple(
            "candidate_replacement",
            {"new_part": new_part, "old_part": old_part},
        )
        if detail is None:
            return []
        return [{"claim": claim, "evidence": grounding_evidence(detail)}]

    claim = (
        f"{new_part} is a represented replacement candidate for {old_part} "
        f"in {context}"
    )
    detail = world.inspect_tuple(
        "candidate_replacement",
        {"new_part": new_part, "old_part": old_part},
    )
    if detail is None:
        return []
    return [{"claim": claim, "evidence": grounding_evidence(detail)}]


def main() -> None:
    world = open_world()
    try:
        obligated = obligation_keys(world.obligations())
        raw_cases = group_cases(world.query_semantic(CASES_SQL))

        cases: list[dict[str, object]] = []
        for case in raw_cases:
            new_part = str(case["new_part"])
            old_part = str(case["old_part"])
            context = str(case["context"])
            bom_items = list(case["bom_items"])
            semantic = semantic_state_for(
                world, new_part, old_part, context, obligated
            )
            cases.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "context": context,
                    "bom_items": bom_items,
                    "mechanical_state": is_mechanically_suitable(
                        world, new_part, bom_items
                    ),
                    "semantic_state": semantic,
                    "epistemic": epistemic_for(semantic),
                }
            )

        support_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"),
            cases[0] if cases else None,
        )
        support = build_support(world, support_case) if support_case else []

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
