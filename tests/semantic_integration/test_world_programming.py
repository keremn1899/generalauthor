from __future__ import annotations

import ast
from pathlib import Path

from research.semantic_integration.domains.bom.world_programming.access import (
    trace_source_access,
)
from research.semantic_integration.domains.bom.world_programming.canonical import dump
from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
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

EXPECTED = Path(
    "research/semantic_integration/domains/bom/world_programming/expected"
)
WORLD_DIR = Path(
    "research/semantic_integration/domains/bom/world_programming/world"
)
SEALED = [
    Path("research/taskview_bom/oracle.json"),
    Path("research/taskview_bom/report.json"),
    Path("research/taskview_bom/frontier_packets.json"),
    Path(
        "research/semantic_integration/domains/bom/c2/results/c2_campaign_report.json"
    ),
    Path(
        "research/semantic_integration/domains/bom/operational_frontier/operational_frontier.json"
    ),
]


def test_raw_and_world_match_frozen_expected_and_world_opens_no_sources(tmp_path):
    sealed_before = {path: path.read_bytes() for path in SEALED if path.exists()}
    experimental = construct_experimental_world(tmp_path / "world.sqlite")
    try:
        with trace_source_access() as raw_log:
            raw_outputs = {
                "analysis_a": raw_a.run(FIXTURES),
                "analysis_b": raw_b.run(FIXTURES),
                "analysis_c": raw_c.run(FIXTURES),
            }
        with trace_source_access() as world_log:
            world_outputs = {
                "analysis_a": world_a.run(
                    experimental.world, experimental.obligations
                ),
                "analysis_b": world_b.run(
                    experimental.world, experimental.obligations
                ),
                "analysis_c": world_c.run(
                    experimental.world, experimental.obligations
                ),
            }
        for name in raw_outputs:
            assert raw_outputs[name] == world_outputs[name]
            assert dump(raw_outputs[name]) == (EXPECTED / f"{name}.json").read_text(
                encoding="utf-8"
            )
        assert world_log.file_count == 0
        assert world_log.bytes_consumed == 0
        assert raw_log.file_count > 0
        indoor = next(
            case
            for case in world_outputs["analysis_a"]["cases"]
            if case["context"] == "context:indoor_panel"
        )
        assert indoor["semantic_state"] == "unresolved"
        assert indoor["epistemic"] == "UNRESOLVED"
        assert indoor["mechanical_state"] == "suitable"
        assert indoor["semantic_state"] != "accepted"
        assert all(
            case["epistemic"] != "ADJUDICATED_FALSE"
            for case in world_outputs["analysis_a"]["cases"]
        )
        accepted = next(
            case
            for case in world_outputs["analysis_a"]["cases"]
            if case["semantic_state"] == "accepted"
        )
        inspected = explain_tuple(
            experimental.world,
            "acceptable_replacement",
            {
                "new_part": accepted["new_part"],
                "old_part": accepted["old_part"],
                "context": accepted["context"],
            },
        )
        assert inspected is not None
        assert inspected["construction_origin"] == "SEMANTIC"
        assert any(ground["kind"] == "SOURCE" for ground in inspected["grounding"])
        bottleneck = next(
            case
            for case in world_outputs["analysis_b"]["cases"]
            if case["context"] == "context:indoor_panel"
        )
        assert "semantic_acceptance" in bottleneck["leaves_viability_uncertain"]
        assert "semantic_acceptance" not in bottleneck["prevents_viability"]
    finally:
        experimental.world.close()
    for path, payload in sealed_before.items():
        assert path.read_bytes() == payload


def test_world_analysis_modules_do_not_read_fixture_paths():
    for path in WORLD_DIR.glob("analysis_*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "research.taskview_bom.experiment" not in imported
        assert "FIXTURES" not in source
        assert "manufacturer.csv" not in source
        assert "suppliers.json" not in source
        assert "engineering_notes.md" not in source
        assert "bom.csv" not in source
        assert "oracle.json" not in source
        assert "FrozenOracle" not in source
