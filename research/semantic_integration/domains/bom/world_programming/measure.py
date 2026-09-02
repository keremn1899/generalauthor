"""AST/code-review measurements for RAW vs WORLD analysis programs."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "raw"
WORLD_DIR = ROOT / "world"

SOURCE_FIELDS = {
    "part_number",
    "part_type",
    "description",
    "rated_voltage_v",
    "min_temp_c",
    "max_temp_c",
    "lifecycle",
    "bom_item",
    "required_voltage_v",
    "deployment_environment",
    "sku",
    "supplier",
    "manufacturer_part_number",
    "availability",
    "observed_voltage_v",
    "listings",
}

RELATIONS = {
    "candidate_replacement",
    "acceptable_replacement",
    "eligible_part",
    "voltage_compatible",
    "temperature_compatible",
    "lifecycle",
    "part_type",
    "requires_type",
    "deployment_environment",
    "spec_conflict",
    "rated_voltage",
    "listing_of",
    "listing_availability",
}

ID_PREFIXES = ("part:", "bom:", "context:", "listing:")


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _string_literals(tree: ast.AST) -> list[str]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def _count_calls(tree: ast.AST, names: set[str]) -> int:
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in names:
                count += 1
            elif isinstance(func, ast.Attribute) and func.attr in names:
                count += 1
    return count


def _line_count(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    return len([line for line in lines if line.strip() and not line.strip().startswith("#")])


def review_file(path: Path, *, kind: str) -> dict[str, Any]:
    tree = _parse(path)
    literals = _string_literals(tree)
    field_refs = sorted(
        {value for value in literals if value in SOURCE_FIELDS}
        if kind == "raw"
        else set()
    )
    relation_refs = sorted(
        {
            name
            for value in literals
            for name in RELATIONS
            if name in value
        }
    )
    id_normalizations = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.JoinedStr)
        or (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in ID_PREFIXES
        )
    )
    parsers = {
        "csv_dict_reader": _count_calls(tree, {"DictReader"}),
        "json_loads": _count_calls(tree, {"loads"}),
        "regex": _count_calls(tree, {"compile", "findall", "fullmatch"}),
        "path_read_text": _count_calls(tree, {"read_text"}),
        "path_open": _count_calls(tree, {"open"}),
    }
    query_calls = _count_calls(tree, {"query", "query_semantic", "inspect_tuple", "relation_rows"})
    return {
        "path": str(path.relative_to(ROOT)),
        "kind": kind,
        "nonempty_lines": _line_count(path),
        "parsers": parsers,
        "source_schema_field_references": field_refs,
        "source_schema_field_count": len(field_refs),
        "relation_references": relation_refs,
        "identifier_normalization_nodes": id_normalizations,
        "query_or_inspect_calls": query_calls,
        "inspect_tuple_calls": _count_calls(tree, {"inspect_tuple"}),
    }


def burden_inventory() -> dict[str, Any]:
    raw_files = [
        RAW_DIR / "io.py",
        RAW_DIR / "analysis_a.py",
        RAW_DIR / "analysis_b.py",
        RAW_DIR / "analysis_c.py",
    ]
    world_files = [
        WORLD_DIR / "analysis_a.py",
        WORLD_DIR / "analysis_b.py",
        WORLD_DIR / "analysis_c.py",
        ROOT / "relation_rows.py",
    ]
    raw = [review_file(path, kind="raw") for path in raw_files]
    world = [review_file(path, kind="world") for path in world_files]
    return {
        "raw": raw,
        "world": world,
        "raw_nonempty_lines": sum(item["nonempty_lines"] for item in raw),
        "world_nonempty_lines": sum(item["nonempty_lines"] for item in world),
        "raw_preparation_lines": next(
            item["nonempty_lines"] for item in raw if item["path"].endswith("io.py")
        ),
        "raw_analysis_lines": sum(
            item["nonempty_lines"] for item in raw if "analysis_" in item["path"]
        ),
        "world_analysis_lines": sum(
            item["nonempty_lines"] for item in world if "analysis_" in item["path"]
        ),
        "raw_source_field_union": sorted(
            {field for item in raw for field in item["source_schema_field_references"]}
        ),
        "world_source_field_union": sorted(
            {field for item in world for field in item["source_schema_field_references"]}
        ),
        "world_relation_union": sorted(
            {name for item in world for name in item["relation_references"]}
        ),
    }
