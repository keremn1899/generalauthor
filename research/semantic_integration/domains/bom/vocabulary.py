"""BOM relation vocabulary.  Domain config, not engine code."""

from __future__ import annotations

from taskview import RelationMode, Role, RoleType

from research.semantic_integration.core.kernel import SemanticWorld


REF = RoleType.REFERENT
TEXT = RoleType.TEXT
INTEGER = RoleType.INTEGER

BASE_RELATIONS: dict[str, list[Role]] = {
    "manufacturer_part": [Role("part", REF)],
    "supplier_listing": [Role("listing", REF)],
    "bom_item": [Role("bom_item", REF)],
    "part_type": [Role("part", REF), Role("part_type", TEXT)],
    "listing_of": [Role("listing", REF), Role("part", REF)],
    "offered_by": [Role("listing", REF), Role("supplier", REF)],
    "listing_availability": [Role("listing", REF), Role("state", TEXT)],
    "rated_voltage": [Role("part", REF), Role("volts", INTEGER)],
    "temperature_range": [
        Role("part", REF),
        Role("minimum_c", INTEGER),
        Role("maximum_c", INTEGER),
    ],
    "lifecycle": [Role("part", REF), Role("state", TEXT)],
    "requires_type": [Role("bom_item", REF), Role("part_type", TEXT)],
    "requires_voltage": [Role("bom_item", REF), Role("volts", INTEGER)],
    "requires_temperature": [
        Role("bom_item", REF),
        Role("minimum_c", INTEGER),
        Role("maximum_c", INTEGER),
    ],
    "deployment_environment": [Role("bom_item", REF), Role("environment", REF)],
    "candidate_replacement": [Role("new_part", REF), Role("old_part", REF)],
    "acceptable_replacement": [
        Role("new_part", REF),
        Role("old_part", REF),
        Role("context", REF),
    ],
}

DERIVED_RELATIONS: dict[str, list[Role]] = {
    "voltage_compatible": [Role("part", REF), Role("bom_item", REF)],
    "temperature_compatible": [Role("part", REF), Role("bom_item", REF)],
    "eligible_part": [Role("part", REF), Role("bom_item", REF)],
    "spec_conflict": [Role("part", REF), Role("property", TEXT)],
}


def declare_bom_schema(world: SemanticWorld) -> None:
    for name, roles in BASE_RELATIONS.items():
        world.declare_relation(name, roles)
    for name, roles in DERIVED_RELATIONS.items():
        world.declare_relation(name, roles, mode=RelationMode.DERIVED)
