#!/usr/bin/env python3
"""Derive context-specific replacement state from the authoritative sources."""

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name):
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_candidates(notes):
    """Extract each candidate, its stated context, and its scoped judgment."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates = []
    for section in sections:
        heading, _, body = section.partition("\n")
        relation = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body
        )
        if relation is None:
            continue

        contexts = re.findall(r"`([^`]+)`\s+context\b", body)
        for context in dict.fromkeys(contexts):
            candidates.append(
                {
                    "new": relation.group(1),
                    "old": relation.group(2),
                    "context": context,
                    "section": heading.strip(),
                    "text": body,
                }
            )
    return candidates


def semantic_state(text):
    normalized = " ".join(text.lower().split())

    # Check explicit non-acceptance before positive words such as "acceptable".
    unresolved_markers = (
        "not acceptable",
        "acceptance is unresolved",
        "remains unresolved",
        "pending acceptance",
        "pending review",
        "not yet accepted",
        "rejected",
    )
    if any(marker in normalized for marker in unresolved_markers):
        return "unresolved"

    accepted_markers = (
        "acceptable substitute",
        "accepted substitute",
        "approved substitute",
        "preferred fallback",
        "accepted replacement",
        "approved replacement",
    )
    if any(marker in normalized for marker in accepted_markers):
        return "accepted"
    return "not_established"


def mechanically_suitable(part, bom_rows):
    if not bom_rows:
        return False

    rated_voltage = float(part["rated_voltage_v"])
    part_min = float(part["min_temp_c"])
    part_max = float(part["max_temp_c"])
    return all(
        part["part_type"] == item["part_type"]
        and rated_voltage >= float(item["required_voltage_v"])
        and part_min <= float(item["min_temp_c"])
        and part_max >= float(item["max_temp_c"])
        for item in bom_rows
    )


def prefixed(kind, value):
    return f"{kind}:{value}"


def make_support(candidate, case, part, bom_rows):
    """Trace the first result case through relation, BOM, and rating evidence."""
    relation_claim = (
        f"{case['new_part']} replaces {case['old_part']} in "
        f"{case['context']} with semantic state {case['semantic_state']}."
    )
    support = [
        {
            "claim": relation_claim,
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section {candidate['section']}",
                }
            ],
        },
        {
            "claim": (
                f"{case['context']} contains BOM items "
                f"{', '.join(case['bom_items'])}."
            ),
            "evidence": [
                {
                    "source": "sources/bom.csv",
                    "locator": f"row bom_item={row['bom_item']}",
                }
                for row in bom_rows
            ],
        },
        {
            "claim": (
                f"{case['new_part']} has mechanical state "
                f"{case['mechanical_state']} for {', '.join(case['bom_items'])}."
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"row part_number={part['part_number']}",
                },
                *[
                    {
                        "source": "sources/bom.csv",
                        "locator": f"row bom_item={row['bom_item']}",
                    }
                    for row in bom_rows
                ],
            ],
        },
    ]
    return support


def main():
    manufacturer = {
        row["part_number"]: row for row in read_csv("manufacturer.csv")
    }
    bom = read_csv("bom.csv")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidates(notes)

    cases = []
    provenance_inputs = []
    epistemic_for = {
        "accepted": "ASSERTED_TRUE",
        "unresolved": "UNRESOLVED",
        "not_established": "NOT_KNOWN",
    }

    for candidate in candidates:
        part = manufacturer[candidate["new"]]
        bom_rows = [
            row
            for row in bom
            if row["deployment_environment"] == candidate["context"]
            and row["part_type"] == part["part_type"]
        ]
        semantic = semantic_state(candidate["text"])
        suitable = mechanically_suitable(part, bom_rows)
        case = {
            "new_part": prefixed("part", candidate["new"]),
            "old_part": prefixed("part", candidate["old"]),
            "context": prefixed("context", candidate["context"]),
            "bom_items": sorted(
                prefixed("bom", row["bom_item"]) for row in bom_rows
            ),
            "mechanical_state": "suitable" if suitable else "unsuitable",
            "semantic_state": semantic,
            "epistemic": epistemic_for[semantic],
        }
        cases.append(case)
        provenance_inputs.append((case, candidate, part, bom_rows))

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))
    provenance_inputs.sort(
        key=lambda item: (
            item[0]["new_part"],
            item[0]["old_part"],
            item[0]["context"],
        )
    )

    support = []
    if provenance_inputs:
        case, candidate, part, bom_rows = provenance_inputs[0]
        support = make_support(candidate, case, part, bom_rows)

    result = {
        "task": "replacement_state",
        "cases": cases,
        "support": support,
    }
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
