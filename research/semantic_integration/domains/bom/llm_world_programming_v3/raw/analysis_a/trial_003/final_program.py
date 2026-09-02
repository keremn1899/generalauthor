#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name):
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def prefixed(kind, value):
    return f"{kind}:{value}"


def line_number(text, fragment):
    for number, line in enumerate(text.splitlines(), start=1):
        if fragment in line:
            return number
    raise ValueError(f"Could not locate {fragment!r}")


def parse_candidates(notes):
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates = []
    for section in sections:
        heading, _, body = section.partition("\n")
        match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\.", body
        )
        if not match:
            continue

        context_match = re.search(r"`([^`]+)`\s+context", body)
        bom_match = re.search(r"used by\s+([A-Za-z0-9_-]+)", body)
        if not context_match:
            raise ValueError(f"No deployment context in {heading}")

        normalized = " ".join(body.lower().split())
        negative = (
            "not acceptable",
            "unacceptable",
            "rejected",
            "must not substitute",
        )
        positive = (
            "acceptable substitute",
            "acceptance judgment",
            "accepted substitute",
            "approved substitute",
        )
        uncertainty = ("unresolved", "pending review", "undetermined")

        if any(phrase in normalized for phrase in negative + uncertainty):
            semantic_state = "unresolved"
        elif any(phrase in normalized for phrase in positive):
            semantic_state = "accepted"
        else:
            semantic_state = "not_established"

        candidates.append(
            {
                "heading": heading.strip(),
                "new": match.group(1),
                "old": match.group(2),
                "context": context_match.group(1),
                "noted_bom": bom_match.group(1) if bom_match else None,
                "semantic_state": semantic_state,
                "candidate_text": match.group(0),
            }
        )
    return candidates


def mechanically_suitable(part, bom_rows):
    return all(
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
        for item in bom_rows
    )


def epistemic_class(mechanical_state, semantic_state):
    if mechanical_state == "suitable" and semantic_state == "accepted":
        return "ASSERTED_TRUE"
    if semantic_state == "unresolved":
        return "UNRESOLVED"
    return "NOT_KNOWN"


def main():
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    manufacturer = {row["part_number"]: row for row in manufacturer_rows}

    # Supplier data is authoritative identity evidence: candidate and replaced
    # part numbers must both be represented by listings in the current export.
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        suppliers = json.load(handle)
    listed_parts = {
        row["manufacturer_part_number"] for row in suppliers["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidates(notes)
    cases = []
    case_metadata = []

    for candidate in candidates:
        new_number = candidate["new"]
        old_number = candidate["old"]
        if new_number not in manufacturer or old_number not in manufacturer:
            raise ValueError("Replacement note refers to an unknown manufacturer part")
        if new_number not in listed_parts or old_number not in listed_parts:
            raise ValueError("Replacement note refers to a part absent from listings")

        contextual_boms = [
            row
            for row in bom_rows
            if row["deployment_environment"] == candidate["context"]
        ]
        if not contextual_boms:
            raise ValueError(f"No BOM items for context {candidate['context']}")
        if candidate["noted_bom"] and candidate["noted_bom"] not in {
            row["bom_item"] for row in contextual_boms
        }:
            raise ValueError("Engineering note and BOM context disagree")

        mechanical_state = (
            "suitable"
            if mechanically_suitable(manufacturer[new_number], contextual_boms)
            else "unsuitable"
        )
        case = {
            "new_part": prefixed("part", new_number),
            "old_part": prefixed("part", old_number),
            "context": prefixed("context", candidate["context"]),
            "bom_items": sorted(
                prefixed("bom", row["bom_item"]) for row in contextual_boms
            ),
            "mechanical_state": mechanical_state,
            "semantic_state": candidate["semantic_state"],
            "epistemic": epistemic_class(
                mechanical_state, candidate["semantic_state"]
            ),
        }
        cases.append(case)
        case_metadata.append((case, candidate))

    cases.sort(key=lambda row: (row["new_part"], row["old_part"], row["context"]))

    support = []
    if cases:
        supported = cases[0]
        candidate = next(
            metadata
            for case, metadata in case_metadata
            if case["new_part"] == supported["new_part"]
            and case["old_part"] == supported["old_part"]
            and case["context"] == supported["context"]
        )
        new_number = candidate["new"]
        bom_number = supported["bom_items"][0].split(":", 1)[1]
        support.append(
            {
                "claim": (
                    f"{supported['new_part']} replacing {supported['old_part']} "
                    f"in {supported['context']} is mechanically "
                    f"{supported['mechanical_state']} and semantically "
                    f"{supported['semantic_state']}."
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": (
                            f"{candidate['heading']}; lines "
                            f"{line_number(notes, candidate['candidate_text'])}-"
                            f"{line_number(notes, candidate['context'])}"
                        ),
                    },
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": (
                            f"line {next(i for i, row in enumerate(manufacturer_rows, 2) if row['part_number'] == new_number)}; "
                            f"part_number={new_number}"
                        ),
                    },
                    {
                        "source": "sources/bom.csv",
                        "locator": (
                            f"line {next(i for i, row in enumerate(bom_rows, 2) if row['bom_item'] == bom_number)}; "
                            f"bom_item={bom_number}"
                        ),
                    },
                ],
            }
        )

    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
