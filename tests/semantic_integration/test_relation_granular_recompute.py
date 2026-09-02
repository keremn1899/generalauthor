from __future__ import annotations

from research.semantic_integration.benchmarks.relation_granular_invalidation.measure import (
    LIMITATION_ID,
    measure,
)


def test_relation_granular_recompute_is_frozen_not_fixed():
    report = measure()
    assert report["limitation_id"] == LIMITATION_ID
    assert report["fix_implemented"] is False
    by_scale = {row["scale"]: row for row in report["scales"]}
    assert by_scale["S1"]["number_of_tuples_recomputed"] == 29
    assert by_scale["S10"]["number_of_tuples_recomputed"] == 330
    assert by_scale["S100"]["number_of_tuples_recomputed"] == 3120
    for row in report["scales"]:
        assert row["changed_source_observations"] == 1
        assert row["changed_base_tuples"] == 2
        assert row["stale_derived_relations"] == [
            "eligible_part",
            "temperature_compatible",
        ]
        assert row["unaffected_derived_relations"] == [
            "spec_conflict",
            "voltage_compatible",
        ]
        assert row["rerun_result_correctness"] is True
