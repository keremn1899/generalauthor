from __future__ import annotations

import sqlite3

import pytest

from ontology_author.world.core.model import (
    Completeness,
    CompletenessStatus,
    DerivationError,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
    WorldStoreError,
)
from ontology_author.world.core.store import WorldStore


@pytest.fixture()
def view(tmp_path):
    world_store = WorldStore(
        tmp_path / "world.sqlite",
        world_id="test-view",
        purpose_ref="task:test@1",
    )
    yield world_store
    world_store.close()


def test_referent_identity_is_stable_and_can_retain_grounding(view):
    first_revision = view.revision
    assert view.add_referent(
        "service:orders",
        label="orders-service",
        grounding=[
            Grounding(GroundingKind.SOURCE, "repo://services/orders/service.yaml")
        ],
    ) == "service:orders"
    created_revision = view.revision
    assert created_revision == first_revision + 1

    view.add_referent(
        "service:orders",
        label="orders-service",
        grounding=[
            Grounding(GroundingKind.SOURCE, "repo://services/orders/service.yaml")
        ],
    )
    assert view.revision == created_revision
    assert view.groundings("REFERENT", "service:orders") == [
        {
            "kind": "SOURCE",
            "reference": "repo://services/orders/service.yaml",
            "detail": "",
        }
    ]


def test_named_relations_create_real_typed_unary_binary_and_nary_tables(view):
    for referent in ("service:a", "library:v2", "library:v3", "adapter:x"):
        view.add_referent(referent)

    view.declare_relation("production_service", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "depends_on",
        [Role("component", RoleType.REFERENT), Role("dependency", RoleType.REFERENT)],
    )
    view.add_referent("component:a")
    view.declare_relation(
        "compatible_via",
        [
            Role("service", RoleType.REFERENT),
            Role("old_library", RoleType.REFERENT),
            Role("new_library", RoleType.REFERENT),
            Role("adapter", RoleType.REFERENT),
        ],
    )
    view.declare_relation(
        "typed_values",
        [
            Role("name", RoleType.TEXT),
            Role("count", RoleType.INTEGER),
            Role("ratio", RoleType.REAL),
            Role("enabled", RoleType.BOOLEAN),
        ],
    )

    columns = {
        row["name"]: row["type"]
        for row in view.query("PRAGMA table_info(compatible_via)")
    }
    assert columns == {
        "_assertion_id": "TEXT",
        "service_id": "TEXT",
        "old_library_id": "TEXT",
        "new_library_id": "TEXT",
        "adapter_id": "TEXT",
    }

    view.assert_tuple(
        "typed_values",
        {"name": "sample", "count": 3, "ratio": 0.5, "enabled": True},
    )
    assert view.query("SELECT name, count, ratio, enabled FROM typed_values") == [
        {"name": "sample", "count": 3, "ratio": 0.5, "enabled": 1}
    ]


def test_semantic_tuple_is_unique_while_multiple_grounds_are_retained(view):
    view.add_referent("service:a")
    view.add_referent("adapter:x")
    view.declare_relation(
        "protected_by",
        [Role("service", RoleType.REFERENT), Role("adapter", RoleType.REFERENT)],
    )
    first = view.assert_tuple(
        "protected_by",
        {"service": "service:a", "adapter": "adapter:x"},
        grounding=[Grounding(GroundingKind.SOURCE, "repo://adapter.py")],
    )
    second = view.assert_tuple(
        "protected_by",
        {"service": "service:a", "adapter": "adapter:x"},
        grounding=[Grounding(GroundingKind.SOURCE, "test://adapter-contract")],
    )

    assert first.assertion_id == second.assertion_id
    assert first.inserted is True
    assert second.inserted is False
    assert view.query("SELECT service_id, adapter_id FROM protected_by") == [
        {"service_id": "service:a", "adapter_id": "adapter:x"}
    ]
    assert view.groundings("ASSERTION", first.assertion_id) == [
        {"kind": "SOURCE", "reference": "repo://adapter.py", "detail": ""},
        {"kind": "SOURCE", "reference": "test://adapter-contract", "detail": ""},
    ]


def test_rows_in_semantic_tables_are_active_assertions(view):
    view.add_referent("service:a")
    view.declare_relation("unresolved_scope", [Role("subject", RoleType.REFERENT)])
    assertion = view.assert_tuple("unresolved_scope", {"subject": "service:a"})
    metadata = view.query(
        "SELECT origin FROM _world_assertions WHERE assertion_id = ?",
        (assertion.assertion_id,),
    )
    assert metadata == [{"origin": "ASSERTED"}]
    assert view.query("SELECT subject_id FROM unresolved_scope") == [
        {"subject_id": "service:a"}
    ]


def test_base_and_derived_mutation_rules_and_sql_materialization(view):
    for referent in ("service:a", "service:b"):
        view.add_referent(referent)
    view.declare_relation("candidate", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "selected",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    assertion = view.assert_tuple("candidate", {"service": "service:a"})
    with pytest.raises(WorldStoreError, match="cannot be manually edited"):
        view.assert_tuple("selected", {"service": "service:a"})

    view.register_derivation(
        "selected",
        sql="SELECT service_id FROM candidate",
        inputs=["candidate"],
    )
    result = view.run_derivation(
        "selected",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="candidate",
            basis="All candidates were selected.",
        ),
    )
    assert result.row_count == 1
    assert view.query("SELECT service_id FROM selected") == [
        {"service_id": "service:a"}
    ]
    origin = view.query(
        "SELECT origin FROM _world_assertions WHERE relation_name = 'selected'"
    )
    assert origin == [{"origin": "DERIVED"}]
    with pytest.raises(WorldStoreError, match="cannot be manually edited"):
        view.retract("selected", assertion.assertion_id)


