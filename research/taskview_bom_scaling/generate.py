"""Generate frozen S1/S10/S100 parts worlds and independent C0 extensions."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from research.taskview_bom.experiment import FIXTURES as BASE_FIXTURES
from research.taskview_bom.experiment import ORACLE_PATH as BASE_ORACLE_PATH
from research.taskview_bom_scaling import (
    BASELINE_ORACLE_ID,
    EXPERIMENT_ID,
    SCALE_SEED,
)


ROOT = Path(__file__).resolve().parent
SCALES_ROOT = ROOT / "scales"
SCALE_FACTORS = {"S1": 1, "S10": 10, "S100": 100}

MANUFACTURER_FIELDS = [
    "part_number",
    "part_type",
    "description",
    "rated_voltage_v",
    "min_temp_c",
    "max_temp_c",
    "lifecycle",
]
BOM_FIELDS = [
    "bom_item",
    "part_type",
    "required_voltage_v",
    "min_temp_c",
    "max_temp_c",
    "deployment_environment",
]

DISTRACTOR_PARTS = [
    {
        "part_number": "X161",
        "part_type": "sensor_interface",
        "description": "Alternate sealed sensor interface",
        "rated_voltage_v": "24",
        "min_temp_c": "-20",
        "max_temp_c": "75",
        "lifecycle": "active",
        "replaces": "X160",
    },
    {
        "part_number": "X162",
        "part_type": "sensor_interface",
        "description": "Alternate coated sensor interface",
        "rated_voltage_v": "24",
        "min_temp_c": "-20",
        "max_temp_c": "70",
        "lifecycle": "active",
        "replaces": "X160",
    },
    {
        "part_number": "X165",
        "part_type": "sensor_interface",
        "description": "Extended-range sealed sensor interface",
        "rated_voltage_v": "24",
        "min_temp_c": "-30",
        "max_temp_c": "85",
        "lifecycle": "active",
        "replaces": "X160",
    },
    {
        "part_number": "X169",
        "part_type": "sensor_interface",
        "description": "Compact sealed sensor interface",
        "rated_voltage_v": "24",
        "min_temp_c": "-10",
        "max_temp_c": "60",
        "lifecycle": "active",
        "replaces": "X160",
    },
    {
        "part_number": "R201",
        "part_type": "power_relay",
        "description": "Alternate standard power relay",
        "rated_voltage_v": "24",
        "min_temp_c": "-20",
        "max_temp_c": "70",
        "lifecycle": "active",
        "replaces": "R200",
    },
    {
        "part_number": "R202",
        "part_type": "power_relay",
        "description": "Alternate vibration power relay",
        "rated_voltage_v": "24",
        "min_temp_c": "-30",
        "max_temp_c": "80",
        "lifecycle": "active",
        "replaces": "R200",
    },
    {
        "part_number": "R205",
        "part_type": "power_relay",
        "description": "Compact vibration power relay",
        "rated_voltage_v": "24",
        "min_temp_c": "-40",
        "max_temp_c": "85",
        "lifecycle": "active",
        "replaces": "R200",
    },
    {
        "part_number": "R209",
        "part_type": "power_relay",
        "description": "Sealed vibration power relay",
        "rated_voltage_v": "24",
        "min_temp_c": "-10",
        "max_temp_c": "75",
        "lifecycle": "active",
        "replaces": "R200",
    },
]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _cohort_code(index: int) -> str:
    digest = hashlib.sha256(f"{SCALE_SEED}:{index}".encode("ascii")).hexdigest()
    return f"G{index:03}-{digest[:4].upper()}"


def _source_rows(factor: int) -> dict[str, Any]:
    manufacturer = _read_csv(BASE_FIXTURES / "manufacturer.csv")
    suppliers_document = json.loads(
        (BASE_FIXTURES / "suppliers.json").read_text(encoding="utf-8")
    )
    listings = [dict(row) for row in suppliers_document["listings"]]
    bom = _read_csv(BASE_FIXTURES / "bom.csv")
    notes = (BASE_FIXTURES / "engineering_notes.md").read_text(encoding="utf-8").rstrip()
    candidates = [("X110", "X160"), ("R210", "R200")]

    base_manufacturer = list(manufacturer)
    base_listings = list(listings)
    base_bom = list(bom)
    note_sections: list[str] = []
    for cohort_index in range(1, factor):
        cohort = _cohort_code(cohort_index)
        type_map = {
            "sensor_interface": f"sensor_interface_{cohort.lower()}",
            "power_relay": f"power_relay_{cohort.lower()}",
            "connector": f"connector_{cohort.lower()}",
        }
        environment_map = {
            "outdoor_enclosure": f"outdoor_enclosure_{cohort.lower()}",
            "indoor_panel": f"indoor_panel_{cohort.lower()}",
            "high_vibration_cabinet": f"high_vibration_cabinet_{cohort.lower()}",
        }
        for row in base_manufacturer:
            number = f"{row['part_number']}-{cohort}"
            manufacturer.append(
                {
                    **row,
                    "part_number": number,
                    "part_type": type_map[row["part_type"]],
                    "description": f"{row['description']} {cohort}",
                }
            )
        for row in base_listings:
            number = f"{row['manufacturer_part_number']}-{cohort}"
            listing = {
                **row,
                "sku": f"{row['sku']}-{cohort}",
                "manufacturer_part_number": number,
            }
            listings.append(listing)
        for row in base_bom:
            bom.append(
                {
                    **row,
                    "bom_item": f"{row['bom_item']}-{cohort}",
                    "part_type": type_map[row["part_type"]],
                    "deployment_environment": environment_map[
                        row["deployment_environment"]
                    ],
                }
            )
        cohort_candidates = [
            (f"X110-{cohort}", f"X160-{cohort}"),
            (f"R210-{cohort}", f"R200-{cohort}"),
        ]
        candidates.extend(cohort_candidates)
        for candidate_index, (new_part, old_part) in enumerate(
            cohort_candidates, start=1
        ):
            note_sections.append(
                f"## {cohort}-ER-{candidate_index}\n\n"
                f"Candidate: `{new_part}` replaces `{old_part}`."
            )

    if factor > 1:
        for index, distractor in enumerate(DISTRACTOR_PARTS, start=1):
            row = {key: distractor[key] for key in MANUFACTURER_FIELDS}
            manufacturer.append(row)
            prefix = "AC"
            listings.append(
                {
                    "sku": f"{prefix}-{distractor['part_number']}",
                    "supplier": "Acme Supply",
                    "manufacturer_part_number": distractor["part_number"],
                    "availability": "stock",
                }
            )
            candidates.append(
                (distractor["part_number"], str(distractor["replaces"]))
            )
            note_sections.append(
                f"## CAND-{index:02}\n\n"
                f"Candidate: `{distractor['part_number']}` replaces "
                f"`{distractor['replaces']}`."
            )

    if note_sections:
        notes += "\n\n" + "\n\n".join(note_sections)
    notes += "\n"
    return {
        "manufacturer": manufacturer,
        "listings": listings,
        "bom": bom,
        "notes": notes,
        "candidates": candidates,
    }


def _sorted_tuples(rows: set[tuple[Any, ...]]) -> list[list[Any]]:
    return [
        list(row)
        for row in sorted(
            rows,
            key=lambda value: json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ),
        )
    ]


def _oracle_for_scale(
    scale: str,
    factor: int,
    rows: dict[str, Any],
    fingerprints: dict[str, str],
) -> dict[str, Any]:
    baseline = json.loads(BASE_ORACLE_PATH.read_text(encoding="utf-8"))
    manufacturer = rows["manufacturer"]
    listings = rows["listings"]
    bom = rows["bom"]
    candidates = rows["candidates"]

    parts = {row["part_number"]: row for row in manufacturer}
    observed_voltages: dict[str, set[int]] = {
        number: {int(row["rated_voltage_v"])} for number, row in parts.items()
    }
    for listing in listings:
        if "observed_voltage_v" in listing:
            observed_voltages[listing["manufacturer_part_number"]].add(
                int(listing["observed_voltage_v"])
            )

    tuples: dict[str, set[tuple[Any, ...]]] = {
        "manufacturer_part": {
            (f"part:{row['part_number']}",) for row in manufacturer
        },
        "supplier_listing": {(f"listing:{row['sku']}",) for row in listings},
        "bom_item": {(f"bom:{row['bom_item']}",) for row in bom},
        "part_type": {
            (f"part:{row['part_number']}", row["part_type"])
            for row in manufacturer
        },
        "listing_of": {
            (
                f"listing:{row['sku']}",
                f"part:{row['manufacturer_part_number']}",
            )
            for row in listings
        },
        "offered_by": {
            (
                f"listing:{row['sku']}",
                "supplier:"
                + re_slug(str(row["supplier"])),
            )
            for row in listings
        },
        "listing_availability": {
            (f"listing:{row['sku']}", row["availability"]) for row in listings
        },
        "rated_voltage": {
            (f"part:{number}", volts)
            for number, values in observed_voltages.items()
            for volts in values
        },
        "temperature_range": {
            (
                f"part:{row['part_number']}",
                int(row["min_temp_c"]),
                int(row["max_temp_c"]),
            )
            for row in manufacturer
        },
        "lifecycle": {
            (f"part:{row['part_number']}", row["lifecycle"])
            for row in manufacturer
        },
        "requires_type": {
            (f"bom:{row['bom_item']}", row["part_type"]) for row in bom
        },
        "requires_voltage": {
            (f"bom:{row['bom_item']}", int(row["required_voltage_v"]))
            for row in bom
        },
        "requires_temperature": {
            (
                f"bom:{row['bom_item']}",
                int(row["min_temp_c"]),
                int(row["max_temp_c"]),
            )
            for row in bom
        },
        "deployment_environment": {
            (
                f"bom:{row['bom_item']}",
                f"context:{row['deployment_environment']}",
            )
            for row in bom
        },
        "candidate_replacement": {
            (f"part:{new_part}", f"part:{old_part}")
            for new_part, old_part in candidates
        },
        "acceptable_replacement": {
            (
                "part:X110",
                "part:X160",
                "context:outdoor_enclosure",
            ),
            (
                "part:R210",
                "part:R200",
                "context:high_vibration_cabinet",
            ),
        },
    }

    voltage_compatible: set[tuple[Any, ...]] = set()
    temperature_compatible: set[tuple[Any, ...]] = set()
    for part_number, part in parts.items():
        for requirement in bom:
            if part["part_type"] != requirement["part_type"]:
                continue
            pair = (f"part:{part_number}", f"bom:{requirement['bom_item']}")
            if int(requirement["required_voltage_v"]) in observed_voltages[part_number]:
                voltage_compatible.add(pair)
            if (
                int(part["min_temp_c"]) <= int(requirement["min_temp_c"])
                and int(part["max_temp_c"]) >= int(requirement["max_temp_c"])
            ):
                temperature_compatible.add(pair)
    tuples["voltage_compatible"] = voltage_compatible
    tuples["temperature_compatible"] = temperature_compatible
    tuples["eligible_part"] = {
        pair
        for pair in voltage_compatible & temperature_compatible
        if parts[pair[0].removeprefix("part:")]["lifecycle"] != "discontinued"
    }
    tuples["spec_conflict"] = {
        (f"part:{part_number}", "rated_voltage_v")
        for part_number, values in observed_voltages.items()
        if len(values) > 1
    }

    relations: dict[str, Any] = {}
    for relation, declaration in baseline["relations"].items():
        origin = declaration["origin"]
        if relation == "acceptable_replacement":
            relations[relation] = {
                "origin": "SEMANTIC",
                "assertions": [
                    {
                        "tuple": list(assertion),
                        "grounding": {
                            "source": "engineering_notes.md",
                            "source_fingerprint": fingerprints[
                                "engineering_notes.md"
                            ],
                            "native_location": (
                                "lines 10-13"
                                if assertion[0] == "part:X110"
                                else "lines 19-21"
                            ),
                            "construction_method": (
                                "hand-authored taskview-bom-c0-v1 engineering judgment"
                            ),
                        },
                    }
                    for assertion in _sorted_tuples(tuples[relation])
                ],
            }
            continue
        item: dict[str, Any] = {
            "origin": origin,
            "tuples": _sorted_tuples(tuples[relation]),
        }
        if "source_basis" in declaration:
            item["source_basis"] = declaration["source_basis"]
        if "derivation" in declaration:
            item["derivation"] = declaration["derivation"]
        relations[relation] = item
    return {
        "oracle_id": f"{BASELINE_ORACLE_ID}-{scale.lower()}",
        "baseline_oracle_id": BASELINE_ORACLE_ID,
        "experiment_id": EXPERIMENT_ID,
        "scale": scale,
        "scale_factor": factor,
        "seed": SCALE_SEED,
        "frozen_before_c1_evaluation": True,
        "source_fingerprints": fingerprints,
        "role_order": baseline["role_order"],
        "relations": relations,
    }


def re_slug(value: str) -> str:
    return "".join(
        character if character.isalnum() else "-"
        for character in value.lower()
    ).strip("-")


def generate_scale(scale: str, factor: int, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    mutation_dir = destination / "mutation"
    mutation_dir.mkdir(exist_ok=True)
    rows = _source_rows(factor)

    if factor == 1:
        for name in (
            "manufacturer.csv",
            "suppliers.json",
            "bom.csv",
            "engineering_notes.md",
        ):
            shutil.copyfile(BASE_FIXTURES / name, destination / name)
        shutil.copyfile(
            BASE_FIXTURES / "mutations" / "manufacturer.csv",
            mutation_dir / "manufacturer.csv",
        )
        shutil.copyfile(BASE_ORACLE_PATH, destination / "oracle.json")
    else:
        _write_csv(
            destination / "manufacturer.csv",
            MANUFACTURER_FIELDS,
            rows["manufacturer"],
        )
        (destination / "suppliers.json").write_text(
            json.dumps(
                {
                    "revision": (
                        f"supplier-export-{scale.lower()}-seed-{SCALE_SEED}"
                    ),
                    "listings": rows["listings"],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        _write_csv(destination / "bom.csv", BOM_FIELDS, rows["bom"])
        (destination / "engineering_notes.md").write_text(
            rows["notes"], encoding="utf-8"
        )
        mutation_rows = [dict(row) for row in rows["manufacturer"]]
        x100 = next(row for row in mutation_rows if row["part_number"] == "X100")
        x100["max_temp_c"] = "60"
        _write_csv(
            mutation_dir / "manufacturer.csv",
            MANUFACTURER_FIELDS,
            mutation_rows,
        )
        fingerprints = {
            name: _sha256(destination / name)
            for name in (
                "manufacturer.csv",
                "suppliers.json",
                "bom.csv",
                "engineering_notes.md",
            )
        }
        oracle = _oracle_for_scale(scale, factor, rows, fingerprints)
        (destination / "oracle.json").write_text(
            json.dumps(oracle, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    source_paths = [
        destination / "manufacturer.csv",
        destination / "suppliers.json",
        destination / "bom.csv",
        destination / "engineering_notes.md",
    ]
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "baseline_oracle_id": BASELINE_ORACLE_ID,
        "scale": scale,
        "scale_factor": factor,
        "seed": SCALE_SEED,
        "cohort_algorithm": "sha256(seed:index), first four hex characters",
        "source_fingerprints": {
            path.name: _sha256(path) for path in source_paths
        },
        "mutation_fingerprint": _sha256(
            mutation_dir / "manufacturer.csv"
        ),
        "source_record_count": (
            len(rows["manufacturer"])
            + len(rows["listings"])
            + len(rows["bom"])
            + len(rows["candidates"])
        ),
        "source_bytes": sum(path.stat().st_size for path in source_paths),
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def generate_all(root: Path = SCALES_ROOT) -> dict[str, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    return {
        scale: generate_scale(scale, factor, root / scale)
        for scale, factor in SCALE_FACTORS.items()
    }


if __name__ == "__main__":
    print(json.dumps(generate_all(), indent=2, sort_keys=True))
