#!/usr/bin/env python3
"""Compute replacement state from the authoritative files in sources/."""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_clean(path: Path) -> str:
    """Read a source while tolerating displayed every-tenth-line markers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(re.sub(r"^\s*\d+\|", "", line) for line in lines) + "\n"


def read_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(read_clean(path))))


def semantic_state(prose: str) -> str:
    positive = (
        r"\bacceptable\s+substitute\b",
        r"\bpreferred\s+fallback\b",
        r"\bapproved (?:replacement|substitute|alternative)\b",
        r"\baccepted (?:replacement|substitute|alternative)\b",
        r"\bacceptance\s+judgment\b",
    )
    unresolved = (
        r"\bunresolved\b",
        r"\bpending (?:review|qualification|approval)\b",
        r"\bunder review\b",
        r"\bno (?:acceptance )?(?:decision|judgment|conclusion)\b",
    )
    if any(re.search(pattern, prose, re.IGNORECASE) for pattern in positive):
        return "accepted"
    if any(re.search(pattern, prose, re.IGNORECASE) for pattern in unresolved):
        return "unresolved"
    return "not_established"


def parse_candidates(notes: str) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    for section in sections:
        heading, _, prose = section.partition("\n")
        part_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", prose
        )
        context_match = re.search(r"(?:the\s+)?`([^`]+)`\s+context\b", prose)
        if not part_match or not context_match:
            continue
        candidates.append(
            {
                "new_part": part_match.group(1),
                "old_part": part_match.group(2),
                "context": context_match.group(1),
                "section": heading.strip(),
                "prose": prose,
            }
        )
    return candidates


def mechanically_suitable(part: dict[str, str], bom_rows: list[dict[str, str]]) -> bool:
    return all(
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
        for item in bom_rows
    )


def main() -> None:
    notes = read_clean(SOURCES / "engineering_notes.md")
    bom = read_csv(SOURCES / "bom.csv")
    manufacturer_rows = read_csv(SOURCES / "manufacturer.csv")
    parts = {row["part_number"]: row for row in manufacturer_rows}

    cases: list[dict[str, object]] = []
    parsed = parse_candidates(notes)
    for candidate in parsed:
        context_rows = [
            row for row in bom
            if row["deployment_environment"] == candidate["context"]
        ]
        new_part = parts.get(candidate["new_part"])
        suitable = bool(new_part) and bool(context_rows) and mechanically_suitable(
            new_part, context_rows
        )
        semantic = semantic_state(candidate["prose"])
        epistemic = {
            "accepted": "ASSERTED_TRUE",
            "unresolved": "UNRESOLVED",
            "not_established": "NOT_KNOWN",
        }[semantic]
        cases.append(
            {
                "new_part": f"part:{candidate['new_part']}",
                "old_part": f"part:{candidate['old_part']}",
                "context": f"context:{candidate['context']}",
                "bom_items": sorted(
                    f"bom:{row['bom_item']}" for row in context_rows
                ),
                "mechanical_state": "suitable" if suitable else "unsuitable",
                "semantic_state": semantic,
                "epistemic": epistemic,
            }
        )

    cases.sort(key=lambda case: (
        case["new_part"], case["old_part"], case["context"]
    ))

    support: list[dict[str, object]] = []
    if cases:
        supported = cases[0]
        raw_new_part = str(supported["new_part"]).removeprefix("part:")
        candidate = next(
            item for item in parsed if item["new_part"] == raw_new_part
        )
        bom_locators = ", ".join(
            f"row[bom_item={item.removeprefix('bom:')}]"
            for item in supported["bom_items"]
        )
        support = [
            {
                "claim": (
                    f"{supported['new_part']} replaces {supported['old_part']} "
                    f"in {supported['context']}; its semantic state is "
                    f"{supported['semantic_state']}."
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {candidate['section']}",
                    }
                ],
            },
            {
                "claim": (
                    f"{supported['new_part']} is "
                    f"{supported['mechanical_state']} for "
                    f"{', '.join(supported['bom_items'])}."
                ),
                "evidence": [
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": f"row[part_number={raw_new_part}]",
                    },
                    {
                        "source": "sources/bom.csv",
                        "locator": bom_locators,
                    },
                ],
            },
        ]

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
