"""Worked dependency-migration TaskView used by tests and inspection.

The example is intentionally fixture-authored.  It exercises TaskView mechanics
without claiming to extract or infer these semantic assertions from sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskview import (
    Completeness,
    CompletenessStatus,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
    TaskView,
    TaskViewAgentSurface,
)


def _source(reference: str, detail: str = "") -> tuple[Grounding, ...]:
    return (Grounding(GroundingKind.SOURCE, reference, detail),)


def build_migration_view(path: Path | str) -> TaskView:
    """Build and materialize one compact library-migration TaskView."""

    view = TaskView(
        path,
        view_id="jsonlib-v3-migration",
        task_spec_ref="task:migrate-jsonlib@7",
    )

    referents = {
        "library:jsonlib-v2": "jsonlib v2",
        "library:jsonlib-v3": "jsonlib v3",
        "component:checkout-json": "Checkout JSON integration",
        "component:reporting-json": "Reporting JSON integration",
        "component:partner-json": "Partner JSON bridge",
        "service:checkout": "checkout-service",
        "service:reporting": "reporting-service",
        "service:partner-gateway": "partner-gateway",
        "service:external-worker": "external-worker",
        "adapter:reporting-json-v3": "Reporting v3 compatibility adapter",
        "test:checkout-contract": "Checkout JSON contract test",
        "test:reporting-contract": "Reporting JSON contract test",
    }
    for identity, label in referents.items():
        view.add_referent(
            identity,
            label=label,
            grounding=_source(f"world-index://migration/{identity}"),
        )

    ref = RoleType.REFERENT
    text = RoleType.TEXT
    base_relations = [
        (
            "component",
            [Role("component", ref)],
            "Components considered by the migration dependency inventory.",
        ),
        (
            "depends_on",
            [Role("component", ref), Role("dependency", ref)],
            "Direct build/runtime dependency asserted for a component.",
        ),
        (
            "implements",
            [Role("service", ref), Role("component", ref)],
            "Service-to-component realization relevant to this migration.",
        ),
        (
            "production_service",
            [Role("service", ref)],
            "Production service universe for affectedness.",
        ),
        (
            "protected_by",
            [Role("service", ref), Role("adapter", ref)],
            "Service whose migration behavior is protected by an adapter.",
        ),
        (
            "compatible_via",
            [
                Role("service", ref),
                Role("old_library", ref),
                Role("new_library", ref),
                Role("adapter", ref),
            ],
            "Accepted n-ary compatibility judgment.",
        ),
        (
            "verified_by",
            [Role("service", ref), Role("test", ref)],
            "Task-relevant verification relationship.",
        ),
        ("in_scope", [Role("subject", ref)], "Interior task scope."),
        ("boundary", [Role("subject", ref)], "Relevant opaque boundary."),
        (
            "excluded",
            [Role("subject", ref), Role("basis", text)],
            "Explicit grounded task exclusion.",
        ),
        (
            "unresolved_scope",
            [Role("subject", ref)],
            "Object whose scope mapping remains unresolved.",
        ),
    ]
    for name, roles, description in base_relations:
        view.declare_relation(name, roles, description=description)

    derived_relations = [
        (
            "legacy_component",
            "component",
            "Materialized component set that depends on jsonlib v2.",
        ),
        (
            "affected_service",
            "service",
            "Production services in scope whose components depend on jsonlib v2.",
        ),
        (
            "verification_gap",
            "service",
            "Affected services without declared task-relevant verification.",
        ),
        (
            "requires_change",
            "service",
            "Affected services requiring direct code change after protections and exclusions.",
        ),
        (
            "boundary_affected_service",
            "service",
            "Known affected services situated at the modeled task boundary.",
        ),
    ]
    for name, role_name, description in derived_relations:
        view.declare_relation(
            name,
            [Role(role_name, ref)],
            mode=RelationMode.DERIVED,
            description=description,
        )

    for component in (
        "component:checkout-json",
        "component:reporting-json",
        "component:partner-json",
    ):
        view.assert_tuple(
            "component",
            {"component": component},
            grounding=_source("repo://inventory/components.toml", component),
        )
        view.assert_tuple(
            "depends_on",
            {"component": component, "dependency": "library:jsonlib-v2"},
            grounding=_source(f"repo://lockfiles/{component.split(':', 1)[1]}.lock"),
        )

    implementations = {
        "service:checkout": "component:checkout-json",
        "service:reporting": "component:reporting-json",
        "service:partner-gateway": "component:partner-json",
    }
    for service, component in implementations.items():
        view.assert_tuple(
            "implements",
            {"service": service, "component": component},
            grounding=_source("world-index://deployable/service-components"),
        )
        view.assert_tuple(
            "production_service",
            {"service": service},
            grounding=_source("deploy://production/services@2026-08-30"),
        )

    for service in ("service:checkout", "service:reporting"):
        view.assert_tuple(
            "in_scope",
            {"subject": service},
            grounding=_source("task-scope://migrate-jsonlib@7"),
        )
    view.assert_tuple(
        "boundary",
        {"subject": "service:partner-gateway"},
        grounding=_source("architecture://boundaries/partner-gateway"),
    )
    view.assert_tuple(
        "excluded",
        {
            "subject": "service:partner-gateway",
            "basis": "vendor-owned boundary remains on the supported v2 protocol",
        },
        grounding=_source("task-scope://migrate-jsonlib@7#partner-exclusion"),
    )
    view.assert_tuple(
        "unresolved_scope",
        {"subject": "service:external-worker"},
        grounding=_source("runtime://dynamic-consumers", "inventory is incomplete"),
    )
    view.assert_tuple(
        "protected_by",
        {
            "service": "service:reporting",
            "adapter": "adapter:reporting-json-v3",
        },
        grounding=_source("repo://reporting/json_adapter.py"),
    )
    view.assert_tuple(
        "compatible_via",
        {
            "service": "service:reporting",
            "old_library": "library:jsonlib-v2",
            "new_library": "library:jsonlib-v3",
            "adapter": "adapter:reporting-json-v3",
        },
        grounding=(
            Grounding(GroundingKind.SOURCE, "repo://reporting/json_adapter.py"),
            Grounding(GroundingKind.SOURCE, "test://reporting-json-v3-contract"),
        ),
    )
    verification_assertions = {
        "service:checkout": "test:checkout-contract",
        "service:reporting": "test:reporting-contract",
    }
    for service, test in verification_assertions.items():
        view.assert_tuple(
            "verified_by",
            {"service": service, "test": test},
            grounding=_source(f"repo://tests/{test.split(':', 1)[1]}.yaml"),
        )

    view.register_derivation(
        "legacy_component",
        inputs=["component", "depends_on"],
        sql="""
            SELECT DISTINCT c.component_id
            FROM component AS c
            JOIN depends_on AS d ON d.component_id = c.component_id
            WHERE d.dependency_id = 'library:jsonlib-v2'
        """,
    )
    view.register_derivation(
        "affected_service",
        inputs=[
            "legacy_component",
            "implements",
            "production_service",
            "in_scope",
            "excluded",
        ],
        sql="""
            SELECT DISTINCT p.service_id
            FROM production_service AS p
            JOIN in_scope AS scope ON scope.subject_id = p.service_id
            JOIN implements AS i ON i.service_id = p.service_id
            JOIN legacy_component AS l ON l.component_id = i.component_id
            WHERE NOT EXISTS (
                SELECT 1 FROM excluded AS x WHERE x.subject_id = p.service_id
            )
        """,
    )
    view.register_derivation(
        "verification_gap",
        inputs=["affected_service", "verified_by"],
        sql="""
            SELECT a.service_id
            FROM affected_service AS a
            WHERE NOT EXISTS (
                SELECT 1 FROM verified_by AS v WHERE v.service_id = a.service_id
            )
        """,
    )
    view.register_derivation(
        "requires_change",
        inputs=["affected_service", "protected_by", "excluded"],
        sql="""
            SELECT a.service_id
            FROM affected_service AS a
            WHERE NOT EXISTS (
                SELECT 1 FROM protected_by AS p WHERE p.service_id = a.service_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM excluded AS x WHERE x.subject_id = a.service_id
            )
        """,
    )
    view.register_derivation(
        "boundary_affected_service",
        inputs=["affected_service", "boundary"],
        sql="""
            SELECT a.service_id
            FROM affected_service AS a
            JOIN boundary AS b ON b.subject_id = a.service_id
        """,
    )

    view.run_derivation(
        "legacy_component",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="component",
            basis="All components in the pinned build inventory were evaluated.",
        ),
    )
    view.run_derivation(
        "affected_service",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="production_service",
            basis="Pinned production universe, component map, scope, and exclusions evaluated.",
        ),
    )
    view.run_derivation(
        "verification_gap",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="affected_service",
            basis="Every currently affected service was checked against verified_by.",
        ),
    )
    view.run_derivation(
        "requires_change",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="affected_service",
            basis="All affected services were checked for protection and exclusion.",
        ),
    )
    view.run_derivation(
        "boundary_affected_service",
        completeness=Completeness(
            CompletenessStatus.UNKNOWN,
            universe="boundary",
            basis="The partner boundary is represented, but its internal consumers are opaque.",
            known_gaps=("partner-internal dependency inventory unavailable",),
        ),
    )
    return view


def agent_sql_exercise(view: TaskView) -> dict[str, Any]:
    """Representative ordinary SQL answers over the worked semantic plane."""

    affected = view.query(
        "SELECT service_id FROM affected_service ORDER BY service_id"
    )
    protected = view.query(
        """
        SELECT a.service_id, p.adapter_id
        FROM affected_service AS a
        JOIN protected_by AS p ON p.service_id = a.service_id
        ORDER BY a.service_id
        """
    )
    gaps = view.query(
        "SELECT service_id FROM verification_gap ORDER BY service_id"
    )
    exclusions = view.query(
        "SELECT subject_id, basis FROM excluded ORDER BY subject_id"
    )
    return {
        "affected": affected,
        "protected": protected,
        "verification_gaps": gaps,
        "exclusions": exclusions,
        "verification_gap_receipt": view.latest_completeness("verification_gap"),
        "verification_gap_empty_is_exhaustive": view.absence_is_exhaustive(
            "verification_gap"
        ),
        "stale_relations": view.stale_relations(),
    }


def mutate_verification_and_rerun(view: TaskView) -> dict[str, Any]:
    """Demonstrate input invalidation and an explicit restoring rerun."""

    view.retract_tuple(
        "verified_by",
        {"service": "service:checkout", "test": "test:checkout-contract"},
    )
    stale_before = view.stale_relations()
    exhaustive_before = view.absence_is_exhaustive("verification_gap")
    result = view.run_derivation(
        "verification_gap",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="affected_service",
            basis="Every currently affected service was checked after the assertion change.",
        ),
    )
    return {
        "stale_before_rerun": stale_before,
        "empty_is_exhaustive_before_rerun": exhaustive_before,
        "stale_after_rerun": view.stale_relations(),
        "result": result,
        "rows": view.query(
            "SELECT service_id FROM verification_gap ORDER BY service_id"
        ),
    }


def agent_surface_exercise(view: TaskView) -> dict[str, Any]:
    """Exercise the frozen four-operation surface from end to end."""

    surface = TaskViewAgentSurface(view)
    initial = {
        "describe": surface.describe(),
        "affected": surface.query_sql(
            "SELECT service_id FROM affected_service ORDER BY service_id"
        ),
        "protected": surface.query_sql(
            """
            SELECT a.service_id, p.adapter_id
            FROM affected_service AS a
            JOIN protected_by AS p ON p.service_id = a.service_id
            ORDER BY a.service_id
            """
        ),
        "excluded": surface.query_sql(
            "SELECT subject_id, basis FROM excluded ORDER BY subject_id"
        ),
        "compatible_via": surface.query_sql(
            """
            SELECT service_id, old_library_id, new_library_id, adapter_id
            FROM compatible_via
            ORDER BY service_id
            """
        ),
        "verification_gap": surface.query_sql(
            "SELECT service_id FROM verification_gap ORDER BY service_id"
        ),
        "requires_change": surface.query_sql(
            "SELECT service_id FROM requires_change ORDER BY service_id"
        ),
        "exhaustive": view.absence_is_exhaustive("verification_gap"),
    }

    retract = surface.assertion(
        action="RETRACT",
        relation="verified_by",
        values={
            "service": "service:checkout",
            "test": "test:checkout-contract",
        },
    )
    stale = {
        "describe": surface.describe(),
        "exhaustive": view.absence_is_exhaustive("verification_gap"),
    }
    first_rerun = surface.rerun(
        "verification_gap",
        universe="affected_service",
        status="COMPLETE",
        basis="Every affected service was checked after checkout verification retraction.",
    )
    gap_after_retract = surface.query_sql(
        "SELECT service_id FROM verification_gap ORDER BY service_id"
    )

    asserted = surface.assertion(
        action="ASSERT",
        relation="verified_by",
        values={
            "service": "service:checkout",
            "test": "test:checkout-contract",
        },
        grounding=[
            {
                "kind": "SOURCE",
                "reference": "repo://tests/checkout-contract.yaml",
                "detail": "verification restored",
            }
        ],
    )
    second_rerun = surface.rerun(
        "verification_gap",
        universe="affected_service",
        status="COMPLETE",
        basis="Every affected service was checked after checkout verification restoration.",
    )
    restored = {
        "verification_gap": surface.query_sql(
            "SELECT service_id FROM verification_gap ORDER BY service_id"
        ),
        "exhaustive": view.absence_is_exhaustive("verification_gap"),
        "describe": surface.describe(),
    }
    return {
        "initial": initial,
        "retract": retract,
        "stale": stale,
        "first_rerun": first_rerun,
        "gap_after_retract": gap_after_retract,
        "assert": asserted,
        "second_rerun": second_rerun,
        "restored": restored,
    }
