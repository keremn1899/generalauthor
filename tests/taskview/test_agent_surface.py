from __future__ import annotations

import json

import pytest

from research.taskview_orientation.telemetry import visible_bytes
from taskview import TaskViewAgentSurface, TaskViewError
from taskview.migration_example import agent_surface_exercise, build_migration_view


@pytest.fixture()
def migration(tmp_path):
    view = build_migration_view(tmp_path / "migration.sqlite")
    yield view, TaskViewAgentSurface(view)
    view.close()


def _completeness(description, target):
    return next(
        record
        for record in description["completeness"]
        if record["target"] == target
    )


def test_describe_is_compact_schema_faithful_and_contains_no_hidden_plane(migration):
    _view, surface = migration
    description = surface.describe()

    assert description["task_view"] == {
        "view_id": "jsonlib-v3-migration",
        "task_spec_ref": "task:migrate-jsonlib@7",
        "revision": description["task_view"]["revision"],
    }
    compatible = next(
        relation
        for relation in description["relations"]["BASE"]
        if relation["name"] == "compatible_via"
    )
    assert compatible["roles"] == ["service", "old_library", "new_library", "adapter"]
    affected = next(
        relation
        for relation in description["relations"]["DERIVED"]
        if relation["name"] == "affected_service"
    )
    assert "state" not in affected  # CURRENT is the compact-catalog default.
    assert description["surface_version"] == "0.1"
    wire = json.dumps(description, sort_keys=True)
    assert "_tv_" not in wire
    assert "SELECT " not in wire
    assert "world-index://" not in wire
    assert "_assertion_id" not in wire


def test_query_sql_supports_normal_sql_and_rejects_writes_and_system_tables(migration):
    _view, surface = migration
    result = surface.query_sql(
        """
        SELECT a.service_id
        FROM affected_service AS a
        LEFT JOIN protected_by AS p ON p.service_id = a.service_id
        WHERE p.service_id IS NULL
        ORDER BY a.service_id
        """
    )
    assert result == {
        "rows": [{"service_id": "service:checkout"}],
        "row_count": 1,
    }

    recursive = surface.query_sql(
        """
        WITH RECURSIVE numbers(n) AS (
            SELECT 1 UNION ALL SELECT n + 1 FROM numbers WHERE n < 3
        )
        SELECT n FROM numbers
        """
    )
    assert recursive["rows"] == [{"n": 1}, {"n": 2}, {"n": 3}]

    with pytest.raises(TaskViewError, match="query_sql rejected"):
        surface.query_sql("DELETE FROM affected_service")
    with pytest.raises(TaskViewError, match="query_sql rejected"):
        surface.query_sql("SELECT * FROM _tv_assertions")
    with pytest.raises(TaskViewError):
        surface.query_sql("SELECT _assertion_id FROM affected_service")


def test_assertion_operation_asserts_base_adds_grounding_and_rejects_derived(migration):
    view, surface = migration
    values = {
        "service": "service:reporting",
        "adapter": "adapter:reporting-json-v3",
    }
    result = surface.assertion(
        action="ASSERT",
        relation="protected_by",
        values=values,
        grounding=[
            {
                "kind": "SOURCE",
                "reference": "review://adapter-compatibility",
            }
        ],
    )
    assert result["inserted"] is False
    assert "assertion_id" not in result
    assert view.query("SELECT count(*) AS n FROM protected_by") == [{"n": 1}]
    assert {ground["reference"] for ground in result["grounding"]} == {
        "repo://reporting/json_adapter.py",
        "review://adapter-compatibility",
    }

    with pytest.raises(TaskViewError, match="cannot be manually edited"):
        surface.assertion(
            action="ASSERT",
            relation="affected_service",
            values={"service": "service:checkout"},
        )


def test_retract_uses_semantic_tuple_and_recursively_stales_dependents(migration):
    view, surface = migration
    result = surface.assertion(
        action="RETRACT",
        relation="in_scope",
        values={"subject": "service:checkout"},
    )
    assert result["removed"] is True
    assert "assertion_id" not in result
    assert result["stale_relations"] == [
        "affected_service",
        "boundary_affected_service",
        "requires_change",
        "verification_gap",
    ]
    assert view.query(
        "SELECT subject_id FROM in_scope ORDER BY subject_id"
    ) == [{"subject_id": "service:reporting"}]


def test_describe_distinguishes_complete_unknown_and_stale_empty_results(migration):
    view, surface = migration
    initial = surface.describe()
    assert _completeness(initial, "verification_gap") == {
        "target": "verification_gap",
        "universe": "affected_service",
        "status": "COMPLETE",
    }
    unknown = _completeness(initial, "boundary_affected_service")
    assert unknown["status"] == "UNKNOWN"
    assert view.absence_is_exhaustive("verification_gap") is True
    assert view.absence_is_exhaustive("boundary_affected_service") is False

    surface.assertion(
        action="RETRACT",
        relation="verified_by",
        values={
            "service": "service:checkout",
            "test": "test:checkout-contract",
        },
    )
    stale = _completeness(surface.describe(), "verification_gap")
    assert stale["status"] == "COMPLETE"
    assert stale["state"] == "STALE"
    assert view.query("SELECT service_id FROM verification_gap") == []
    assert view.absence_is_exhaustive("verification_gap") is False


