#!/usr/bin/env python3
"""Compute replacement_state from authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def load_bom() -> list[dict[str, str]]:
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_parts() -> dict[str, dict[str, str]]:
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        return {row["part_number"]: row for row in csv.DictReader(handle)}


def parse_engineering_notes() -> list[dict[str, object]]:
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    sections = re.split(r"(?=^## ER-\d+\s*$)", text, flags=re.MULTILINE)
    records: list[dict[str, object]] = []

    for section in sections:
        section = section.strip()
        if not section.startswith("## ER-"):
            continue

        header, _, body = section.partition("\n")
        record_id = header.replace("##", "").strip()

        candidate_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`",
            body,
        )
        context_match = re.search(
            r"For the\s+`([^`]+)`\s+context",
            body,
        )
        if not candidate_match or not context_match:
            continue

        records.append(
            {
                "record_id": record_id,
                "new_part": candidate_match.group(1),
                "old_part": candidate_match.group(2),
                "context": context_match.group(1),
                "body": body.strip(),
            }
        )

    return records


def bom_items_for_context(bom_rows: list[dict[str, str]], context: str) -> list[str]:
    items = [
        row["bom_item"]
        for row in bom_rows
        if row["deployment_environment"] == context
    ]
    return sorted(items)


def is_mechanically_suitable(part: dict[str, str], bom_item: dict[str, str]) -> bool:
    if part["part_type"] != bom_item["part_type"]:
        return False
    if float(part["rated_voltage_v"]) < float(bom_item["required_voltage_v"]):
        return False
    if float(part["min_temp_c"]) > float(bom_item["min_temp_c"]):
        return False
    if float(part["max_temp_c"]) < float(bom_item["max_temp_c"]):
        return False
    return True


def mechanical_state(
    new_part: str,
    bom_rows: list[dict[str, str]],
    parts: dict[str, dict[str, str]],
    context: str,
) -> str:
    part = parts.get(new_part)
    if part is None:
        return "unsuitable"

    context_rows = [row for row in bom_rows if row["deployment_environment"] == context]
    if not context_rows:
        return "unsuitable"

    for bom_item in context_rows:
        if not is_mechanically_suitable(part, bom_item):
            return "unsuitable"
    return "suitable"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def semantic_state(body: str) -> str:
    lower = _normalize_text(body)

    acceptance_markers = (
        "acceptable substitute",
        "engineering acceptance judgment",
        "preferred fallback",
    )
    if not any(marker in lower for marker in acceptance_markers):
        return "not_established"

    conditional_markers = (
        "if the existing",
        "qualification was not repeated",
    )
    if any(marker in lower for marker in conditional_markers):
        return "unresolved"

    if "acceptable substitute" in lower:
        return "accepted"

    if "engineering acceptance judgment" in lower:
        return "accepted"

    return "unresolved"


def epistemic_class(body: str) -> str:
    lower = _normalize_text(body)

    assertion_markers = (
        "acceptable substitute",
        "engineering acceptance judgment",
        "preferred fallback",
        "treats",
    )
    evidence_gap_markers = (
        "qualification was not repeated",
        "no numeric crosswalk",
        "rather than a conclusion from the tabulated ratings alone",
    )

    has_assertion = any(marker in lower for marker in assertion_markers)
    has_gap = any(marker in lower for marker in evidence_gap_markers)

    if not has_assertion:
        return "NOT_KNOWN"
    if has_gap and "engineering acceptance judgment" in lower:
        return "ASSERTED_TRUE"
    if has_gap:
        return "UNRESOLVED"
    return "ASSERTED_TRUE"


def build_support(
    record: dict[str, object],
    bom_rows: list[dict[str, str]],
    parts: dict[str, dict[str, str]],
    mechanical: str,
    semantic: str,
    epistemic: str,
) -> list[dict[str, object]]:
    context = str(record["context"])
    new_part = str(record["new_part"])
    old_part = str(record["old_part"])
    record_id = str(record["record_id"])
    bom_items = bom_items_for_context(bom_rows, context)

    support: list[dict[str, object]] = [
        {
            "claim": (
                f"{new_part} is a replacement candidate for {old_part} "
                f"in context {context}"
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": record_id,
                }
            ],
        },
        {
            "claim": (
                f"BOM items in context {context} are {', '.join(bom_items)}"
            ),
            "evidence": [
                {
                    "source": "sources/bom.csv",
                    "locator": f"deployment_environment={context}",
                }
            ],
        },
        {
            "claim": (
                f"Mechanical suitability of {new_part} for context {context} "
                f"is {mechanical}"
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"part_number={new_part}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"deployment_environment={context}",
                },
            ],
        },
        {
            "claim": (
                f"Semantic acceptance state is {semantic} and epistemic class "
                f"is {epistemic}"
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": record_id,
                }
            ],
        },
    ]

    part = parts[new_part]
    for bom_item_name in bom_items:
        bom_item = next(row for row in bom_rows if row["bom_item"] == bom_item_name)
        support.append(
            {
                "claim": (
                    f"Part {new_part} ({part['part_type']}, "
                    f"{part['rated_voltage_v']}V, "
                    f"{part['min_temp_c']}..{part['max_temp_c']}C) "
                    f"meets BOM {bom_item_name} requirements "
                    f"({bom_item['part_type']}, "
                    f"{bom_item['required_voltage_v']}V, "
                    f"{bom_item['min_temp_c']}..{bom_item['max_temp_c']}C)"
                ),
                "evidence": [
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": f"part_number={new_part}",
                    },
                    {
                        "source": "sources/bom.csv",
                        "locator": f"bom_item={bom_item_name}",
                    },
                ],
            }
        )

    return support


def main() -> None:
    bom_rows = load_bom()
    parts = load_parts()
    records = parse_engineering_notes()

    cases: list[dict[str, object]] = []
    for record in records:
        context = str(record["context"])
        new_part = str(record["new_part"])
        old_part = str(record["old_part"])
        body = str(record["body"])

        bom_items = bom_items_for_context(bom_rows, context)
        mechanical = mechanical_state(new_part, bom_rows, parts, context)
        semantic = semantic_state(body)
        epistemic = epistemic_class(body)

        cases.append(
            {
                "new_part": f"part:{new_part}",
                "old_part": f"part:{old_part}",
                "context": f"context:{context}",
                "bom_items": [f"bom:{item}" for item in bom_items],
                "mechanical_state": mechanical,
                "semantic_state": semantic,
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

    support_record = next(
        record for record in records if str(record["new_part"]) == "R210"
    )
    support = build_support(
        support_record,
        bom_rows,
        parts,
        mechanical_state("R210", bom_rows, parts, str(support_record["context"])),
        semantic_state(str(support_record["body"])),
        epistemic_class(str(support_record["body"])),
    )

    result = {
        "task": "replacement_state",
        "cases": cases,
        "support": support,
    }

    output_path = ROOT / "output.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
