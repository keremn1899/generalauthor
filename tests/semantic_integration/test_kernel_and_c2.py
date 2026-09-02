from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation
from research.semantic_integration.domains.bom.c2.campaign import run_campaign
from research.semantic_integration.domains.bom.vocabulary import declare_bom_schema
from research.semantic_integration.domains.taskview_migration.vocabulary import (
    declare_migration_schema,
)
from research.semantic_integration.harness import coverage, load_oracle_document
from research.taskview_bom.experiment import ORACLE_PATH, compile_c1
from research.taskview_bom_scaling import SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED
from research.taskview_bom_scaling.c2.protocol import LiveInferenceBlocked, run_c2

PACKET_DIR = Path("research/taskview_bom_scaling/c2/packets")


def test_scaling_preflight_flag_remains_closed():
    assert SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED is False
    packet = json.loads((PACKET_DIR / "packet-001.json").read_text(encoding="utf-8"))
    with pytest.raises(LiveInferenceBlocked):
        run_c2(lambda _request: {}, packet)


def test_bom_and_migration_vocabularies_share_kernel_without_engine_branch(tmp_path):
    world = SemanticWorld(tmp_path / "shared.sqlite", world_id="vocab-share")
    try:
        declare_bom_schema(world)
        declare_migration_schema(world)
        names = {item["name"] for item in world.taskview.describe()["relations"]}
        assert {"eligible_part", "requires_change", "acceptable_replacement"} <= names
    finally:
        world.close()


def test_origin_account_tracks_mechanical_semantic_derived(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    world = SemanticWorld.wrap(compilation.view, world_id="origins")
    try:
        for row in world.query("SELECT assertion_id, origin FROM _tv_assertions"):
            world._origins[row["assertion_id"]] = (
                ConstructionOrigin.DERIVED.value
                if row["origin"] == "DERIVED"
                else ConstructionOrigin.MECHANICAL.value
            )
        oracle = load_oracle_document(json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        before = coverage(
            oracle, {name: world.relation_tuples(name) for name in oracle.tuples}
        )
        assert before["c1_established"] == 178
        assert before["semantic_established"] == 0
        assert before["frontier_tuple_count"] == 2
        observation = SourceObservation(
            provider="fixture",
            native_handle="engineering_notes.md",
            source_revision="sha256:bb9e10c4c220701d7c5ff755c18a7d39e78371d014680b99576626f3e4652c16",
            native_location="lines 15-21 (ER-2)",
        )
        world.assert_tuple(
            "acceptable_replacement",
            {
                "new_part": "part:R210",
                "old_part": "part:R200",
                "context": "context:high_vibration_cabinet",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(observation,),
                construction_method="test",
            ),
        )
        account = world.origin_account()
        assert account["SEMANTIC"] == 1
        assert account["MECHANICAL"] == 131
        assert account["DERIVED"] == 47
    finally:
        world.close()


def test_scripted_c2_inserts_without_live_model(tmp_path):
    def provider(request):
        packet = request["packet"]
        note = next(
            item
            for item in packet["evidence"]
            if item["source"] == "engineering_notes.md"
        )
        return {
            "decision": "ACCEPT",
            "grounds": [
                {
                    "source": note["source"],
                    "record_or_span": note["native_location"],
                }
            ],
            "reason": "The supplied engineering note states a qualified acceptance.",
        }

    report = run_campaign(
        live=False,
        provider=provider,
        output_dir=tmp_path,
        db_path=tmp_path / "loop.sqlite",
    )
    assert report["provider_inference_calls"] == 2
    assert report["fully_grounded_success_count"] == 2
    assert report["downstream"]["construction_loop_closed"] is True
    assert report["after_coverage"]["semantic_established"] == 2
    assert report["after_coverage"]["frontier_tuple_count"] == 0
    assert report["after_coverage"]["c1_established"] == 178
    live = json.loads(
        Path(
            "research/semantic_integration/domains/bom/c2/results/c2_campaign_report.json"
        ).read_text(encoding="utf-8")
    )
    assert live["fully_grounded_success_count"] == 2
    assert live["provider_inference_calls"] == 2
    assert live["downstream"]["construction_loop_closed"] is True
