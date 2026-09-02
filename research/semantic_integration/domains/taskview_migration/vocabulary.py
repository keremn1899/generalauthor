"""TaskView migration vocabulary as another domain over the same kernel."""

from __future__ import annotations

from taskview import RelationMode, Role, RoleType

from research.semantic_integration.core.kernel import SemanticWorld


REF = RoleType.REFERENT

BASE_RELATIONS: dict[str, list[Role]] = {
    "component": [Role("component", REF)],
    "depends_on": [Role("component", REF), Role("dependency", REF)],
    "production_service": [Role("service", REF)],
    "protected_by": [Role("service", REF), Role("adapter", REF)],
}

DERIVED_RELATIONS: dict[str, list[Role]] = {
    "requires_change": [Role("service", REF)],
}


def declare_migration_schema(world: SemanticWorld) -> None:
    for name, roles in BASE_RELATIONS.items():
        world.declare_relation(name, roles)
    for name, roles in DERIVED_RELATIONS.items():
        world.declare_relation(name, roles, mode=RelationMode.DERIVED)
