"""Ledger-backed frozen TaskView fixture for the orientation experiment."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
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
)


PACKAGE_ROOT = Path(__file__).resolve().parent
FROZEN_ROOT = PACKAGE_ROOT / "frozen"
SOURCE_ROOT = FROZEN_ROOT / "source_initial"
LEDGER_PATH = FROZEN_ROOT / "grounding_ledger.json"
LEDGER_TEMPLATE_PATH = FROZEN_ROOT / "grounding_ledger.template.json"
FROZEN_DB_PATH = FROZEN_ROOT / "taskview.sqlite"

VIEW_ID = "jsonlib-v3-orientation-experiment"
TASK_SPEC_REF = "source://tasks/migrate-jsonlib-v3.md"


REFERENTS = {
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


BASE_RELATIONS = (
    ("component", (Role("component", RoleType.REFERENT),), "Pinned migration component inventory."),
    (
        "depends_on",
        (Role("component", RoleType.REFERENT), Role("dependency", RoleType.REFERENT)),
        "Pinned direct dependency relevant to this migration.",
    ),
    (
        "implements",
        (Role("service", RoleType.REFERENT), Role("component", RoleType.REFERENT)),
        "Deployable service-to-component realization.",
    ),
    (
        "production_service",
        (Role("service", RoleType.REFERENT),),
        "Pinned production service universe.",
    ),
    (
        "protected_by",
        (Role("service", RoleType.REFERENT), Role("adapter", RoleType.REFERENT)),
        "Accepted task protection by a compatibility adapter.",
    ),
    (
        "compatible_via",
        (
            Role("service", RoleType.REFERENT),
            Role("old_library", RoleType.REFERENT),
            Role("new_library", RoleType.REFERENT),
            Role("adapter", RoleType.REFERENT),
        ),
        "Accepted n-ary migration compatibility judgment.",
    ),
    (
        "verified_by",
        (Role("service", RoleType.REFERENT), Role("test", RoleType.REFERENT)),
        "Task-relevant verification relationship.",
    ),
    ("in_scope", (Role("subject", RoleType.REFERENT),), "Interior task scope."),
    ("boundary", (Role("subject", RoleType.REFERENT),), "Relevant opaque boundary."),
    (
        "excluded",
        (Role("subject", RoleType.REFERENT), Role("basis", RoleType.TEXT)),
        "Grounded exclusion from direct task change.",
    ),
    (
        "unresolved_scope",
        (Role("subject", RoleType.REFERENT),),
        "Consumer whose task-scope mapping remains unresolved.",
    ),
)


DERIVED_RELATIONS = (
    ("legacy_component", "component", "Components pinned to jsonlib v2."),
    (
        "affected_service",
        "service",
        "In-scope production services implementing a legacy component, minus exclusions.",
    ),
    (
        "verification_gap",
        "service",
        "Affected services without a current task-relevant verification assertion.",
    ),
    (
        "requires_change",
        "service",
        "Affected services requiring direct code change after protection and exclusion.",
    ),
    (
        "boundary_affected_service",
        "service",
        "Known affected services also represented as task boundaries.",
    ),
)


DERIVATIONS = {
    "legacy_component": {
        "inputs": ["component", "depends_on"],
        "sql": """
            SELECT DISTINCT c.component_id
            FROM component AS c
            JOIN depends_on AS d ON d.component_id = c.component_id
            WHERE d.dependency_id = 'library:jsonlib-v2'
        """,
    },
    "affected_service": {
        "inputs": [
            "legacy_component",
            "implements",
            "production_service",
            "in_scope",
            "excluded",
        ],
        "sql": """
            SELECT DISTINCT p.service_id
            FROM production_service AS p
            JOIN in_scope AS scope ON scope.subject_id = p.service_id
            JOIN implements AS i ON i.service_id = p.service_id
            JOIN legacy_component AS l ON l.component_id = i.component_id
            WHERE NOT EXISTS (
                SELECT 1 FROM excluded AS x WHERE x.subject_id = p.service_id
            )
        """,
    },
    "verification_gap": {
        "inputs": ["affected_service", "verified_by"],
        "sql": """
            SELECT a.service_id
            FROM affected_service AS a
            WHERE NOT EXISTS (
                SELECT 1 FROM verified_by AS v WHERE v.service_id = a.service_id
            )
        """,
    },
    "requires_change": {
        "inputs": ["affected_service", "protected_by", "excluded"],
        "sql": """
            SELECT a.service_id
            FROM affected_service AS a
            WHERE NOT EXISTS (
                SELECT 1 FROM protected_by AS p WHERE p.service_id = a.service_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM excluded AS x WHERE x.subject_id = a.service_id
            )
        """,
    },
    "boundary_affected_service": {
        "inputs": ["affected_service", "boundary"],
        "sql": """
            SELECT a.service_id
            FROM affected_service AS a
            JOIN boundary AS b ON b.subject_id = a.service_id
        """,
    },
}


COMPLETENESS_CONTRACTS = {
    "legacy_component": Completeness(
        CompletenessStatus.COMPLETE,
        universe="component",
        basis="Every component in the pinned build inventory was evaluated.",
    ),
    "affected_service": Completeness(
        CompletenessStatus.COMPLETE,
        universe="production_service",
        basis="Pinned production inventory, realization map, scope, and exclusions were evaluated.",
    ),
    "verification_gap": Completeness(
        CompletenessStatus.COMPLETE,
        universe="affected_service",
        basis="Every affected service was checked against current task-relevant verification assertions.",
    ),
    "requires_change": Completeness(
        CompletenessStatus.COMPLETE,
        universe="affected_service",
        basis="Every affected service was checked for accepted protection and exclusion.",
    ),
    "boundary_affected_service": Completeness(
        CompletenessStatus.UNKNOWN,
        universe="boundary",
        basis="The partner boundary is represented, but its internal consumers are opaque.",
        known_gaps=("partner-internal dependency inventory unavailable",),
    ),
}


def load_ledger(path: Path | None = None) -> dict[str, Any]:
    selected = path or (LEDGER_PATH if LEDGER_PATH.exists() else LEDGER_TEMPLATE_PATH)
    return json.loads(selected.read_text(encoding="utf-8"))


def _groundings(record: dict[str, Any]) -> tuple[Grounding, ...]:
    grounds = []
    for evidence in record["evidence"]:
        digest = evidence.get("source_sha256", "UNFROZEN")
        reference = (
            f"source://{evidence['path']}#L{evidence['start_line']}-"
            f"L{evidence['end_line']}@sha256:{digest}"
        )
        grounds.append(
            Grounding(
                GroundingKind.SOURCE,
                reference,
                f"{record['construction_category']}; {record['taskview_role']}",
            )
        )
    return tuple(grounds)


def _referent_groundings(ledger: dict[str, Any]) -> dict[str, Grounding]:
    by_referent: dict[str, Grounding] = {}
    for record in ledger["records"]:
        grounding = _groundings(record)[0]
        for value in record["tuple"].values():
            if isinstance(value, str) and value in REFERENTS:
                by_referent.setdefault(value, grounding)
    migration_reference = Grounding(
        GroundingKind.SOURCE,
        "source://vendor/jsonlib_v3_migration.md#L1-L13",
        "visible migration reference",
    )
    by_referent.setdefault("library:jsonlib-v3", migration_reference)
    return by_referent


def build_task_view(path: Path | str, *, ledger_path: Path | None = None) -> TaskView:
    """Create the exact initial experiment TaskView at a new path."""

    database_path = Path(path)
    if database_path.exists():
        raise FileExistsError(f"refusing to replace existing TaskView: {database_path}")
    ledger = load_ledger(ledger_path)
    view = TaskView(database_path, view_id=VIEW_ID, task_spec_ref=TASK_SPEC_REF)

    referent_grounds = _referent_groundings(ledger)
    for identity, label in REFERENTS.items():
        view.add_referent(
            identity,
            label=label,
            grounding=(referent_grounds[identity],),
        )

    for name, roles, description in BASE_RELATIONS:
        view.declare_relation(name, roles, description=description)
    for name, role_name, description in DERIVED_RELATIONS:
        view.declare_relation(
            name,
            (Role(role_name, RoleType.REFERENT),),
            mode=RelationMode.DERIVED,
            description=description,
        )

    for record in ledger["records"]:
        view.assert_tuple(
            record["relation"],
            record["tuple"],
            grounding=_groundings(record),
        )

    for relation, definition in DERIVATIONS.items():
        view.register_derivation(
            relation,
            inputs=definition["inputs"],
            sql=definition["sql"],
        )

    for relation in (
        "legacy_component",
        "affected_service",
        "verification_gap",
        "requires_change",
        "boundary_affected_service",
    ):
        view.run_derivation(relation, completeness=COMPLETENESS_CONTRACTS[relation])
    return view


def copy_frozen_task_view(destination: Path | str) -> TaskView:
    """Copy the frozen binary fixture for one isolated episode."""

    destination_path = Path(destination)
    if destination_path.exists():
        raise FileExistsError(f"refusing to replace existing TaskView: {destination_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FROZEN_DB_PATH, destination_path)
    return TaskView(destination_path, view_id=VIEW_ID, task_spec_ref=TASK_SPEC_REF)


def semantic_rows(view: TaskView) -> dict[str, list[dict[str, Any]]]:
    """Return a canonical semantic snapshot without internal receipt UUIDs."""

    description = view.describe()
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in description["relations"]:
        name = relation["name"]
        columns = [role["column"] for role in relation["roles"]]
        order = ", ".join(columns)
        rows[name] = view.query(f'SELECT {order} FROM "{name}" ORDER BY {order}')
    return dict(rows)

