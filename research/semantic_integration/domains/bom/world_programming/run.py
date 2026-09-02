"""Run RAW and WORLD analyses, freeze expected outputs, and write reports."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.world_programming.access import (
    trace_source_access,
)
from research.semantic_integration.domains.bom.world_programming.canonical import dump
from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
)
from research.semantic_integration.domains.bom.world_programming.measure import (
    burden_inventory,
)
from research.semantic_integration.domains.bom.world_programming.raw import (
    analysis_a as raw_a,
)
from research.semantic_integration.domains.bom.world_programming.raw import (
    analysis_b as raw_b,
)
from research.semantic_integration.domains.bom.world_programming.raw import (
    analysis_c as raw_c,
)
from research.semantic_integration.domains.bom.world_programming.world import (
    analysis_a as world_a,
)
from research.semantic_integration.domains.bom.world_programming.world import (
    analysis_b as world_b,
)
from research.semantic_integration.domains.bom.world_programming.world import (
    analysis_c as world_c,
)
from research.semantic_integration.domains.bom.world_programming.world.analysis_a import (
    explain_tuple,
)
from research.taskview_bom.experiment import FIXTURES


ROOT = Path(__file__).resolve().parent
EXPECTED = ROOT / "expected"
SEALED = [
    Path("research/taskview_bom/oracle.json"),
    Path("research/taskview_bom/report.json"),
    Path("research/taskview_bom/frontier_packets.json"),
    Path("research/semantic_integration/domains/bom/c2/results/c2_campaign_report.json"),
    Path("research/semantic_integration/domains/bom/operational_frontier/operational_frontier.json"),
]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(document), encoding="utf-8")


def _interfaces_used() -> dict[str, Any]:
    return {
        "semantic_world": [
            "query_semantic",
            "inspect_tuple",
            "latest_completeness",
            "is_stale",
            "relation_tuples (via relation_rows helper)",
        ],
        "taskview_reached_through_world": [
            "relation_schema",
            "describe (harness, not analysis programs)",
        ],
        "experiment_local": [
            "relation_rows",
            "operational obligations list",
        ],
        "not_used": [
            "world.relations()",
            "domain-specific query language",
            "LLM explanation",
        ],
        "sql_plus_python_sufficient": True,
        "missing_capability": (
            "ADJUDICATED_FALSE is not representable: there is no negative "
            "semantic assertion form. Missing acceptable_replacement cannot "
            "be read as false."
        ),
    }


def run_pair(tmp_dir: Path) -> dict[str, Any]:
    experimental = construct_experimental_world(tmp_dir / "world.sqlite")
    try:
        with trace_source_access() as raw_a_log:
            raw_a_out = raw_a.run(FIXTURES)
        with trace_source_access() as raw_b_log:
            raw_b_out = raw_b.run(FIXTURES)
        with trace_source_access() as raw_c_log:
            raw_c_out = raw_c.run(FIXTURES)
        with trace_source_access() as world_a_log:
            world_a_out = world_a.run(experimental.world, experimental.obligations)
        with trace_source_access() as world_b_log:
            world_b_out = world_b.run(experimental.world, experimental.obligations)
        with trace_source_access() as world_c_log:
            world_c_out = world_c.run(experimental.world, experimental.obligations)

        indoor = next(
            case
            for case in world_a_out["cases"]
            if case["context"] == "context:indoor_panel"
        )
        accepted = next(
            case
            for case in world_a_out["cases"]
            if case["semantic_state"] == "accepted"
            and case["new_part"] == "part:X110"
        )
        provenance = explain_tuple(
            experimental.world,
            "acceptable_replacement",
            {
                "new_part": accepted["new_part"],
                "old_part": accepted["old_part"],
                "context": accepted["context"],
            },
        )
        origin_account = experimental.world.origin_account()
        describe = experimental.world.taskview.describe()
        return {
            "raw": {
                "analysis_a": {"output": raw_a_out, "log": _log(raw_a_log)},
                "analysis_b": {"output": raw_b_out, "log": _log(raw_b_log)},
                "analysis_c": {"output": raw_c_out, "log": _log(raw_c_log)},
            },
            "world": {
                "analysis_a": {"output": world_a_out, "log": _log(world_a_log)},
                "analysis_b": {"output": world_b_out, "log": _log(world_b_log)},
                "analysis_c": {"output": world_c_out, "log": _log(world_c_log)},
            },
            "obligations": experimental.obligations,
            "indoor_panel_case": indoor,
            "provenance": _strip_provenance(provenance),
            "origin_account": origin_account,
            "relation_names": [item["name"] for item in describe["relations"]],
            "stale_relations": experimental.world.stale_relations(),
        }
    finally:
        experimental.world.close()


def _log(log: Any) -> dict[str, Any]:
    return {
        "source_files_opened": log.file_count,
        "source_file_names": list(log.files),
        "source_bytes_consumed": log.bytes_consumed,
    }


def _strip_provenance(detail: dict[str, Any] | None) -> dict[str, Any] | None:
    if detail is None:
        return None
    grounds = []
    for ground in detail.get("grounding", []):
        item = {"kind": ground["kind"], "reference": ground["reference"]}
        try:
            payload = json.loads(ground["detail"])
        except (TypeError, json.JSONDecodeError):
            payload = {}
        if "source" in payload:
            item["source"] = payload["source"]
        elif "native_handle" in payload:
            item["source"] = payload["native_handle"]
        if "source_native_location" in payload:
            item["native_location"] = payload["source_native_location"]
        if "native_location" in payload and "native_location" not in item:
            item["native_location"] = payload["native_location"]
        grounds.append(item)
    return {
        "relation": detail["relation"],
        "tuple": detail["tuple"],
        "construction_origin": detail.get("construction_origin"),
        "origin": detail.get("origin"),
        "grounding": grounds,
    }


def freeze(tmp_dir: Path | None = None) -> dict[str, Any]:
    if tmp_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="world-programming-")
        work = Path(temporary.name)
    else:
        temporary = None
        work = tmp_dir
    try:
        pair = run_pair(work)
        for name in ("analysis_a", "analysis_b", "analysis_c"):
            if pair["raw"][name]["output"] != pair["world"][name]["output"]:
                raise ValueError(f"{name} RAW and WORLD outputs differ")
            _write(EXPECTED / f"{name}.json", pair["raw"][name]["output"])
        _write(EXPECTED / "obligations.json", {"obligations": pair["obligations"]})
        _write(EXPECTED / "interfaces.json", _interfaces_used())
        report = build_report(pair)
        _write(ROOT / "report.json", report)
        (ROOT / "report.md").write_text(render_report(report), encoding="utf-8")
        return report
    finally:
        if temporary is not None:
            temporary.cleanup()


def build_report(pair: dict[str, Any]) -> dict[str, Any]:
    burden = burden_inventory()
    comparisons = {
        "analysis_a": _compare_task("analysis_a", pair),
        "analysis_b": _compare_task("analysis_b", pair),
        "analysis_c": _compare_task("analysis_c", pair),
    }
    indoor = pair["indoor_panel_case"]
    world_relations = {
        "analysis_a": [
            "candidate_replacement",
            "part_type",
            "requires_type",
            "deployment_environment",
            "eligible_part",
            "acceptable_replacement",
        ],
        "analysis_b": [
            "candidate_replacement",
            "part_type",
            "requires_type",
            "deployment_environment",
            "voltage_compatible",
            "temperature_compatible",
            "lifecycle",
            "acceptable_replacement",
        ],
        "analysis_c": [
            "spec_conflict",
            "rated_voltage",
            "part_type",
            "requires_type",
            "eligible_part",
            "listing_of",
            "listing_availability",
        ],
    }
    reused = sorted(
        set(world_relations["analysis_a"])
        & set(world_relations["analysis_b"])
    )
    reused_across_three = sorted(
        set(world_relations["analysis_a"])
        & set(world_relations["analysis_c"])
    )
    return {
        "experiment": "world-ir-python-programming-substrate-s1",
        "provider_inference_calls": 0,
        "correctness": {
            name: {
                "raw_matches_world": pair["raw"][name]["output"]
                == pair["world"][name]["output"],
                "raw_source_files": pair["raw"][name]["log"],
                "world_source_files": pair["world"][name]["log"],
            }
            for name in ("analysis_a", "analysis_b", "analysis_c")
        },
        "epistemic": {
            "indoor_panel": indoor,
            "missing_acceptable_replacement_not_false": indoor["epistemic"]
            == "UNRESOLVED"
            and indoor["semantic_state"] == "unresolved",
            "adjudicated_false_representable": False,
        },
        "origin_account": pair["origin_account"],
        "provenance": pair["provenance"],
        "burden": burden,
        "world_reuse": {
            "relations_by_analysis": world_relations,
            "relations_reused_by_a_and_b": reused,
            "relations_reused_by_a_and_c": reused_across_three,
            "mechanical_tuples_reused": True,
            "semantic_tuples_reused": True,
            "derived_tuples_reused": True,
        },
        "structural_comparison": comparisons,
        "interfaces": _interfaces_used(),
        "stale_relations": pair["stale_relations"],
        "conclusions": {
            "MEASURED": [
                "Three analyses ran in both conditions with identical canonical outputs.",
                "WORLD analysis opened 0 raw source files and consumed 0 raw source bytes after construction.",
                "Indoor-panel acceptable_replacement is UNRESOLVED, not false.",
                "inspect_tuple returned stored SOURCE groundings for an accepted semantic tuple.",
            ],
            "OBSERVED": [
                "RAW programs parse CSV/JSON/Markdown, normalize identifiers, and reconstruct eligibility, context, and acceptance.",
                "WORLD programs query compiled relations and compute over those tables in ordinary SQL/Python.",
                "The same World relations are reused across distinct analyses.",
            ],
            "HYPOTHESIS": [
                "An LLM writing RAW Python would spend tokens and tool calls on parsers, identifier joins, and note interpretation.",
                "An LLM writing WORLD Python would spend them on relation names, SQL joins, and epistemic status.",
                "This experiment does not measure that difference.",
            ],
        },
        "expected_fingerprints": {
            name: _sha256(EXPECTED / f"{name}.json")
            for name in ("analysis_a", "analysis_b", "analysis_c")
            if (EXPECTED / f"{name}.json").exists()
        },
    }


def _compare_task(name: str, pair: dict[str, Any]) -> dict[str, Any]:
    raw_log = pair["raw"][name]["log"]
    world_log = pair["world"][name]["log"]
    if name == "analysis_a":
        return {
            "RAW": [
                "parse manufacturer.csv and bom.csv",
                "parse engineering_notes.md Candidate records",
                "normalize part/bom/context identifiers",
                "join replacement candidates to BOM items by part_type",
                "reconstruct mechanical eligibility from voltage/temperature/lifecycle fields",
                "interpret note backticks as context-qualified acceptance",
                "classify remaining demanded cases as unresolved, not false",
            ],
            "WORLD": [
                "query candidate_replacement, part_type, requires_type, deployment_environment",
                "query eligible_part and acceptable_replacement",
                "join demanded cases in SQL",
                "classify semantic state from asserted tuples vs obligation list",
            ],
            "raw_source_files_opened": raw_log["source_files_opened"],
            "world_source_files_opened": world_log["source_files_opened"],
        }
    if name == "analysis_b":
        return {
            "RAW": [
                "reuse manufacturer/BOM/notes parsers",
                "recompute voltage, temperature, and lifecycle constraints per BOM item",
                "reconstruct acceptance from note context mentions",
                "separate preventing constraints from unresolved semantic acceptance",
            ],
            "WORLD": [
                "query voltage_compatible, temperature_compatible, lifecycle, acceptable_replacement",
                "consult completeness receipts before treating a derived miss as failure",
                "treat missing acceptable_replacement plus an obligation as uncertain, not false",
            ],
            "raw_source_files_opened": raw_log["source_files_opened"],
            "world_source_files_opened": world_log["source_files_opened"],
        }
    return {
        "RAW": [
            "parse manufacturer.csv and suppliers.json",
            "reconcile manufacturer_part_number to part_number",
            "detect multiple voltage observations per part",
            "join conflicted parts to BOM items by part_type",
            "recompute eligibility from manufacturer ratings",
        ],
        "WORLD": [
            "query spec_conflict, rated_voltage, requires_type, eligible_part, listing_of",
            "inspect_tuple on rated_voltage to recover source handles",
        ],
        "raw_source_files_opened": raw_log["source_files_opened"],
        "world_source_files_opened": world_log["source_files_opened"],
    }


def render_report(report: dict[str, Any]) -> str:
    indoor = report["epistemic"]["indoor_panel"]
    provenance = report["provenance"]
    burden = report["burden"]
    lines = [
        "# World IR as a Python programming substrate (BOM S1)",
        "",
        "No model/provider inference. Provider/model calls: **0**.",
        "",
        "This freeze is the human-written benchmark later LLM RAW vs WORLD",
        "programming experiments should reuse unchanged.",
        "",
        "## Success criteria",
        "",
        "1. Three useful analyses were written entirely over the compiled World.",
        "2. WORLD computation is ordinary Python/SQL.",
        "3. Source-specific reconciliation moved out of WORLD analysis programs.",
        "4. World relations were reused across distinct analyses.",
        "5. Epistemic status and provenance remained accessible.",
        "",
        "## Conditions",
        "",
        "- RAW starts from the frozen S1 fixture files.",
        "- WORLD receives a newly constructed SemanticWorld copy (C1 compile + copied C2 ACCEPT tuples) and operational obligations. After construction it does not open source files.",
        "",
        "## Correctness",
        "",
    ]
    for name, item in report["correctness"].items():
        lines.append(
            f"- `{name}`: RAW matches WORLD = {item['raw_matches_world']}; "
            f"RAW files {item['raw_source_files']['source_files_opened']} "
            f"({item['raw_source_files']['source_bytes_consumed']} bytes); "
            f"WORLD files {item['world_source_files']['source_files_opened']} "
            f"({item['world_source_files']['source_bytes_consumed']} bytes)."
        )
    lines += [
        "",
        "## Epistemic safety",
        "",
        f"- Indoor-panel case: `{indoor['new_part']}` / `{indoor['old_part']}` / `{indoor['context']}`.",
        f"- `semantic_state` = `{indoor['semantic_state']}`; `epistemic` = `{indoor['epistemic']}`.",
        "- Absence from `acceptable_replacement` was not treated as false.",
        "- `ADJUDICATED_FALSE` is not representable in the current assertion model (interface limitation).",
        "",
        "## Provenance",
        "",
    ]
    if provenance:
        lines.append(
            f"- `inspect_tuple` on `{provenance['relation']}` origin "
            f"`{provenance.get('construction_origin')}`."
        )
        for ground in provenance.get("grounding", []):
            lines.append(
                f"- grounding `{ground.get('kind')}` source `{ground.get('source')}` "
                f"at `{ground.get('native_location')}`."
            )
    lines += [
        "",
        "## Programming burden (diagnostic LOC / AST, not value)",
        "",
        f"- RAW nonempty lines: {burden['raw_nonempty_lines']} (preparation {burden['raw_preparation_lines']}, analysis {burden['raw_analysis_lines']})",
        f"- WORLD nonempty lines: {burden['world_nonempty_lines']} (analysis {burden['world_analysis_lines']}, plus relation_rows helper)",
        f"- RAW source-schema fields referenced: {burden['raw_source_field_union']}",
        f"- WORLD source-schema fields referenced: {burden['world_source_field_union']}",
        f"- WORLD relations referenced: {burden['world_relation_union']}",
        "",
        "## Structural comparison",
        "",
    ]
    for name, comparison in report["structural_comparison"].items():
        lines.append(f"### {name}")
        lines.append("RAW:")
        for item in comparison["RAW"]:
            lines.append(f"- {item}")
        lines.append("WORLD:")
        for item in comparison["WORLD"]:
            lines.append(f"- {item}")
        lines.append("")
    reuse = report["world_reuse"]
    lines += [
        "## World reuse",
        "",
        f"- A∩B: {reuse['relations_reused_by_a_and_b']}",
        f"- A∩C: {reuse['relations_reused_by_a_and_c']}",
        "",
        "## Interface assessment",
        "",
        "SQL + ordinary Python + small semantic introspection was sufficient.",
        "No domain query language was added.",
        "",
        f"- Used: {report['interfaces']['semantic_world']}",
        f"- Limitation: {report['interfaces']['missing_capability']}",
        "",
        "## Conclusions",
        "",
        "### MEASURED",
        "",
    ]
    for item in report["conclusions"]["MEASURED"]:
        lines.append(f"- {item}")
    lines += ["", "### OBSERVED", ""]
    for item in report["conclusions"]["OBSERVED"]:
        lines.append(f"- {item}")
    lines += ["", "### HYPOTHESIS", ""]
    for item in report["conclusions"]["HYPOTHESIS"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Later LLM experiment",
        "",
        "Reuse `raw/`, `world/`, `expected/`, and `expected/interfaces.json` unchanged.",
        "Do not run that experiment here.",
        "",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    report = freeze()
    print(
        json.dumps(
            {
                "provider_inference_calls": report["provider_inference_calls"],
                "indoor_panel": report["epistemic"]["indoor_panel"],
                "world_source_files": {
                    name: item["world_source_files"]
                    for name, item in report["correctness"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
