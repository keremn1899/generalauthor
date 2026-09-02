from __future__ import annotations

from dataclasses import fields

import pytest

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin, OriginMetadataError
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation
from research.semantic_integration.domains.bom.vocabulary import declare_bom_schema
from research.taskview_bom.experiment import compile_c1


def test_assert_tuple_origin_is_the_only_construction_origin_authority(tmp_path):
    assert "construction_origin" not in {item.name for item in fields(AssertionGrounding)}

    world = SemanticWorld(tmp_path / "origin.sqlite", world_id="origin-authority")
    try:
        declare_bom_schema(world)
        world.add_referent("part:R210")
        world.add_referent("part:R200")
        world.add_referent("context:high_vibration_cabinet")
        observation = SourceObservation(
            provider="fixture",
            native_handle="engineering_notes.md",
            source_revision="sha256:" + ("a" * 64),
            native_location="lines 15-21 (ER-2)",
        )
        result = world.assert_tuple(
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
        assert world.origin_for_assertion(result.assertion_id) == "SEMANTIC"
        inspected = world.inspect_tuple(
            "acceptable_replacement",
            {
                "new_part": "part:R210",
                "old_part": "part:R200",
                "context": "context:high_vibration_cabinet",
            },
        )
        assert inspected is not None
        assert inspected["construction_origin"] == "SEMANTIC"
        assert world.origin_account()["SEMANTIC"] == 1
    finally:
        world.close()


def test_missing_asserted_origin_does_not_default_to_mechanical(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    world = SemanticWorld.wrap(compilation.view, world_id="missing-origin")
    try:
        asserted = world.query(
            "SELECT assertion_id FROM _tv_assertions WHERE origin = 'ASSERTED' LIMIT 1"
        )
        assert asserted
        with pytest.raises(OriginMetadataError, match="has no construction origin"):
            world.origin_for_assertion(asserted[0]["assertion_id"])
        with pytest.raises(OriginMetadataError, match="has no construction origin"):
            world.origin_account()

        derived = world.query(
            "SELECT assertion_id FROM _tv_assertions WHERE origin = 'DERIVED' LIMIT 1"
        )
        assert derived
        assert world.origin_for_assertion(derived[0]["assertion_id"]) == "DERIVED"
    finally:
        world.close()
