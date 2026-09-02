"""Ordinary source readers for RAW analyses.  Not used by WORLD programs."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

CANDIDATE = re.compile(r"Candidate: `([^`]+)` replaces `([^`]+)`\.")
BACKTICK = re.compile(r"`([^`]+)`")


def read_manufacturer(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "part_number": row["part_number"],
                    "part_type": row["part_type"],
                    "rated_voltage_v": int(row["rated_voltage_v"]),
                    "min_temp_c": int(row["min_temp_c"]),
                    "max_temp_c": int(row["max_temp_c"]),
                    "lifecycle": row["lifecycle"],
                }
            )
        return rows


def read_bom(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "bom_item": row["bom_item"],
                    "part_type": row["part_type"],
                    "required_voltage_v": int(row["required_voltage_v"]),
                    "min_temp_c": int(row["min_temp_c"]),
                    "max_temp_c": int(row["max_temp_c"]),
                    "deployment_environment": row["deployment_environment"],
                }
            )
        return rows


def read_suppliers(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for row in document["listings"]:
        item = {
            "sku": row["sku"],
            "supplier": row["supplier"],
            "manufacturer_part_number": row["manufacturer_part_number"],
            "availability": row["availability"],
        }
        if "observed_voltage_v" in row:
            item["observed_voltage_v"] = int(row["observed_voltage_v"])
        rows.append(item)
    return rows


def read_engineering_notes(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [index for index, line in enumerate(lines) if line.startswith("## ")]
    sections: list[dict[str, Any]] = []
    for heading_index, start in enumerate(headings):
        end = headings[heading_index + 1] if heading_index + 1 < len(headings) else len(lines)
        text = "\n".join(lines[start:end])
        match = next(
            (CANDIDATE.fullmatch(line) for line in lines[start:end] if CANDIDATE.fullmatch(line)),
            None,
        )
        if match is None:
            continue
        sections.append(
            {
                "heading": lines[start].removeprefix("## ").strip(),
                "text": text,
                "new_part": match.group(1),
                "old_part": match.group(2),
                "quoted": BACKTICK.findall(text),
            }
        )
    return sections


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def bom_id(bom_item: str) -> str:
    return f"bom:{bom_item}"


def context_id(environment: str) -> str:
    return f"context:{environment}"


def listing_id(sku: str) -> str:
    return f"listing:{sku}"


def voltage_compatible(part: dict[str, Any], bom: dict[str, Any]) -> bool:
    return (
        part["part_type"] == bom["part_type"]
        and part["rated_voltage_v"] == bom["required_voltage_v"]
    )


def temperature_compatible(part: dict[str, Any], bom: dict[str, Any]) -> bool:
    return (
        part["part_type"] == bom["part_type"]
        and part["min_temp_c"] <= bom["min_temp_c"]
        and part["max_temp_c"] >= bom["max_temp_c"]
    )


def lifecycle_active(part: dict[str, Any]) -> bool:
    return part["lifecycle"] != "discontinued"


def eligible(part: dict[str, Any], bom: dict[str, Any]) -> bool:
    return (
        voltage_compatible(part, bom)
        and temperature_compatible(part, bom)
        and lifecycle_active(part)
    )
