"""Deterministic purpose requirements. Failures are an ordinary PURPOSE relation.

``purpose_requirement_failure`` is a mechanism for explicit unresolvedness, not
a kernel primitive. See CONSTITUTION.md.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from ontology_author.world.core.model import RelationMode, Role, RoleType

from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.runtime.source_helpers import looks_numeric
from ontology_author.world.runtime.world import ConstructionWorld

FAILURE_RELATION = "purpose_requirement_failure"

FAILURE_ROLES = (
    Role("requirement_id", RoleType.TEXT),
    Role("affected_identity", RoleType.TEXT),
    Role("failure_kind", RoleType.TEXT),
    Role("relation_name", RoleType.TEXT),
    Role("subject_json", RoleType.TEXT),
    Role("grounding_ref", RoleType.TEXT),
)


def ensure_failure_relation(world: ConstructionWorld) -> str:
    return world.declare_relation(
        FAILURE_RELATION,
        list(FAILURE_ROLES),
        mode=RelationMode.BASE,
        description="Purpose requirement failures. Ordinary relation, not a kernel primitive.",
        scope="PURPOSE",
    )


class Purpose:
    def __init__(self, world: ConstructionWorld, *, text: str = "") -> None:
        self.world = world
        self.text = text
        self.requirements: list[dict[str, Any]] = []
        ensure_failure_relation(world)

    def require(
        self,
        name: str,
        *,
        relation: str | None = None,
        note: str = "",
    ) -> None:
        self.requirements.append(
            {"name": name, "kind": "REQUIRE", "relation": relation, "note": note}
        )

    def require_unique(
        self,
        name: str,
        *,
        per: str | list[str],
        candidates: str,
        cardinality: str = "ONE",
        requires_established_world: bool = True,
    ) -> None:
        per_roles = [per] if isinstance(per, str) else list(per)
        self.requirements.append(
            {
                "name": name,
                "kind": "UNIQUE",
                "relation": candidates,
                "per": per_roles,
                "cardinality": cardinality,
            }
        )
        if self._not_established(candidates, requires_established_world, name):
            return
        spec = self.world.relation_schema(candidates)
        role_names = {role["name"] for role in spec["roles"]}
        for role in per_roles:
            if role not in role_names:
                raise ValueError(f"require_unique {name}: {role} is not a role of {candidates}")
        buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        rows = self.world.relation_rows(candidates)
        for row in rows:
            buckets[tuple(str(row.get(role, "")) for role in per_roles)].append(row)
        if not rows:
            self._fail(
                name,
                "NO_MATERIALIZABLE_PATH",
                candidates,
                {},
                candidates,
            )
            return
        for key, members in buckets.items():
            n = len(members)
            if cardinality == "ONE" and n == 1:
                continue
            if cardinality == "ZERO_OR_ONE" and n <= 1:
                continue
            if cardinality == "AT_LEAST_ONE" and n >= 1:
                continue
            kind = "CARDINALITY_OVERSATISFIED" if n > 1 else "CARDINALITY_UNDERSATISFIED"
            subject = dict(zip(per_roles, key, strict=True))
            self._fail(name, kind, candidates, subject, _identity(subject, key))
            if n > 1:
                self._fail(
                    name,
                    "MULTIPLE_CANDIDATES",
                    candidates,
                    subject,
                    _identity(subject, key),
                )

    def require_materializable(
        self,
        name: str,
        *,
        relation: str,
        requires_established_world: bool = True,
    ) -> None:
        self.requirements.append(
            {"name": name, "kind": "MATERIALIZABLE", "relation": relation}
        )
        if self._not_established(relation, requires_established_world, name):
            return
        if not self.world.relation_rows(relation):
            self._fail(name, "NO_MATERIALIZABLE_PATH", relation, {}, relation)

    def require_interpreted(
        self,
        name: str,
        *,
        relation: str,
        field: str,
        known: list[Any] | None = None,
        per: str | list[str] | None = None,
        requires_established_world: bool = True,
    ) -> None:
        known_set = {str(item) for item in (known or [])}
        self.requirements.append(
            {
                "name": name,
                "kind": "INTERPRETED",
                "relation": relation,
                "field": field,
                "known": sorted(known_set),
            }
        )
        if self._not_established(relation, requires_established_world, name):
            return
        self._require_field(name, relation, field)
        per_roles = [per] if isinstance(per, str) else list(per or [])
        for row in self.world.relation_rows(relation):
            value = str(row.get(field, ""))
            if value in known_set:
                continue
            subject = {field: value}
            for role in per_roles:
                if role in row:
                    subject[role] = row.get(role)
            self._fail(
                name,
                "UNINTERPRETED",
                relation,
                subject,
                str(subject.get(per_roles[0], value) if per_roles else value),
            )

    def require_numeric(
        self,
        name: str,
        *,
        relation: str,
        field: str,
        per: str | list[str] | None = None,
        requires_established_world: bool = True,
    ) -> None:
        self.requirements.append(
            {"name": name, "kind": "NUMERIC", "relation": relation, "field": field}
        )
        if self._not_established(relation, requires_established_world, name):
            return
        self._require_field(name, relation, field)
        per_roles = [per] if isinstance(per, str) else list(per or [])
        for row in self.world.relation_rows(relation):
            raw = row.get(field, "")
            if looks_numeric(raw):
                continue
            subject = {field: raw}
            for role in per_roles:
                if role in row:
                    subject[role] = row.get(role)
            self._fail(
                name,
                "NOT_NUMERIC",
                relation,
                subject,
                str(subject.get(per_roles[0], raw) if per_roles else raw),
            )

    def unresolved(
        self,
        name: str,
        *,
        subject: dict[str, Any] | None = None,
        relation: str | None = None,
        reason: str = "",
        grounding_ref: str = "",
    ) -> None:
        self.requirements.append(
            {"name": name, "kind": "UNRESOLVED", "relation": relation, "note": reason}
        )
        payload = dict(subject or {})
        if reason:
            payload["reason"] = reason
        self._fail(
            name,
            "EXPLICIT_UNRESOLVED",
            relation or "",
            payload,
            str((subject or {}).get("order") or (subject or {}).get("affected") or name),
            grounding_ref=grounding_ref,
            origin=ConstructionOrigin.SEMANTIC,
        )

    def payload(self) -> dict[str, Any]:
        return {"text": self.text, "requirements": list(self.requirements)}

    def _require_field(self, name: str, relation: str, field: str) -> None:
        role_names = {role["name"] for role in self.world.relation_schema(relation)["roles"]}
        if field not in role_names:
            raise ValueError(f"{name}: {field} is not a role of {relation}")

    def _not_established(
        self, relation: str, requires_established_world: bool, name: str
    ) -> bool:
        if not requires_established_world:
            return False
        if self.world.admission.get(relation) != "PURPOSE":
            return False
        self._fail(
            name,
            "NOT_ESTABLISHED",
            relation,
            {"relation": relation},
            relation,
        )
        return True

    def _fail(
        self,
        requirement_id: str,
        failure_kind: str,
        relation_name: str,
        subject: dict[str, Any],
        affected_identity: str,
        *,
        grounding_ref: str = "",
        origin: ConstructionOrigin = ConstructionOrigin.MECHANICAL,
    ) -> None:
        self.world.assert_tuple(
            FAILURE_RELATION,
            {
                "requirement_id": str(requirement_id),
                "affected_identity": str(affected_identity),
                "failure_kind": str(failure_kind),
                "relation_name": str(relation_name),
                "subject_json": json.dumps(subject, sort_keys=True, default=str),
                "grounding_ref": str(grounding_ref),
            },
            origin=origin,
            grounding=None,
        )
def _identity(subject: dict[str, Any], key: tuple) -> str:
    if not key:
        return json.dumps(subject, sort_keys=True, default=str)
    return "|".join(str(item) for item in key)
