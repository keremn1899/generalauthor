"""Research-only World API. Frozen semantic calculus. No trigger() primitive."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROLE_TYPES = {"REFERENT", "TEXT", "INTEGER", "REAL", "BOOLEAN"}
MODES = {"WORLD", "PURPOSE"}
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INSTANCES: list["World"] = []


def reset() -> None:
    _INSTANCES.clear()


def instances() -> list["World"]:
    return list(_INSTANCES)


def _ident(name: str, kind: str) -> str:
    if not _IDENT.match(name or ""):
        raise ValueError(f"invalid {kind} name {name!r}")
    return name


class World:
    def __init__(self) -> None:
        self.referents: dict[str, dict[str, Any]] = {}
        self.relations: dict[str, dict[str, Any]] = {}
        self.requirements: list[dict[str, Any]] = []
        self.holes: list[dict[str, Any]] = []
        self._purpose: Purpose | None = None
        _INSTANCES.append(self)

    def referent(self, kind: str, key: dict[str, Any], grounding: dict[str, Any] | None = None) -> str:
        kind = _ident(str(kind), "referent kind")
        parts = [f"{k}={key[k]}" for k in sorted(key)]
        rid = kind + ":" + "|".join(parts)
        self.referents[rid] = {"kind": kind, "key": dict(key), "grounding": grounding or {}}
        return rid

    def relation(
        self,
        name: str,
        roles: list[tuple[str, str]] | list[dict[str, str]],
        *,
        mode: str = "WORLD",
        derived: bool = False,
        description: str = "",
    ) -> str:
        name = _ident(name, "relation")
        if mode not in MODES:
            raise ValueError("mode must be WORLD or PURPOSE")
        parsed = []
        for role in roles:
            if isinstance(role, dict):
                rname, rtype = str(role.get("name")), str(role.get("type"))
            else:
                rname, rtype = str(role[0]), str(role[1])
            rname = _ident(rname, "role")
            if rtype not in ROLE_TYPES:
                raise ValueError(f"bad role type {rtype}")
            parsed.append({"name": rname, "type": rtype})
        self.relations[name] = {
            "name": name,
            "roles": parsed,
            "mode": mode,
            "derived": bool(derived),
            "description": description,
            "rows": [],
            "grounding": [],
        }
        return name

    def map(
        self,
        relation: str,
        rows: list[dict[str, Any]],
        *,
        grounding: dict[str, Any] | None = None,
    ) -> int:
        spec = self._rel(relation)
        role_names = [r["name"] for r in spec["roles"]]
        for row in rows:
            spec["rows"].append({k: row.get(k, "") for k in role_names})
        if grounding:
            spec["grounding"].append(grounding)
        return len(spec["rows"])

    def derive(
        self,
        name: str,
        rows: list[dict[str, Any]],
        *,
        roles: list[tuple[str, str]] | None = None,
        inputs: list[str] | None = None,
        grounding: dict[str, Any] | None = None,
        mode: str = "WORLD",
    ) -> int:
        if name not in self.relations:
            if not roles:
                raise ValueError(f"derive {name}: declare relation or pass roles")
            self.relation(name, roles, mode=mode, derived=True)
        else:
            self.relations[name]["derived"] = True
        spec = self._rel(name)
        spec["inputs"] = list(inputs or [])
        return self.map(name, rows, grounding=grounding)

    def purpose(self) -> "Purpose":
        if self._purpose is None:
            self._purpose = Purpose(self)
        return self._purpose

    def _rel(self, name: str) -> dict[str, Any]:
        if name not in self.relations:
            raise ValueError(f"unknown relation {name}")
        return self.relations[name]

    def _hole(self, **kwargs: Any) -> None:
        self.holes.append(
            {
                "requirement": kwargs.get("requirement"),
                "failure_kind": kwargs.get("failure_kind"),
                "relation": kwargs.get("relation"),
                "purpose": kwargs.get("purpose") or [],
                "subject": kwargs.get("subject") or {},
                "expected": kwargs.get("expected"),
                "observed": kwargs.get("observed"),
                "grounding": kwargs.get("grounding") or {},
            }
        )

    def snapshot(self) -> dict[str, Any]:
        groups = _group(self.holes)
        rel_counts = {name: len(spec.get("rows") or []) for name, spec in self.relations.items()}
        kinds: dict[str, int] = defaultdict(int)
        for row in self.referents.values():
            kinds[str(row.get("kind"))] += 1
        return {
            "ok": True,
            "n_referents": len(self.referents),
            "referent_kinds": dict(kinds),
            "relations": {
                name: {
                    "mode": spec.get("mode"),
                    "derived": spec.get("derived"),
                    "roles": spec.get("roles"),
                    "n_rows": len(spec.get("rows") or []),
                    "inputs": spec.get("inputs") or [],
                    "description": spec.get("description") or "",
                }
                for name, spec in self.relations.items()
            },
            "relation_row_counts": rel_counts,
            "requirements": self.requirements,
            "n_hole_instances": len(self.holes),
            "n_hole_groups": len(groups),
            "hole_groups": groups,
            "hole_instances": self.holes,
        }


class Purpose:
    def __init__(self, world: World) -> None:
        self.world = world
        world._purpose = self

    def require(
        self,
        name: str,
        *,
        relation: str | None = None,
        purpose: list[str] | str | None = None,
        note: str = "",
    ) -> None:
        self.world.requirements.append(
            {"name": name, "kind": "REQUIRE", "relation": relation, "purpose": _purposes(purpose), "note": note}
        )

    def require_unique(
        self,
        name: str,
        *,
        per: str | list[str],
        candidates: str,
        purpose: list[str] | str | None = None,
        cardinality: str = "ONE",
    ) -> None:
        per_roles = [per] if isinstance(per, str) else list(per)
        self.world.requirements.append(
            {
                "name": name,
                "kind": "UNIQUE",
                "relation": candidates,
                "per": per_roles,
                "cardinality": cardinality,
                "purpose": _purposes(purpose),
            }
        )
        spec = self.world._rel(candidates)
        role_names = [r["name"] for r in spec["roles"]]
        for role in per_roles:
            if role not in role_names:
                raise ValueError(f"require_unique {name}: {role} is not a role of {candidates}")
        buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        for row in spec["rows"]:
            buckets[tuple(str(row.get(r, "")) for r in per_roles)].append(row)
        if not spec["rows"]:
            self.world._hole(
                requirement=name,
                failure_kind="NO_MATERIALIZABLE_PATH",
                relation=candidates,
                purpose=_purposes(purpose),
                expected="candidates materialize",
                observed={"n": 0},
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
            subject = dict(zip(per_roles, key))
            self.world._hole(
                requirement=name,
                failure_kind=kind,
                relation=candidates,
                purpose=_purposes(purpose),
                subject=subject,
                expected=f"cardinality {cardinality}",
                observed={"n_candidates": n},
            )
            if n > 1:
                self.world._hole(
                    requirement=name,
                    failure_kind="MULTIPLE_CANDIDATES",
                    relation=candidates,
                    purpose=_purposes(purpose),
                    subject=subject,
                    expected="unique candidate",
                    observed={"n_candidates": n},
                )

    def require_materializable(
        self,
        name: str,
        *,
        relation: str,
        purpose: list[str] | str | None = None,
    ) -> None:
        self.world.requirements.append(
            {"name": name, "kind": "MATERIALIZABLE", "relation": relation, "purpose": _purposes(purpose)}
        )
        spec = self.world._rel(relation)
        if not spec["rows"]:
            self.world._hole(
                requirement=name,
                failure_kind="NO_MATERIALIZABLE_PATH",
                relation=relation,
                purpose=_purposes(purpose),
                expected="relation has rows",
                observed={"n": 0},
            )

    def require_interpreted(
        self,
        name: str,
        *,
        relation: str,
        field: str,
        known: list[Any] | None = None,
        purpose: list[str] | str | None = None,
        per: str | list[str] | None = None,
    ) -> None:
        known_set = {str(x) for x in (known if known is not None else [""])}
        self.world.requirements.append(
            {
                "name": name,
                "kind": "INTERPRETED",
                "relation": relation,
                "field": field,
                "known": sorted(known_set),
                "purpose": _purposes(purpose),
            }
        )
        spec = self.world._rel(relation)
        role_names = [r["name"] for r in spec["roles"]]
        if field not in role_names:
            raise ValueError(f"require_interpreted {name}: {field} is not a role of {relation}")
        per_roles = [per] if isinstance(per, str) else list(per or [])
        for row in spec["rows"]:
            val = str(row.get(field, ""))
            if val in known_set:
                continue
            subject = {field: val}
            for role in per_roles:
                if role in row:
                    subject[role] = row.get(role)
            self.world._hole(
                requirement=name,
                failure_kind="UNINTERPRETED",
                relation=relation,
                purpose=_purposes(purpose),
                subject=subject,
                expected=f"{field} in known {sorted(known_set)[:12]}",
                observed={"field": field, "value": val},
            )

    def require_numeric(
        self,
        name: str,
        *,
        relation: str,
        field: str,
        purpose: list[str] | str | None = None,
        per: str | list[str] | None = None,
    ) -> None:
        self.world.requirements.append(
            {"name": name, "kind": "NUMERIC", "relation": relation, "field": field, "purpose": _purposes(purpose)}
        )
        spec = self.world._rel(relation)
        role_names = [r["name"] for r in spec["roles"]]
        if field not in role_names:
            raise ValueError(f"require_numeric {name}: {field} is not a role of {relation}")
        per_roles = [per] if isinstance(per, str) else list(per or [])
        for row in spec["rows"]:
            val = str(row.get(field, "") or "").strip().replace(",", "")
            ok = False
            if val:
                try:
                    float(val)
                    ok = True
                except ValueError:
                    ok = False
            if ok:
                continue
            subject = {field: row.get(field, "")}
            for role in per_roles:
                if role in row:
                    subject[role] = row.get(role)
            self.world._hole(
                requirement=name,
                failure_kind="COMPARISON_OPERATOR_REQUIRED",
                relation=relation,
                purpose=_purposes(purpose),
                subject=subject,
                expected=f"numeric {field}",
                observed={"field": field, "value": row.get(field, "")},
            )

    def unresolved(
        self,
        name: str,
        *,
        subject: dict[str, Any] | None = None,
        relation: str | None = None,
        reason: str = "",
        purpose: list[str] | str | None = None,
        grounding: dict[str, Any] | None = None,
    ) -> None:
        self.world.requirements.append(
            {"name": name, "kind": "UNRESOLVED", "relation": relation, "purpose": _purposes(purpose), "note": reason}
        )
        self.world._hole(
            requirement=name,
            failure_kind="EXPLICIT_UNRESOLVED",
            relation=relation,
            purpose=_purposes(purpose),
            subject=subject or {},
            expected="purpose-computable interpretation",
            observed=reason,
            grounding=grounding or {},
        )


def _purposes(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    return list(value)


def _group(holes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for hole in holes:
        key = (hole.get("requirement"), hole.get("failure_kind"), hole.get("relation"))
        buckets[key].append(hole)
    groups = []
    for i, (key, members) in enumerate(sorted(buckets.items(), key=lambda kv: tuple(str(x) for x in kv[0]))):
        groups.append(
            {
                "group_id": f"g{i:03d}",
                "requirement": key[0],
                "failure_kind": key[1],
                "relation": key[2],
                "n_instances": len(members),
                "purpose": members[0].get("purpose") if members else [],
                "sample_subjects": [m.get("subject") for m in members[:12]],
                "expected": members[0].get("expected") if members else None,
            }
        )
    return groups


def dump_snapshot(snapshot: dict[str, Any], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    slim = dict(snapshot)
    instances = slim.pop("hole_instances", [])
    (dest / "spine.json").write_text(json.dumps(slim, indent=2, default=str) + "\n", encoding="utf-8")
    (dest / "holes.json").write_text(json.dumps(instances, indent=2, default=str) + "\n", encoding="utf-8")