def test_rerun_materializes_and_reports_exact_input_versions(migration):
    view, surface = migration
    surface.assertion(
        action="RETRACT",
        relation="verified_by",
        values={
            "service": "service:checkout",
            "test": "test:checkout-contract",
        },
    )
    relation_versions = {
        relation["name"]: relation["relation_version"]
        for relation in view.describe()["relations"]
    }
    result = surface.rerun(
        "verification_gap",
        universe="affected_service",
        status="COMPLETE",
        basis="All affected services checked after retraction.",
    )
    assert result["row_count"] == 1
    assert result["stale_relations"] == []
    assert result["completeness"]["input_versions"] == {
        "affected_service": relation_versions["affected_service"],
        "verified_by": relation_versions["verified_by"],
    }
    assert surface.query_sql("SELECT service_id FROM verification_gap")["rows"] == [
        {"service_id": "service:checkout"}
    ]


def test_describe_can_explain_one_tuple_without_polluting_normal_queries(migration):
    _view, surface = migration
    detail = surface.describe(
        why={
            "relation": "compatible_via",
            "tuple": {
                "service": "service:reporting",
                "old_library": "library:jsonlib-v2",
                "new_library": "library:jsonlib-v3",
                "adapter": "adapter:reporting-json-v3",
            },
        }
    )["why"]
    assert detail["origin"] == "ASSERTED"
    assert {ground["reference"] for ground in detail["grounding"]} == {
        "repo://reporting/json_adapter.py",
        "test://reporting-json-v3-contract",
    }


def test_v01_describe_catalog_is_compact_and_targeted_describe_is_scoped(migration):
    _view, surface = migration
    catalog = surface.describe()
    assert visible_bytes(catalog) < 1500
    catalog_wire = json.dumps(catalog, sort_keys=True)
    assert "grounding" not in catalog_wire
    assert "derivation" not in catalog_wire
    assert "description" not in catalog_wire
    assert "_tv_" not in catalog_wire

    detail = surface.describe(relation="protected_by")
    assert detail["relation"]["name"] == "protected_by"
    assert detail["relation"]["description"]
    assert detail["relation"]["roles"] == [
        {"name": "service", "type": "REFERENT", "column": "service_id"},
        {"name": "adapter", "type": "REFERENT", "column": "adapter_id"},
    ]
    assert "compatible_via" not in json.dumps(detail, sort_keys=True)


def test_query_sql_accepts_select_star_but_keeps_hidden_ids_private(migration):
    _view, surface = migration
    result = surface.query_sql("SELECT * FROM protected_by")
    assert result == {
        "rows": [
            {
                "service_id": "service:reporting",
                "adapter_id": "adapter:reporting-json-v3",
            }
        ],
        "row_count": 1,
    }
    with pytest.raises(TaskViewError, match="hidden assertion IDs"):
        surface.query_sql("SELECT _assertion_id FROM protected_by")
    with pytest.raises(TaskViewError, match="hidden assertion IDs"):
        surface.query_sql('SELECT "_assertion_id" FROM protected_by')


def test_assertion_accepts_role_names_and_physical_id_aliases(migration):
    view, surface = migration
    result = surface.assertion(
        action="RETRACT",
        relation="verified_by",
        values={
            "service_id": "service:checkout",
            "test_id": "test:checkout-contract",
        },
    )
    assert result["removed"] is True
    assert result["tuple"] == {
        "service": "service:checkout",
        "test": "test:checkout-contract",
    }
    assert view.query("SELECT count(*) AS n FROM verified_by") == [{"n": 1}]


def test_full_four_operation_sequence_restores_exhaustive_empty_result(migration):
    view, _surface = migration
    exercise = agent_surface_exercise(view)
    assert exercise["initial"]["verification_gap"] == {"rows": [], "row_count": 0}
    assert exercise["initial"]["requires_change"] == {
        "rows": [{"service_id": "service:checkout"}],
        "row_count": 1,
    }
    assert exercise["initial"]["exhaustive"] is True
    assert exercise["retract"]["stale_relations"] == ["verification_gap"]
    assert exercise["stale"]["exhaustive"] is False
    assert exercise["gap_after_retract"] == {
        "rows": [{"service_id": "service:checkout"}],
        "row_count": 1,
    }
    assert exercise["assert"]["inserted"] is True
    assert exercise["assert"]["stale_relations"] == ["verification_gap"]
    assert exercise["restored"]["verification_gap"] == {
        "rows": [],
        "row_count": 0,
    }
    assert exercise["restored"]["exhaustive"] is True


def test_surface_does_not_expose_relation_or_referent_creation(migration):
    _view, surface = migration
    assert not hasattr(surface, "declare_relation")
    assert not hasattr(surface, "add_referent")
