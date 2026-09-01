from __future__ import annotations

from taskview.migration_example import (
    agent_sql_exercise,
    build_migration_view,
    mutate_verification_and_rerun,
)


def test_worked_migration_exercises_scope_nary_reuse_and_exhaustive_empty(tmp_path):
    view = build_migration_view(tmp_path / "migration.sqlite")
    try:
        relation_names = {row["name"] for row in view.describe()["relations"]}
        assert {
            "in_scope",
            "boundary",
            "excluded",
            "unresolved_scope",
            "compatible_via",
            "legacy_component",
            "affected_service",
            "verification_gap",
        } <= relation_names

        compatibility = view.query(
            """
            SELECT service_id, old_library_id, new_library_id, adapter_id
            FROM compatible_via
            """
        )
        assert compatibility == [
            {
                "service_id": "service:reporting",
                "old_library_id": "library:jsonlib-v2",
                "new_library_id": "library:jsonlib-v3",
                "adapter_id": "adapter:reporting-json-v3",
            }
        ]

        answers = agent_sql_exercise(view)
        assert answers["affected"] == [
            {"service_id": "service:checkout"},
            {"service_id": "service:reporting"},
        ]
        assert answers["protected"] == [
            {
                "service_id": "service:reporting",
                "adapter_id": "adapter:reporting-json-v3",
            }
        ]
        assert answers["verification_gaps"] == []
        assert answers["verification_gap_empty_is_exhaustive"] is True
        assert answers["verification_gap_receipt"]["universe_relation"] == (
            "affected_service"
        )
        assert answers["exclusions"] == [
            {
                "subject_id": "service:partner-gateway",
                "basis": "vendor-owned boundary remains on the supported v2 protocol",
            }
        ]
        assert view.latest_completeness("boundary_affected_service")["status"] == (
            "UNKNOWN"
        )
        assert view.absence_is_exhaustive("boundary_affected_service") is False
        assert view.query("SELECT subject_id FROM boundary") == [
            {"subject_id": "service:partner-gateway"}
        ]
        assert view.query("SELECT subject_id FROM unresolved_scope") == [
            {"subject_id": "service:external-worker"}
        ]
    finally:
        view.close()


def test_worked_migration_marks_downstream_stale_and_rerun_restores_current_state(
    tmp_path,
):
    view = build_migration_view(tmp_path / "migration.sqlite")
    try:
        result = mutate_verification_and_rerun(view)
        assert result["stale_before_rerun"] == ["verification_gap"]
        assert result["empty_is_exhaustive_before_rerun"] is False
        assert result["stale_after_rerun"] == []
        assert result["rows"] == [{"service_id": "service:checkout"}]
        assert result["result"].row_count == 1
        assert view.absence_is_exhaustive("verification_gap") is False
    finally:
        view.close()
