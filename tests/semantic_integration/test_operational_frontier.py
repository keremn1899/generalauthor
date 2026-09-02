from __future__ import annotations

import ast
import inspect
import json
from collections import defaultdict
from pathlib import Path

from research.semantic_integration.domains.bom.compiler import compile_c1
from research.semantic_integration.domains.bom.operational_frontier.evaluate import (
    FROZEN_PATH,
    compare,
    evaluate,
    obligation_tuples,
    oracle_residual,
)
from research.semantic_integration.domains.bom.operational_frontier.generate import (
    PURPOSE,
    demanded_cases,
    fingerprint,
    freeze_operational_frontier,
    generate_obligations,
    operational_frontier_document,
)
from taskview import Grounding, GroundingKind

GENERATE_PATH = Path(
    "research/semantic_integration/domains/bom/operational_frontier/generate.py"
)
SEALED_ARTIFACTS = [
    Path("research/taskview_bom/oracle.json"),
    Path("research/taskview_bom/report.json"),
    Path("research/taskview_bom/frontier_packets.json"),
    Path(
        "research/semantic_integration/domains/bom/c2/results/c2_campaign_report.json"
    ),
    Path("research/semantic_integration/domains/bom/c2/authorized.json"),
]
FORBIDDEN_GENERATE_TOKENS = (
    "FrozenOracle",
    "oracle.json",
    "load_oracle",
    "unresolved",
    "frontier_packets",
    "packet-001",
    "packet-002",
    "part:X110",
    "part:X160",
    "part:R210",
    "part:R200",
    "outdoor_enclosure",
    "high_vibration_cabinet",
    "adjudication_oracle",
    "C2",
)


def _world(name: str) -> list[Grounding]:
    return [
        Grounding(
            GroundingKind.WORLD,
            name,
            "operational-frontier-counterfactual",
        )
    ]


def _keys(obligations: list[dict]) -> set[tuple[str, str, str]]:
    return {
        (
            item["values"]["new_part"],
            item["values"]["old_part"],
            item["values"]["context"],
        )
        for item in obligations
    }


def test_generate_module_has_no_oracle_imports_or_identities():
    source = GENERATE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= {"__future__", "hashlib", "json", "pathlib", "typing", "taskview"}
    for token in FORBIDDEN_GENERATE_TOKENS:
        assert token not in source, token
    signature = inspect.signature(generate_obligations)
    assert list(signature.parameters) == ["view", "purpose"]


