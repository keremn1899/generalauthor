"""Diagnostic measures of a saved analysis program.  Not a value metric."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

SOURCE_FIELDS = {
    "part_number",
    "part_type",
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


def program_burden(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            "exists": True,
            "syntax_ok": False,
            "nonempty_lines": len(
                [line for line in source.splitlines() if line.strip()]
            ),
        }
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)

    def calls(names: set[str]) -> int:
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in names:
                    count += 1
                elif isinstance(func, ast.Attribute) and func.attr in names:
                    count += 1
        return count

    sql_literals = [
        value
        for value in literals
        if "SELECT" in value.upper() or "JOIN" in value.upper()
    ]
    return {
        "exists": True,
        "syntax_ok": True,
        "nonempty_lines": len([line for line in source.splitlines() if line.strip()]),
        "source_schema_fields": sorted(
            {value for value in literals if value in SOURCE_FIELDS}
        ),
        "relation_references": sorted(
            {
                name
                for value in literals
                for name in RELATIONS
                if name in value
            }
        ),
        "parser_calls": {
            "DictReader": calls({"DictReader"}),
            "json_loads": calls({"loads"}),
            "re": calls({"compile", "findall", "fullmatch"}),
        },
        "sql_statements": len(sql_literals),
        "inspect_tuple_calls": calls({"inspect_tuple"}),
        "open_world_calls": calls({"open_world"}),
    }
