"""Host-side compiler smoke. Not a model trial. Not shown to agents."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.compiler import compile_program
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.paths import STRUCTURED
from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.workspaces import document_inventory


PROGRAM = {
    "referents": [
        {"name": "Measurement", "key": ["permit_id", "outfall", "parameter_code", "period_end", "value_type"]},
        {"name": "Limit", "key": ["permit_id", "outfall", "parameter_code", "begin_date", "end_date", "value_type"]},
        {"name": "Document", "key": ["permit", "filename"]},
    ],
    "maps": [
        {
            "id": "map_dmr",
            "source": "dmr_measurements.csv",
            "referent": "Measurement",
            "fields": {
                "permit_id": "EXTERNAL_PERMIT_NMBR",
                "outfall": "PERM_FEATURE_NMBR",
                "parameter_code": "PARAMETER_CODE",
                "period_end": "MONITORING_PERIOD_END_DATE",
                "value_type": "VALUE_TYPE_CODE",
                "nodi_code": "NODI_CODE",
                "measured_value": "DMR_VALUE_NMBR",
            },
        },
        {
            "id": "map_limit",
            "source": "permit_limits.csv",
            "referent": "Limit",
            "fields": {
                "permit_id": "EXTERNAL_PERMIT_NMBR",
                "outfall": "PERM_FEATURE_NMBR",
                "parameter_code": "PARAMETER_CODE",
                "begin_date": "LIMIT_BEGIN_DATE",
                "end_date": "LIMIT_END_DATE",
                "value_type": "LIMIT_VALUE_TYPE_CODE",
                "limit_value": "LIMIT_VALUE_NMBR",
                "qualifier": "LIMIT_VALUE_QUALIFIER_CODE",
                "comment": "DMR_COMMENT_TEXT",
                "limit_set_name": "LIMIT_SET_NAME",
            },
        },
        {
            "id": "map_doc",
            "source": "document_inventory.json",
            "referent": "Document",
            "fields": {
                "permit": "permit",
                "filename": "filename",
                "document_kind": "document_kind",
            },
        },
    ],
    "relations": [
        {
            "name": "measurement",
            "kind": "base",
            "map": "map_dmr",
            "roles": [
                {"name": "measurement", "type": "REFERENT", "field": "_referent"},
                {"name": "permit_id", "type": "TEXT", "field": "permit_id"},
                {"name": "outfall", "type": "TEXT", "field": "outfall"},
                {"name": "parameter_code", "type": "TEXT", "field": "parameter_code"},
                {"name": "period_end", "type": "TEXT", "field": "period_end"},
                {"name": "nodi_code", "type": "TEXT", "field": "nodi_code"},
            ],
        },
        {
            "name": "limit_row",
            "kind": "base",
            "map": "map_limit",
            "roles": [
                {"name": "limit", "type": "REFERENT", "field": "_referent"},
                {"name": "permit_id", "type": "TEXT", "field": "permit_id"},
                {"name": "outfall", "type": "TEXT", "field": "outfall"},
                {"name": "parameter_code", "type": "TEXT", "field": "parameter_code"},
                {"name": "begin_date", "type": "TEXT", "field": "begin_date"},
                {"name": "end_date", "type": "TEXT", "field": "end_date"},
                {"name": "limit_value", "type": "TEXT", "field": "limit_value"},
                {"name": "qualifier", "type": "TEXT", "field": "qualifier"},
                {"name": "comment", "type": "TEXT", "field": "comment"},
                {"name": "limit_set_name", "type": "TEXT", "field": "limit_set_name"},
            ],
        },
        {
            "name": "source_document",
            "kind": "base",
            "map": "map_doc",
            "roles": [
                {"name": "document", "type": "REFERENT", "field": "_referent"},
                {"name": "permit", "type": "TEXT", "field": "permit"},
                {"name": "filename", "type": "TEXT", "field": "filename"},
                {"name": "document_kind", "type": "TEXT", "field": "document_kind"},
            ],
        },
        {
            "name": "candidate_limit",
            "kind": "derived",
            "from": ["measurement", "limit_row"],
            "roles": [
                {"name": "measurement", "type": "REFERENT", "from_role": "measurement.measurement"},
                {"name": "limit", "type": "REFERENT", "from_role": "limit_row.limit"},
                {"name": "permit_id", "type": "TEXT", "from_role": "measurement.permit_id"},
                {"name": "parameter_code", "type": "TEXT", "from_role": "measurement.parameter_code"},
                {"name": "period_end", "type": "TEXT", "from_role": "measurement.period_end"},
                {"name": "begin_date", "type": "TEXT", "from_role": "limit_row.begin_date"},
                {"name": "end_date", "type": "TEXT", "from_role": "limit_row.end_date"},
                {"name": "limit_value", "type": "TEXT", "from_role": "limit_row.limit_value"},
                {"name": "comment", "type": "TEXT", "from_role": "limit_row.comment"},
                {"name": "nodi_code", "type": "TEXT", "from_role": "measurement.nodi_code"},
            ],
            "match": [
                {"left": "measurement.permit_id", "right": "limit_row.permit_id"},
                {"left": "measurement.outfall", "right": "limit_row.outfall"},
                {"left": "measurement.parameter_code", "right": "limit_row.parameter_code"},
            ],
            "where": [
                {
                    "op": "interval_contains",
                    "point": "measurement.period_end",
                    "begin": "limit_row.begin_date",
                    "end": "limit_row.end_date",
                }
            ],
        },
    ],
    "requirements": [
        {
            "id": "applicable_limit",
            "purpose": ["A"],
            "over": "candidate_limit",
            "group_by": ["measurement"],
            "cardinality": "ONE",
            "require_numeric": ["limit_value"],
            "require_interpreted_code": {"field": "nodi_code", "known": [""]},
        },
        {
            "id": "untensed_parameter_limit",
            "purpose": ["A"],
            "over": "limit_row",
            "group_by": ["permit_id", "outfall", "parameter_code"],
            "cardinality": "ONE",
        },
        {
            "id": "comment_codes",
            "purpose": ["B"],
            "over": "limit_row",
            "group_by": ["comment"],
            "require_interpreted_code": {"field": "comment", "known": [""]},
        },
        {
            "id": "one_operative_document",
            "purpose": ["A"],
            "over": "source_document",
            "group_by": ["permit"],
            "cardinality": "ONE",
        },
    ],
}


def main() -> None:
    import shutil
    import tempfile

    tmp_root = Path(tempfile.mkdtemp(prefix="spine-compiler-smoke-"))
    try:
        for name in ("dmr_measurements.csv", "permit_limits.csv"):
            (tmp_root / name).write_bytes((STRUCTURED / name).read_bytes())
        (tmp_root / "document_inventory.json").write_text(
            json.dumps(document_inventory()), encoding="utf-8"
        )
        result = compile_program(PROGRAM, tmp_root)
        kinds = sorted({g["failure_kind"] for g in result["trigger_groups"]})
        print("valid", result["structurally_valid"])
        print("errors", result["errors"])
        print("rows", result["relation_row_counts"])
        print("groups", result["n_trigger_groups"], "instances", result["n_trigger_instances"])
        print("kinds", kinds)
        for group in result["trigger_groups"]:
            print(
                group["failure_kind"],
                group["requirement_id"],
                group["n_instances"],
                (group.get("sample_subjects") or [])[:1],
            )
        if not result["structurally_valid"]:
            raise SystemExit(1)
        needed = {
            "CARDINALITY_OVERSATISFIED",
            "MULTIPLE_CANDIDATES",
            "COMPARISON_OPERATOR_REQUIRED",
            "UNINTERPRETED_REQUIRED_CODE",
        }
        missing = needed - set(kinds)
        if missing:
            raise SystemExit(f"smoke missing diagnostics {missing}")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