def test_derived_reuse_records_inputs_and_propagates_staleness(view):
    for referent in ("service:a", "service:b"):
        view.add_referent(referent)
    view.declare_relation("seed", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "intermediate",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    view.declare_relation(
        "downstream",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    seed = view.assert_tuple("seed", {"service": "service:a"})
    view.register_derivation(
        "intermediate", sql="SELECT service_id FROM seed", inputs=["seed"]
    )
    view.register_derivation(
        "downstream",
        sql="SELECT service_id FROM intermediate",
        inputs=["intermediate"],
    )
    complete_seed = Completeness(CompletenessStatus.COMPLETE, universe="seed")
    view.run_derivation("intermediate", completeness=complete_seed)
    view.run_derivation(
        "downstream",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="intermediate"
        ),
    )
    assert view.stale_relations() == []

    view.retract("seed", seed.assertion_id)
    assert view.stale_relations() == ["downstream", "intermediate"]
    with pytest.raises(DerivationError, match="derived input 'intermediate' is stale"):
        view.run_derivation(
            "downstream",
            completeness=Completeness(
                CompletenessStatus.COMPLETE, universe="intermediate"
            ),
        )
    view.run_derivation("intermediate", completeness=complete_seed)
    assert view.stale_relations() == ["downstream"]
    view.run_derivation(
        "downstream",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="intermediate"
        ),
    )
    assert view.stale_relations() == []


@pytest.mark.parametrize(
    "status", [
        CompletenessStatus.COMPLETE,
        CompletenessStatus.INCOMPLETE,
        CompletenessStatus.UNKNOWN,
    ]
)
def test_all_three_completeness_states_are_recorded(view, status):
    view.add_referent("service:a")
    view.declare_relation("universe", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "empty_result",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    view.assert_tuple("universe", {"service": "service:a"})
    view.register_derivation(
        "empty_result",
        sql="SELECT service_id FROM universe WHERE 0",
        inputs=["universe"],
    )
    gaps = () if status == CompletenessStatus.COMPLETE else ("inventory gap",)
    view.run_derivation(
        "empty_result",
        completeness=Completeness(
            status,
            universe="universe",
            basis="Explicit fixture declaration.",
            known_gaps=gaps,
        ),
    )
    receipt = view.latest_completeness("empty_result")
    assert receipt["status"] == status.value
    assert view.absence_is_exhaustive("empty_result") is (
        status == CompletenessStatus.COMPLETE
    )


def test_read_only_agent_sql_refuses_mutation(view):
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        view.query("CREATE TABLE intrusion(id TEXT)")


def test_complete_empty_is_not_exhaustive_over_unknown_derived_universe(view):
    view.add_referent("service:a")
    view.declare_relation("seed", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "uncertain_universe",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    view.declare_relation(
        "empty_result",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    view.assert_tuple("seed", {"service": "service:a"})
    view.register_derivation(
        "uncertain_universe",
        sql="SELECT service_id FROM seed WHERE 0",
        inputs=["seed"],
    )
    view.register_derivation(
        "empty_result",
        sql="SELECT service_id FROM uncertain_universe WHERE 0",
        inputs=["uncertain_universe"],
    )
    view.run_derivation(
        "uncertain_universe",
        completeness=Completeness(
            CompletenessStatus.UNKNOWN,
            universe="seed",
            known_gaps=("dynamic service inventory",),
        ),
    )
    view.run_derivation(
        "empty_result",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="uncertain_universe",
            basis="Every currently represented universe member was checked.",
        ),
    )
    assert view.query("SELECT service_id FROM empty_result") == []
    assert view.completeness_state("empty_result") == "UNIVERSE_NOT_COMPLETE"
    assert view.absence_is_exhaustive("empty_result") is False


def test_discovery_is_compact_and_reports_schema_mode_staleness_and_completeness(view):
    view.add_referent("service:a")
    view.declare_relation(
        "production_service",
        [Role("service", RoleType.REFERENT)],
        description="Production universe.",
    )
    view.declare_relation(
        "affected_service",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
        description="Affected production services.",
    )
    view.assert_tuple("production_service", {"service": "service:a"})
    view.register_derivation(
        "affected_service",
        sql="SELECT service_id FROM production_service",
        inputs=["production_service"],
    )
    view.run_derivation(
        "affected_service",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="production_service"
        ),
    )
    text = view.describe_text()
    assert "production_service(service REFERENT) BASE" in text
    assert "affected_service(service REFERENT) DERIVED" in text
    assert "completeness: COMPLETE over production_service" in text


def test_derivation_cannot_hide_an_undeclared_sql_input(view):
    view.add_referent("service:a")
    view.declare_relation("first_input", [Role("service", RoleType.REFERENT)])
    view.declare_relation("hidden_input", [Role("service", RoleType.REFERENT)])
    view.declare_relation(
        "result",
        [Role("service", RoleType.REFERENT)],
        mode=RelationMode.DERIVED,
    )
    view.assert_tuple("first_input", {"service": "service:a"})
    view.assert_tuple("hidden_input", {"service": "service:a"})
    view.register_derivation(
        "result",
        sql="""
            SELECT f.service_id
            FROM first_input AS f
            JOIN hidden_input AS h ON h.service_id = f.service_id
        """,
        inputs=["first_input"],
    )
    with pytest.raises(DerivationError, match="undeclared input relations.*hidden_input"):
        view.run_derivation(
            "result",
            completeness=Completeness(
                CompletenessStatus.COMPLETE, universe="first_input"
            ),
        )
