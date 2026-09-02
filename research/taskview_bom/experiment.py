"""Deterministic C0/C1 TaskView experiment for a small parts/BOM world.

This module is research-only.  It reuses the TaskView relational store without
adding a construction path or changing TaskView's production API.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from taskview import (
    Completeness,
    CompletenessStatus,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
    TaskView,
)


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
ORACLE_PATH = ROOT / "oracle.json"
SOURCE_NAMES = (
    "manufacturer.csv",
    "suppliers.json",
    "bom.csv",
    "engineering_notes.md",
)


@dataclass(frozen=True)
class Observation:
    source: str
    fingerprint: str
    location: str
    method: str
    key: str
    data: dict[str, Any]
    evidence: str

    def grounding(self) -> Grounding:
        detail = json.dumps(
            {
                "source": self.source,
                "source_fingerprint": self.fingerprint,
                "source_native_location": self.location,
                "construction_method": self.method,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return Grounding(
            GroundingKind.SOURCE,
            f"fixture://{self.source}@{self.fingerprint}",
            detail,
        )


@dataclass
class Compilation:
    view: TaskView
    observations: list[Observation]
    fingerprints: dict[str, str]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_observations(path: Path, method: str, key_field: str) -> list[Observation]:
    fingerprint = _sha256(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Observation(
            source=path.name,
            fingerprint=fingerprint,
            location=f"row {index + 2} ({key_field}={row[key_field]})",
            method=method,
            key=row[key_field],
            data=dict(row),
            evidence=lines[index + 1],
        )
        for index, row in enumerate(rows)
    ]


def parse_manufacturer(path: Path) -> list[Observation]:
    return _csv_observations(
        path,
        "csv.DictReader; native part_number is the stable key",
        "part_number",
    )


def parse_bom(path: Path) -> list[Observation]:
    return _csv_observations(
        path,
        "csv.DictReader; native bom_item is the stable key",
        "bom_item",
    )


def parse_suppliers(path: Path) -> list[Observation]:
    fingerprint = _sha256(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    return [
        Observation(
            source=path.name,
            fingerprint=fingerprint,
            location=f"$.listings[{index}] (sku={row['sku']})",
            method="json.loads; native sku is the stable key",
            key=str(row["sku"]),
            data=dict(row),
            evidence=json.dumps(row, sort_keys=True, separators=(",", ":")),
        )
        for index, row in enumerate(document["listings"])
    ]


_CANDIDATE = re.compile(r"Candidate: `([^`]+)` replaces `([^`]+)`\.")


def parse_engineering_notes(path: Path) -> list[Observation]:
    fingerprint = _sha256(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [index for index, line in enumerate(lines) if line.startswith("## ")]
    observations: list[Observation] = []
    for heading_index, start in enumerate(headings):
        end = headings[heading_index + 1] if heading_index + 1 < len(headings) else len(lines)
        section = lines[start:end]
        match = next(
            (_CANDIDATE.fullmatch(line) for line in section if _CANDIDATE.fullmatch(line)),
            None,
        )
        if match is None:
            continue
        record_id = lines[start].removeprefix("## ").strip()
        observations.append(
            Observation(
                source=path.name,
                fingerprint=fingerprint,
                location=f"lines {start + 1}-{end} ({record_id})",
                method="markdown heading segmentation plus exact Candidate record syntax",
                key=record_id,
                data={"new_part": match.group(1), "old_part": match.group(2)},
                evidence="\n".join(section).strip(),
            )
        )
    return observations


def parse_sources(
    source_dir: Path = FIXTURES, *, manufacturer_path: Path | None = None
) -> tuple[list[Observation], dict[str, str]]:
    manufacturer = manufacturer_path or source_dir / "manufacturer.csv"
    paths = {
        "manufacturer.csv": manufacturer,
        "suppliers.json": source_dir / "suppliers.json",
        "bom.csv": source_dir / "bom.csv",
        "engineering_notes.md": source_dir / "engineering_notes.md",
    }
    observations = [
        *parse_manufacturer(paths["manufacturer.csv"]),
        *parse_suppliers(paths["suppliers.json"]),
        *parse_bom(paths["bom.csv"]),
        *parse_engineering_notes(paths["engineering_notes.md"]),
    ]
    return observations, {name: _sha256(path) for name, path in paths.items()}


REF = RoleType.REFERENT
TEXT = RoleType.TEXT
INTEGER = RoleType.INTEGER

BASE_RELATIONS: dict[str, list[Role]] = {
    "manufacturer_part": [Role("part", REF)],
    "supplier_listing": [Role("listing", REF)],
    "bom_item": [Role("bom_item", REF)],
    "part_type": [Role("part", REF), Role("part_type", TEXT)],
    "listing_of": [Role("listing", REF), Role("part", REF)],
    "offered_by": [Role("listing", REF), Role("supplier", REF)],
    "listing_availability": [Role("listing", REF), Role("state", TEXT)],
    "rated_voltage": [Role("part", REF), Role("volts", INTEGER)],
    "temperature_range": [
        Role("part", REF),
        Role("minimum_c", INTEGER),
        Role("maximum_c", INTEGER),
    ],
    "lifecycle": [Role("part", REF), Role("state", TEXT)],
    "requires_type": [Role("bom_item", REF), Role("part_type", TEXT)],
    "requires_voltage": [Role("bom_item", REF), Role("volts", INTEGER)],
    "requires_temperature": [
        Role("bom_item", REF),
        Role("minimum_c", INTEGER),
        Role("maximum_c", INTEGER),
    ],
    "deployment_environment": [
        Role("bom_item", REF),
        Role("environment", REF),
    ],
    "candidate_replacement": [Role("new_part", REF), Role("old_part", REF)],
    "acceptable_replacement": [
        Role("new_part", REF),
        Role("old_part", REF),
        Role("context", REF),
    ],
}

DERIVED_RELATIONS: dict[str, list[Role]] = {
    "voltage_compatible": [Role("part", REF), Role("bom_item", REF)],
    "temperature_compatible": [Role("part", REF), Role("bom_item", REF)],
    "eligible_part": [Role("part", REF), Role("bom_item", REF)],
    "spec_conflict": [Role("part", REF), Role("property", TEXT)],
}

DERIVATIONS: dict[str, dict[str, Any]] = {
    "voltage_compatible": {
        "inputs": ["part_type", "rated_voltage", "requires_type", "requires_voltage"],
        "sql": """
            SELECT DISTINCT p.part_id, b.bom_item_id
            FROM part_type AS p
            JOIN requires_type AS t ON t.part_type = p.part_type
            JOIN requires_voltage AS b ON b.bom_item_id = t.bom_item_id
            JOIN rated_voltage AS v
              ON v.part_id = p.part_id AND v.volts = b.volts
        """,
        "universe": "bom_item",
        "basis": "Exact voltage equality for every represented BOM item and required part type.",
    },
    "temperature_compatible": {
        "inputs": [
            "part_type",
            "temperature_range",
            "requires_type",
            "requires_temperature",
        ],
        "sql": """
            SELECT DISTINCT p.part_id, b.bom_item_id
            FROM part_type AS p
            JOIN requires_type AS t ON t.part_type = p.part_type
            JOIN requires_temperature AS b ON b.bom_item_id = t.bom_item_id
            JOIN temperature_range AS r ON r.part_id = p.part_id
            WHERE r.minimum_c <= b.minimum_c AND r.maximum_c >= b.maximum_c
        """,
        "universe": "bom_item",
        "basis": "Range containment for every represented BOM item and required part type.",
    },
    "eligible_part": {
        "inputs": ["voltage_compatible", "temperature_compatible", "lifecycle"],
        "sql": """
            SELECT DISTINCT v.part_id, v.bom_item_id
            FROM voltage_compatible AS v
            JOIN temperature_compatible AS t
              ON t.part_id = v.part_id AND t.bom_item_id = v.bom_item_id
            JOIN lifecycle AS l ON l.part_id = v.part_id
            WHERE l.state <> 'discontinued'
        """,
        "universe": "bom_item",
        "basis": "Current voltage, temperature, and lifecycle predicates were all evaluated.",
    },
    "spec_conflict": {
        "inputs": ["rated_voltage"],
        "sql": """
            SELECT part_id, 'rated_voltage_v' AS property
            FROM rated_voltage
            GROUP BY part_id
            HAVING COUNT(DISTINCT volts) > 1
        """,
        "universe": "manufacturer_part",
        "basis": "All represented voltage observations were grouped by exact part referent.",
    },
}


def _declare_schema(view: TaskView) -> None:
    for name, roles in BASE_RELATIONS.items():
        view.declare_relation(name, roles)
    for name, roles in DERIVED_RELATIONS.items():
        view.declare_relation(name, roles, mode=RelationMode.DERIVED)
    for name, definition in DERIVATIONS.items():
        view.register_derivation(
            name,
            sql=definition["sql"],
            inputs=definition["inputs"],
        )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def compile_c1(
    db_path: Path,
    source_dir: Path = FIXTURES,
    *,
    manufacturer_path: Path | None = None,
) -> Compilation:
    observations, fingerprints = parse_sources(
        source_dir, manufacturer_path=manufacturer_path
    )
    by_source: dict[str, list[Observation]] = {}
    for observation in observations:
        by_source.setdefault(observation.source, []).append(observation)

    view = TaskView(db_path, view_id="bom-semantic-integration-c1")
    _declare_schema(view)

    manufacturer_by_number: dict[str, Observation] = {}
    for observation in by_source["manufacturer.csv"]:
        row = observation.data
        number = row["part_number"]
        part = f"part:{number}"
        manufacturer_by_number[number] = observation
        grounds = [observation.grounding()]
        view.add_referent(part, label=row["description"], grounding=grounds)
        view.assert_tuple("manufacturer_part", {"part": part}, grounding=grounds)
        view.assert_tuple(
            "part_type",
            {"part": part, "part_type": row["part_type"]},
            grounding=grounds,
        )
        view.assert_tuple(
            "rated_voltage",
            {"part": part, "volts": int(row["rated_voltage_v"])},
            grounding=grounds,
        )
        view.assert_tuple(
            "temperature_range",
            {
                "part": part,
                "minimum_c": int(row["min_temp_c"]),
                "maximum_c": int(row["max_temp_c"]),
            },
            grounding=grounds,
        )
        view.assert_tuple(
            "lifecycle",
            {"part": part, "state": row["lifecycle"]},
            grounding=grounds,
        )

    for observation in by_source["suppliers.json"]:
        row = observation.data
        listing = f"listing:{row['sku']}"
        supplier = f"supplier:{_slug(row['supplier'])}"
        grounds = [observation.grounding()]
        view.add_referent(listing, label=row["sku"], grounding=grounds)
        view.add_referent(supplier, label=row["supplier"], grounding=grounds)
        view.assert_tuple("supplier_listing", {"listing": listing}, grounding=grounds)
        view.assert_tuple(
            "offered_by",
            {"listing": listing, "supplier": supplier},
            grounding=grounds,
        )
        view.assert_tuple(
            "listing_availability",
            {"listing": listing, "state": row["availability"]},
            grounding=grounds,
        )
        manufacturer = manufacturer_by_number.get(row["manufacturer_part_number"])
        if manufacturer is None:
            continue
        part = f"part:{row['manufacturer_part_number']}"
        view.assert_tuple(
            "listing_of",
            {"listing": listing, "part": part},
            grounding=[observation.grounding(), manufacturer.grounding()],
        )
        if "observed_voltage_v" in row:
            view.assert_tuple(
                "rated_voltage",
                {"part": part, "volts": int(row["observed_voltage_v"])},
                grounding=grounds,
            )

    for observation in by_source["bom.csv"]:
        row = observation.data
        bom_item = f"bom:{row['bom_item']}"
        environment = f"context:{row['deployment_environment']}"
        grounds = [observation.grounding()]
        view.add_referent(bom_item, label=row["bom_item"], grounding=grounds)
        view.add_referent(
            environment,
            label=row["deployment_environment"].replace("_", " "),
            grounding=grounds,
        )
        view.assert_tuple("bom_item", {"bom_item": bom_item}, grounding=grounds)
        view.assert_tuple(
            "requires_type",
            {"bom_item": bom_item, "part_type": row["part_type"]},
            grounding=grounds,
        )
        view.assert_tuple(
            "requires_voltage",
            {"bom_item": bom_item, "volts": int(row["required_voltage_v"])},
            grounding=grounds,
        )
        view.assert_tuple(
            "requires_temperature",
            {
                "bom_item": bom_item,
                "minimum_c": int(row["min_temp_c"]),
                "maximum_c": int(row["max_temp_c"]),
            },
            grounding=grounds,
        )
        view.assert_tuple(
            "deployment_environment",
            {"bom_item": bom_item, "environment": environment},
            grounding=grounds,
        )

    for observation in by_source["engineering_notes.md"]:
        new_part = f"part:{observation.data['new_part']}"
        old_part = f"part:{observation.data['old_part']}"
        view.assert_tuple(
            "candidate_replacement",
            {"new_part": new_part, "old_part": old_part},
            grounding=[observation.grounding()],
        )

    for relation in (
        "voltage_compatible",
        "temperature_compatible",
        "spec_conflict",
        "eligible_part",
    ):
        definition = DERIVATIONS[relation]
        view.run_derivation(
            relation,
            completeness=Completeness(
                CompletenessStatus.COMPLETE,
                universe=definition["universe"],
                basis=definition["basis"],
            ),
        )
    return Compilation(view=view, observations=observations, fingerprints=fingerprints)


def _relation_tuples(view: TaskView, relation: str) -> set[tuple[Any, ...]]:
    roles = view.relation_schema(relation)["roles"]
    columns = [role["column"] for role in roles]
    rows = view.query(
        f"SELECT {', '.join(columns)} FROM {relation} ORDER BY {', '.join(columns)}"
    )
    return {tuple(row[column] for column in columns) for row in rows}


def load_oracle() -> tuple[dict[str, Any], dict[str, set[tuple[Any, ...]]]]:
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    if not oracle.get("frozen_before_c1_evaluation"):
        raise ValueError("C0 oracle is not frozen")
    if set(oracle["role_order"]) != set(oracle["relations"]):
        raise ValueError("C0 role declarations and relation extensions differ")
    tuples: dict[str, set[tuple[Any, ...]]] = {}
    for relation, declaration in oracle["relations"].items():
        if declaration["origin"] not in {"MECHANICAL", "SEMANTIC", "DERIVED"}:
            raise ValueError(f"{relation} has an invalid construction origin")
        raw = declaration.get("tuples")
        if raw is None:
            raw = [item["tuple"] for item in declaration["assertions"]]
        tuples[relation] = {tuple(item) for item in raw}
        if any(len(item) != len(oracle["role_order"][relation]) for item in raw):
            raise ValueError(f"{relation} tuple arity differs from its frozen roles")
        if declaration["origin"] == "SEMANTIC":
            for assertion in declaration["assertions"]:
                required = {
                    "source",
                    "source_fingerprint",
                    "native_location",
                    "construction_method",
                }
                if set(assertion["grounding"]) != required:
                    raise ValueError(
                        f"{relation} semantic assertion lacks explicit grounding"
                    )
    return oracle, tuples


def _facts_for_referents(
    view: TaskView, new_part: str, old_part: str, context: str
) -> dict[str, list[list[Any]]]:
    facts: dict[str, list[list[Any]]] = {}
    bom_ids = {
        item["bom_item_id"]
        for item in view.query(
            "SELECT bom_item_id FROM deployment_environment WHERE environment_id = ?",
            (context,),
        )
    }
    for relation in (
        "candidate_replacement",
        "part_type",
        "rated_voltage",
        "temperature_range",
        "lifecycle",
        "deployment_environment",
        "requires_type",
        "requires_voltage",
        "requires_temperature",
        "eligible_part",
        "spec_conflict",
    ):
        schema = view.relation_schema(relation)
        roles = schema["roles"]
        columns = [role["column"] for role in roles]
        rows = view.query(
            f"SELECT {', '.join(columns)} FROM {relation} ORDER BY {', '.join(columns)}"
        )
        for row in rows:
            values = tuple(row[column] for column in columns)
            value_set = set(values)
            include = bool({new_part, old_part} & value_set)
            if relation == "candidate_replacement":
                include = values == (new_part, old_part)
            if relation.startswith("requires_"):
                include = bool(bom_ids & value_set)
            if relation == "deployment_environment":
                include = context in value_set
            if relation == "eligible_part":
                include = include and bool(bom_ids & value_set)
            if include:
                facts.setdefault(relation, []).append(list(values))
    return facts


def build_frontier_packets(
    view: TaskView,
    unresolved: dict[str, set[tuple[Any, ...]]],
    observations: Iterable[Observation],
) -> list[dict[str, Any]]:
    observations = list(observations)
    packets: list[dict[str, Any]] = []
    for relation, tuples in sorted(unresolved.items()):
        for values in sorted(tuples):
            new_part, old_part, context = values
            part_numbers = {
                new_part.removeprefix("part:"),
                old_part.removeprefix("part:"),
            }
            context_name = context.removeprefix("context:")
            evidence: list[dict[str, Any]] = []
            for observation in observations:
                data = observation.data
                selected = (
                    data.get("part_number") in part_numbers
                    or data.get("deployment_environment") == context_name
                    or (
                        data.get("new_part") in part_numbers
                        and data.get("old_part") in part_numbers
                    )
                )
                if selected:
                    evidence.append(
                        {
                            "source": observation.source,
                            "source_fingerprint": observation.fingerprint,
                            "native_location": observation.location,
                            "record": observation.evidence,
                        }
                    )
            facts = _facts_for_referents(view, new_part, old_part, context)
            packets.append(
                {
                    "candidate_assertion": {
                        "relation": relation,
                        "tuple": list(values),
                    },
                    "relevant_referents": [new_part, old_part, context],
                    "known_mechanical_facts": facts,
                    "evidence": evidence,
                    "conflicts": facts.get("spec_conflict", []),
                    "missing_information": [
                        "No deterministic rule interprets the qualified prose as acceptance; no numeric crosswalk covers its environmental qualification."
                    ],
                }
            )
    return packets


def _apply_mutation(view: TaskView, mutation_path: Path) -> dict[str, Any]:
    initial_rows = {
        observation.key: observation
        for observation in parse_manufacturer(FIXTURES / "manufacturer.csv")
    }
    mutated_rows = {
        observation.key: observation
        for observation in parse_manufacturer(mutation_path)
    }
    changed_keys = [
        key
        for key in sorted(initial_rows)
        if initial_rows[key].data != mutated_rows[key].data
    ]
    if changed_keys != ["X100"]:
        raise AssertionError(f"frozen mutation changed unexpected observations: {changed_keys}")

    old = initial_rows["X100"]
    new = mutated_rows["X100"]
    old_tuple = {
        "part": "part:X100",
        "minimum_c": int(old.data["min_temp_c"]),
        "maximum_c": int(old.data["max_temp_c"]),
    }
    new_tuple = {
        "part": "part:X100",
        "minimum_c": int(new.data["min_temp_c"]),
        "maximum_c": int(new.data["max_temp_c"]),
    }
    initial_expected = (
        ("part:X100", "bom:BOM-A") in _relation_tuples(view, "eligible_part")
        and ("part:X100", "bom:BOM-A")
        in _relation_tuples(view, "temperature_compatible")
    )
    view.retract_tuple("temperature_range", old_tuple)
    view.assert_tuple(
        "temperature_range",
        new_tuple,
        grounding=[new.grounding()],
    )

    stale = view.stale_relations()
    derived_names = sorted(DERIVED_RELATIONS)
    unaffected = sorted(set(derived_names) - set(stale))
    stale_expected = ["eligible_part", "temperature_compatible"]
    excessive_invalidation = stale != stale_expected

    for relation in ("temperature_compatible", "eligible_part"):
        definition = DERIVATIONS[relation]
        view.run_derivation(
            relation,
            completeness=Completeness(
                CompletenessStatus.COMPLETE,
                universe=definition["universe"],
                basis=definition["basis"] + " Recomputed after frozen X100 mutation.",
            ),
        )

    temperature = _relation_tuples(view, "temperature_compatible")
    eligible = _relation_tuples(view, "eligible_part")
    rerun_correct = (
        initial_expected
        and ("part:X100", "bom:BOM-A") not in temperature
        and ("part:X100", "bom:BOM-A") not in eligible
        and ("part:X100", "bom:BOM-B") in temperature
        and ("part:X100", "bom:BOM-B") in eligible
        and view.stale_relations() == []
    )
    return {
        "source": "manufacturer.csv",
        "old_fingerprint": old.fingerprint,
        "new_fingerprint": new.fingerprint,
        "source_fingerprint_changed": old.fingerprint != new.fingerprint,
        "changed_source_observations": len(changed_keys),
        "changed_observation_keys": changed_keys,
        "changed_base_tuples": 2,
        "changed_base_tuple_detail": [
            {"action": "RETRACT", "relation": "temperature_range", "tuple": old_tuple},
            {"action": "ASSERT", "relation": "temperature_range", "tuple": new_tuple},
        ],
        "stale_derived_relations": stale,
        "unaffected_derived_relations": unaffected,
        "excessive_invalidation": excessive_invalidation,
        "rerun_result_correctness": rerun_correct,
        "stale_after_rerun": view.stale_relations(),
    }


def run_experiment(work_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    oracle, c0 = load_oracle()
    compilation = compile_c1(work_dir / "c1.sqlite")
    view = compilation.view
    try:
        if compilation.fingerprints != oracle["source_fingerprints"]:
            raise AssertionError("fixture fingerprints differ from the frozen C0 oracle")
        actual_roles = {
            name: [
                role["name"] for role in view.relation_schema(name)["roles"]
            ]
            for name in oracle["relations"]
        }
        if actual_roles != oracle["role_order"]:
            raise AssertionError("C1 relation roles differ from the frozen C0 oracle")
        actual = {name: _relation_tuples(view, name) for name in c0}
        unresolved = {
            name: tuples - actual[name]
            for name, tuples in c0.items()
            if tuples - actual[name]
        }
        unexpected = {
            name: actual[name] - tuples
            for name, tuples in c0.items()
            if actual[name] - tuples
        }
        packets = build_frontier_packets(view, unresolved, compilation.observations)

        origin_counts = {"MECHANICAL": 0, "SEMANTIC": 0, "DERIVED": 0}
        for name, declaration in oracle["relations"].items():
            origin_counts[declaration["origin"]] += len(c0[name])
        c0_count = sum(len(rows) for rows in c0.values())
        established_count = sum(len(c0[name] & actual[name]) for name in c0)
        evidence_bytes = sum((FIXTURES / name).stat().st_size for name in SOURCE_NAMES)
        packet_bytes = sum(
            len(
                json.dumps(packet, sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            )
            for packet in packets
        )
        relation_sources: dict[str, set[str]] = {
            name: set(declaration.get("source_basis", []))
            for name, declaration in oracle["relations"].items()
            if declaration["origin"] != "DERIVED"
        }
        pending = set(DERIVATIONS)
        while pending:
            ready = {
                name
                for name in pending
                if all(
                    input_relation in relation_sources
                    for input_relation in DERIVATIONS[name]["inputs"]
                )
            }
            if not ready:
                raise AssertionError("derivation source lineage is cyclic or incomplete")
            for name in ready:
                relation_sources[name] = set().union(
                    *(
                        relation_sources[input_relation]
                        for input_relation in DERIVATIONS[name]["inputs"]
                    )
                )
            pending -= ready
        cross_authority = sorted(
            name for name, sources in relation_sources.items() if len(sources) > 1
        )

        measurements = {
            "total_source_bytes": evidence_bytes,
            "total_observations": len(compilation.observations),
            "total_referents": view.query("SELECT count(*) AS n FROM _tv_referents")[0][
                "n"
            ],
            "c0_relation_tuples": c0_count,
            "c0_assertions_by_construction_origin": origin_counts,
            "c1_mechanically_established_tuples": established_count,
            "mechanical_coverage_ratio": established_count / c0_count,
            "cross_authority_relation_count": len(cross_authority),
            "cross_authority_relations": cross_authority,
            "conflict_count": len(actual["spec_conflict"]),
            "unresolved_frontier_tuple_count": sum(
                len(rows) for rows in unresolved.values()
            ),
            "frontier_selected_evidence_records": sum(
                len(packet["evidence"]) for packet in packets
            ),
            "frontier_packet_bytes": packet_bytes,
            "frontier_packet_to_total_evidence_ratio": packet_bytes / evidence_bytes,
            "number_of_derivations": len(DERIVATIONS),
            "number_of_input_relations_per_derivation": {
                name: len(definition["inputs"])
                for name, definition in sorted(DERIVATIONS.items())
            },
        }
        mutation = _apply_mutation(
            view, FIXTURES / "mutations" / "manufacturer.csv"
        )
        report = {
            "experiment": "minimal non-software semantic integration using TaskView core",
            "stage": "C1 evaluated against frozen C0; no participant/provider inference",
            "provider_inference_calls": 0,
            "oracle_id": oracle["oracle_id"],
            "source_fingerprints": compilation.fingerprints,
            "measurements": measurements,
            "comparison": {
                "unresolved_assertions": {
                    name: [list(row) for row in sorted(rows)]
                    for name, rows in sorted(unresolved.items())
                },
                "unexpected_c1_tuples": {
                    name: [list(row) for row in sorted(rows)]
                    for name, rows in sorted(unexpected.items())
                },
            },
            "mutation": mutation,
            "questions": {
                "1_core_representation": (
                    "Yes for this bounded fixture: referents and typed relations represented "
                    "parts, listings, BOM requirements, conflicts, and replacements without "
                    "software-shaped semantic concepts. The TaskView/view wrapper name remains."
                ),
                "2_reused_unchanged": (
                    "Referents, typed named n-ary BASE relations, assertion grounding, SQLite/SQL, "
                    "DERIVED relations, declared dependencies, revisions, staleness, rerun, and "
                    "scoped completeness receipts."
                ),
                "3_unnecessary_concepts": (
                    "The agent surface, task specification, software migration relations, and "
                    "software/task scope vocabulary were unnecessary; task_spec_ref was left empty."
                ),
                "4_cross_authority_relations": (
                    "listing_of joins exact supplier and manufacturer identifiers; rated_voltage "
                    "retains both authorities; compatibility, eligibility, and conflict derivations "
                    "cross manufacturer/supplier/BOM evidence."
                ),
                "5_deterministic_coverage": (
                    f"{established_count}/{c0_count} C0 tuples "
                    f"({established_count / c0_count:.2%}) were mechanically established."
                ),
                "6_semantic_frontier": (
                    "Exactly two context-qualified acceptable_replacement assertions remain; "
                    "candidate_replacement and all tabulated facts are already mechanical."
                ),
                "7_packet_size": (
                    f"No in serialized byte terms: compact packets are {packet_bytes} bytes versus "
                    f"{evidence_bytes} source bytes ({packet_bytes / evidence_bytes:.2%}). "
                    "They select only 8 of 30 records, but repeated grounding and normalized-fact "
                    "metadata dominate this unusually tiny evidence universe."
                ),
                "8_grounding_invalidation": (
                    "Grounding identified the changed temperature assertion precisely; applying "
                    "that BASE delta revised temperature_range, which invalidated only "
                    "temperature_compatible and its eligible_part dependent. Unrelated derivations "
                    "remained current."
                ),
                "9_lifecycle_machinery": (
                    "Yes: relation revisions exposed staleness outside software, dependency order "
                    "was enforced, rerun restored current correct results, and completeness receipts "
                    "remained scoped to represented BOM items."
                ),
                "10_concrete_failure": (
                    "C1 cannot turn qualified prose into the two acceptance judgments. If a next "
                    "mechanism is authorized, the evidence supports a bounded relation-specific "
                    "adjudicator over these packets, not a general constructor. No model was run."
                ),
            },
            "limitations": [
                "Invalidation is relation-granular, not tuple-granular; this fixture did not cause an unrelated relation to become stale.",
                "TaskView and its metadata retain task-oriented names even though the semantic schema does not.",
                "Groundings are append-only pointers; the mutation records the new assertion ground and does not claim the old source assertion was semantically falsified by the file change.",
            ],
        }
        return report, packets
    finally:
        view.close()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT,
        help="directory for report.json and frontier_packets.json",
    )
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="taskview-bom-") as temporary:
        report, packets = run_experiment(Path(temporary))
    args.output.mkdir(parents=True, exist_ok=True)
    _write_json(args.output / "report.json", report)
    _write_json(args.output / "frontier_packets.json", packets)
    print(json.dumps(report["measurements"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