def test_operational_frontier_from_c1_and_purpose_only(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    try:
        document = operational_frontier_document(compilation.view)
        obligations = generate_obligations(compilation.view, purpose=PURPOSE)
        assert document["provider_inference_calls"] == 0
        assert document["inputs"] == ["compiled_c1_taskview", "purpose_contract"]
        assert document["purpose"]["id"] == "viable_replacement"
        assert document["candidate_replacement_pairs"] == 2
        assert document["candidate_case_count"] == len(demanded_cases(compilation.view))
        assert document["obligation_count"] == len(obligations) == 3
        assert compilation.view.query("SELECT * FROM acceptable_replacement") == []
        for item in obligations:
            assert item["relation"] == "acceptable_replacement"
            assert item["demanded_by"] == {
                "kind": "purpose",
                "name": "viable_replacement",
                "revision": 1,
            }
            assert set(item["values"]) == {"new_part", "old_part", "context"}
    finally:
        compilation.view.close()


def test_already_resolved_obligation_disappears(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    try:
        before = generate_obligations(compilation.view)
        target = before[0]["values"]
        compilation.view.assert_tuple(
            "acceptable_replacement",
            {
                "new_part": target["new_part"],
                "old_part": target["old_part"],
                "context": target["context"],
            },
            grounding=_world("resolved-obligation"),
        )
        after = generate_obligations(compilation.view)
        assert len(after) == len(before) - 1
        assert (
            target["new_part"],
            target["old_part"],
            target["context"],
        ) not in _keys(after)
        assert _keys(after) == _keys(before) - {
            (target["new_part"], target["old_part"], target["context"])
        }
    finally:
        compilation.view.close()


def test_additional_mechanical_candidate_adds_one_obligation(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    try:
        before = generate_obligations(compilation.view)
        by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
        for case in demanded_cases(compilation.view):
            by_pair[(case["new_part"], case["old_part"])].add(case["context"])
        reverse = next(
            (new_part, old_part)
            for (new_part, old_part), contexts in by_pair.items()
            if len(contexts) == 1
        )
        compilation.view.assert_tuple(
            "candidate_replacement",
            {"new_part": reverse[1], "old_part": reverse[0]},
            grounding=_world("extra-candidate"),
        )
        after = generate_obligations(compilation.view)
        added = _keys(after) - _keys(before)
        assert len(after) == len(before) + 1
        assert len(added) == 1
        extra = next(iter(added))
        assert extra[0] == reverse[1]
        assert extra[1] == reverse[0]
        for item in after:
            assert item["demanded_by"]["name"] == "viable_replacement"
    finally:
        compilation.view.close()


def test_irrelevant_world_growth_leaves_frontier_unchanged(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    try:
        before = operational_frontier_document(compilation.view)
        grounds = _world("irrelevant-growth")
        compilation.view.add_referent("part:Z900", label="thermal fuse", grounding=grounds)
        compilation.view.add_referent("bom:BOM-Z", label="BOM-Z", grounding=grounds)
        compilation.view.add_referent(
            "context:lab_bench", label="lab bench", grounding=grounds
        )
        compilation.view.add_referent(
            "listing:ZZ-Z900", label="ZZ-Z900", grounding=grounds
        )
        compilation.view.add_referent(
            "supplier:counterfactual", label="counterfactual", grounding=grounds
        )
        compilation.view.assert_tuple(
            "manufacturer_part", {"part": "part:Z900"}, grounding=grounds
        )
        compilation.view.assert_tuple(
            "part_type",
            {"part": "part:Z900", "part_type": "thermal_fuse"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "rated_voltage",
            {"part": "part:Z900", "volts": 24},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "temperature_range",
            {"part": "part:Z900", "minimum_c": -10, "maximum_c": 85},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "lifecycle",
            {"part": "part:Z900", "state": "active"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "bom_item", {"bom_item": "bom:BOM-Z"}, grounding=grounds
        )
        compilation.view.assert_tuple(
            "requires_type",
            {"bom_item": "bom:BOM-Z", "part_type": "thermal_fuse"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "requires_voltage",
            {"bom_item": "bom:BOM-Z", "volts": 24},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "requires_temperature",
            {"bom_item": "bom:BOM-Z", "minimum_c": 0, "maximum_c": 40},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "deployment_environment",
            {"bom_item": "bom:BOM-Z", "environment": "context:lab_bench"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "supplier_listing", {"listing": "listing:ZZ-Z900"}, grounding=grounds
        )
        compilation.view.assert_tuple(
            "offered_by",
            {"listing": "listing:ZZ-Z900", "supplier": "supplier:counterfactual"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "listing_availability",
            {"listing": "listing:ZZ-Z900", "state": "stock"},
            grounding=grounds,
        )
        compilation.view.assert_tuple(
            "listing_of",
            {"listing": "listing:ZZ-Z900", "part": "part:Z900"},
            grounding=grounds,
        )
        after = operational_frontier_document(compilation.view)
        assert after["obligation_count"] == before["obligation_count"]
        assert _keys(after["obligations"]) == _keys(before["obligations"])
        assert after["candidate_case_count"] == before["candidate_case_count"]
        assert after["candidate_replacement_pairs"] == before["candidate_replacement_pairs"]
    finally:
        compilation.view.close()


def test_frozen_artifact_matches_fresh_generation_then_scores_c0(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    try:
        frozen_path = tmp_path / "operational_frontier.json"
        document = freeze_operational_frontier(compilation.view, frozen_path)
        sidecar = json.loads(frozen_path.read_text(encoding="utf-8"))
        assert sidecar["fingerprint"] == fingerprint(document)
        assert (tmp_path / "operational_frontier.json.sha256").read_text(
            encoding="utf-8"
        ).strip() == document["fingerprint"]
        residual = oracle_residual(compilation.view)
        expected = residual["acceptable_replacement"]
        comparison = compare(obligation_tuples(document), expected)
        assert comparison["true_positive_count"] == 2
        assert comparison["false_positive_count"] == 1
        assert comparison["false_negative_count"] == 0
        assert comparison["precision"] == 2 / 3
        assert comparison["recall"] == 1.0
        assert comparison["exact_frontier_match"] is False
        assert comparison["false_positives"] == [
            ["part:X110", "part:X160", "context:indoor_panel"]
        ]
    finally:
        compilation.view.close()

    sealed_before = {
        path: path.read_bytes() for path in SEALED_ARTIFACTS if path.exists()
    }
    package_eval = evaluate(FROZEN_PATH)
    assert package_eval["provider_inference_calls"] == 0
    assert package_eval["comparison"]["exact_frontier_match"] is False
    assert package_eval["comparison"]["true_positive_count"] == 2
    assert package_eval["comparison"]["false_positive_count"] == 1
    assert package_eval["comparison"]["false_negative_count"] == 0
    for path, payload in sealed_before.items():
        assert path.read_bytes() == payload


def test_evaluate_loads_c0_only_after_frozen_file_exists():
    assert FROZEN_PATH.exists()
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    assert frozen["obligation_count"] == 3
    assert frozen["provider_inference_calls"] == 0
    assert frozen["fingerprint"].startswith("sha256:")
    assert fingerprint(frozen) == frozen["fingerprint"]
