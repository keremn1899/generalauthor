"""`WorldExplorerAdapter` — the read surface the canvas talks to.

The front end needs the answers listed in §14 of the World IR front-end spec:
relation schemas, tuples, SQL, tuple inspection, construction origin, grounding,
staleness, completeness, derivation dependencies and unresolved obligations.
`SemanticWorld` and `TaskView` already answer nearly all of it — `describe()`
alone carries roles, types, columns, mode, counts, staleness and completeness —
so this module formats; it does not store.

That distinction is the one rule worth stating outright, because it is the one
that would quietly be broken first: **the adapter holds no state.** Every method
reads through to the open world. Nothing is cached, denormalised, or kept
between calls. An adapter that starts remembering is a second copy of the world
with its own staleness, which is exactly what rule 10 of the spec forbids and
what the tests here pin.

Two things it does have to reconcile, because the store and the product disagree
about words:

**Origin.** `_tv_assertions.origin` is `ASSERTED` or `DERIVED` — how the tuple
got into the table. The product means something else by origin: MECHANICAL,
SEMANTIC or DERIVED — who decided it, which is what the canvas paints. That
lives in the kernel's sidecar, via `origin_for_assertion`. A world compiled
without the backfill has no answer at all, and this reports `UNKNOWN` rather
than raising, because a missing origin is a fact about the world worth seeing on
screen, not a broken request.

**Roles versus columns.** A relation's role is `new_part`; its column is
`new_part_id` for a referent role and the bare name for a scalar. `describe()`
returns both, so nothing here guesses — and the referent/scalar split is what
decides whether a value becomes a node on the canvas or a field on a card.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import OriginMetadataError

#: Reported when a world carries no construction-origin sidecar for a tuple.
UNKNOWN_ORIGIN = "UNKNOWN"

#: Ceiling on rows any single call will return. The canvas is bounded by design
#: and the table pages; nothing downstream wants the whole extension in one
#: response, and a missing `limit` should not be able to ask for one.
MAX_ROWS = 500


def _demand_path(db_path: Path) -> Path:
    return db_path.with_suffix(".demand.json")


def view_id_of(db_path: Path | str) -> str:
    """The TaskView id a world file already carries.

    Asked of the file rather than of the caller. `TaskView` refuses to open a
    database whose `view_id` differs from the one passed in, and that id is set
    by whichever compiler wrote the file — so requiring the explorer to know it
    in advance turns opening a world into a guess, and the failure reads as a
    corrupt file rather than as a mismatched string.
    """
    connection = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ValueError(f"{db_path} is not a TaskView world")
    return str(row[0])


@dataclass(frozen=True)
class Role:
    name: str
    type: str
    column: str

    @property
    def referent(self) -> bool:
        return self.type == "REFERENT"


class WorldExplorerAdapter:
    """One open World, formatted for the explorer."""

    def __init__(self, path: Path | str, *, world_id: str | None = None) -> None:
        self.path = Path(path)
        self._world = SemanticWorld(
            self.path, world_id=world_id or view_id_of(self.path)
        )
        self._demand_document: dict[str, Any] | None = None
        demand = _demand_path(self.path)
        if demand.exists():
            self._demand_document = json.loads(demand.read_text(encoding="utf-8"))

    def close(self) -> None:
        self._world.close()

    def __enter__(self) -> "WorldExplorerAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # -- reading through ----------------------------------------------------

    @property
    def _view(self):
        return self._world.taskview

    def _described(self) -> list[dict[str, Any]]:
        return self._view.describe()["relations"]

    def _relation(self, name: str) -> dict[str, Any]:
        for record in self._described():
            if record["name"] == name:
                return record
        raise KeyError(f"no relation {name!r} in this world")

    @staticmethod
    def _roles(record: Mapping[str, Any]) -> list[Role]:
        return [Role(r["name"], r["type"], r["column"]) for r in record["roles"]]

    def _origin(self, assertion_id: str) -> str:
        try:
            return self._world.origin_for_assertion(assertion_id)
        except OriginMetadataError:
            return UNKNOWN_ORIGIN

    def _grounding(self, subject_type: str, subject_id: str) -> list[dict[str, Any]]:
        """Grounding with its detail opened up.

        TaskView stores `detail` as a JSON string, which is right for a store
        and wrong for the thing that has to draw `engineering_notes.md lines
        6-14` in a panel. Parsed here, once, rather than in every consumer —
        and the source handle and location are lifted to the top level because
        they are the whole of what §8.5 shows.

        Left as the raw string if it will not parse. A grounding this layer
        cannot read is still a grounding, and dropping it would be the one kind
        of loss this product cannot afford.
        """
        out: list[dict[str, Any]] = []
        for row in self._view.groundings(subject_type, subject_id):
            item: dict[str, Any] = {"kind": row["kind"], "reference": row["reference"]}
            try:
                detail = json.loads(row["detail"]) if row["detail"] else {}
            except (TypeError, ValueError):
                item["detail_text"] = row["detail"]
                out.append(item)
                continue
            item["detail"] = detail
            if isinstance(detail, Mapping):
                for key in ("native_handle", "native_location", "provider",
                            "source_revision", "construction_method",
                            "construction_origin"):
                    if key in detail:
                        item[key] = detail[key]
            out.append(item)
        return out

    def _row_out(self, roles: Sequence[Role], row: Mapping[str, Any]) -> dict[str, Any]:
        assertion_id = row["_assertion_id"]
        return {
            "assertion_id": assertion_id,
            "origin": self._origin(assertion_id),
            "values": {role.name: row[role.column] for role in roles},
        }

    # -- §7.1 world and schema ---------------------------------------------

    def overview(self) -> dict[str, Any]:
        described = self._described()
        counts = self._view.query(
            "SELECT (SELECT COUNT(*) FROM _tv_referents) AS referents, "
            "(SELECT COUNT(*) FROM _tv_assertions) AS assertions"
        )[0]
        origins: dict[str, int] = {}
        for row in self._view.query("SELECT assertion_id FROM _tv_assertions"):
            origin = self._origin(row["assertion_id"])
            origins[origin] = origins.get(origin, 0) + 1
        demand = self._demand_document
        return {
            "world_id": self._world.world_id,
            "revision": self._view.revision,
            "relations": len(described),
            "referents": counts["referents"],
            "assertions": counts["assertions"],
            "origins": origins,
            "stale": self._world.stale_relations(),
            "demand": None
            if demand is None
            else {
                "purpose": demand["purpose"],
                "obligations": demand["obligation_count"],
                "demanded": demand["candidate_case_count"],
            },
        }

    def schema(self) -> list[dict[str, Any]]:
        """Every relation, with the facts the schema canvas draws from.

        `arity` and the referent/scalar split are here rather than in the front
        end because they decide the projection — arity 2 collapses onto a
        filament, arity 3+ stands as a plate, and a scalar role never becomes a
        node at all. That is a rule about the world, not about the renderer.
        """
        out: list[dict[str, Any]] = []
        for record in self._described():
            roles = self._roles(record)
            item: dict[str, Any] = {
                "name": record["name"],
                "description": record["description"],
                "mode": record["mode"],
                "arity": len(roles),
                "roles": [
                    {
                        "name": role.name,
                        "type": role.type,
                        "column": role.column,
                        "referent": role.referent,
                        "kinds": self.role_kinds(record["name"], role.column)
                        if role.referent
                        else [],
                    }
                    for role in roles
                ],
                "referent_arity": sum(1 for role in roles if role.referent),
                "count": record["row_count"],
                "stale": record["stale"],
                "completeness": record["completeness"],
            }
            if record.get("derivation"):
                item["derivation"] = {
                    **record["derivation"],
                    "inputs": self.derivation_inputs(record["name"]),
                }
            out.append(item)
        return out

    #: How many distinct namespaces a role is reported as accepting before the
    #: answer stops being a type and starts being a list.
    MAX_ROLE_KINDS = 6

    def role_kinds(self, relation: str, column: str) -> list[str]:
        """The referent namespaces actually seen in one role, e.g. `["part"]`.

        World IR types a role as REFERENT and stops there — a role knows it
        takes a referent, not that it takes a *part*. But §7.1's schema view is
        drawn in exactly those terms (`SupplierListing ─ listing_of ─ Part`), so
        the kinds have to come from somewhere.

        They come from the data. Referent ids in this world are namespaced —
        `part:X160`, `context:outdoor_enclosure` — so the distinct prefixes a
        role has actually been filled with are an observation, not a schema
        claim, and this returns them as such. A role that has never been filled
        reports nothing, which is honest: an empty relation has no kinds to
        show, and inventing one would put a type on the canvas the world has
        never asserted.
        """
        rows = self._view.query(
            f'SELECT DISTINCT substr("{column}", 1, instr("{column}", \':\') - 1) '
            f'AS kind FROM "{relation}" '
            f'WHERE "{column}" IS NOT NULL AND instr("{column}", \':\') > 0 '
            f"ORDER BY kind LIMIT ?",
            (self.MAX_ROLE_KINDS,),
        )
        return [row["kind"] for row in rows if row["kind"]]

    def derivation_inputs(self, relation: str) -> list[str]:
        return [
            row["input_relation"]
            for row in self._view.query(
                "SELECT input_relation FROM _tv_derivation_inputs "
                "WHERE relation_name = ? ORDER BY input_relation",
                (relation,),
            )
        ]

    # -- §8.1 search --------------------------------------------------------

    def search(self, query: str, *, limit: int = 30) -> list[dict[str, Any]]:
        """Referents and relation names matching a substring.

        Deliberately dumb. At S100 the whole referent table is 3,118 rows and
        reads in 3ms, so the front end is expected to hold it and filter as you
        type; this exists for callers that are not the canvas.
        """
        needle = f"%{query}%"
        out: list[dict[str, Any]] = [
            {"kind": "referent", "id": row["id"], "label": row["label"]}
            for row in self._view.query(
                "SELECT id, label FROM _tv_referents "
                "WHERE id LIKE ? OR label LIKE ? ORDER BY id LIMIT ?",
                (needle, needle, min(limit, MAX_ROWS)),
            )
        ]
        lowered = query.lower()
        out.extend(
            {"kind": "relation", "id": record["name"], "label": record["description"]}
            for record in self._described()
            if lowered in record["name"].lower()
        )
        return out

    def referents(self) -> list[dict[str, Any]]:
        """Every referent, for a front end that wants to search locally."""
        return [
            {"id": row["id"], "label": row["label"]}
            for row in self._view.query("SELECT id, label FROM _tv_referents ORDER BY id")
        ]

    # -- §7.2 referent neighborhood ----------------------------------------

    def referent(self, referent_id: str) -> dict[str, Any]:
        """One referent, its scalar fields, and its relations *with counts*.

        Counts before matter: the canvas asks what expanding would cost before
        it expands, which is how a relation with four hundred tuples goes to the
        table instead of onto the field. Cheap enough to always do — 20 counting
        queries over the largest world is under a millisecond.
        """
        rows = self._view.query(
            "SELECT id, label FROM _tv_referents WHERE id = ?", (referent_id,)
        )
        if not rows:
            raise KeyError(f"no referent {referent_id!r} in this world")

        fields: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        for record in self._described():
            roles = self._roles(record)
            referent_roles = [role for role in roles if role.referent]
            if not referent_roles:
                continue
            where = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
            found = self._view.query(
                f'SELECT * FROM "{record["name"]}" WHERE {where}',
                [referent_id] * len(referent_roles),
            )
            if not found:
                continue
            scalar_roles = [role for role in roles if not role.referent]
            # A scalar-valued relation over exactly this referent is a property
            # of it as far as a reader is concerned — `rated_voltage 24` — so it
            # is offered as a card field. It stays an assertion: the field
            # carries its assertion id, so the inspector can still be opened on
            # it and its grounding read. §5.4 is a presentation rule, not a
            # claim that the value is stored on the referent.
            if len(referent_roles) == 1 and len(scalar_roles) == 1:
                for row in found:
                    fields.append(
                        {
                            "relation": record["name"],
                            "role": scalar_roles[0].name,
                            "value": row[scalar_roles[0].column],
                            "assertion_id": row["_assertion_id"],
                            "origin": self._origin(row["_assertion_id"]),
                        }
                    )
                continue
            relations.append(
                {
                    "name": record["name"],
                    "arity": len(roles),
                    "mode": record["mode"],
                    "stale": record["stale"],
                    "count": len(found),
                }
            )
        return {
            "id": rows[0]["id"],
            "label": rows[0]["label"],
            "grounding": self._grounding("REFERENT", referent_id),
            "fields": fields,
            "relations": sorted(relations, key=lambda item: item["name"]),
        }

    def expand(
        self, referent_id: str, relation: str, *, limit: int = MAX_ROWS
    ) -> dict[str, Any]:
        """The tuples of one relation that this referent takes part in."""
        record = self._relation(relation)
        roles = self._roles(record)
        referent_roles = [role for role in roles if role.referent]
        if not referent_roles:
            return {"relation": relation, "roles": [r.name for r in roles], "tuples": []}
        where = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
        rows = self._view.query(
            f'SELECT * FROM "{relation}" WHERE {where} LIMIT ?',
            [referent_id] * len(referent_roles) + [min(limit, MAX_ROWS)],
        )
        return {
            "relation": relation,
            "arity": len(roles),
            "roles": [
                {"name": role.name, "type": role.type, "referent": role.referent}
                for role in roles
            ],
            "tuples": [self._row_out(roles, row) for row in rows],
        }

    # -- §8.3 relation extension -------------------------------------------

    def rows(
        self,
        relation: str,
        *,
        limit: int = 200,
        offset: int = 0,
        order: str | None = None,
        descending: bool = False,
        subject: str | None = None,
    ) -> dict[str, Any]:
        """One page of a relation's extension, ordered in SQL.

        Sorting is the database's job, not the table component's. SQLite orders
        the largest relation in this world in well under a millisecond, and a
        client-side sort would only ever see the page it already has.

        `subject` narrows the extension to the tuples one referent takes part
        in — the same predicate `expand` uses, because it is the same question
        asked of a surface that pages instead of drawing. A referent's panel
        offers its own count, so a table opened from there that answered with
        the whole relation would be answering a question nobody asked. The
        total is the filtered total for the same reason.
        """
        record = self._relation(relation)
        roles = self._roles(record)
        columns = {role.name: role.column for role in roles}
        clause = ""
        if order:
            if order not in columns:
                raise KeyError(f"{relation!r} has no role {order!r}")
            clause = f' ORDER BY "{columns[order]}" {"DESC" if descending else "ASC"}'

        where = ""
        subject_values: list[Any] = []
        total = record["row_count"]
        if subject is not None:
            referent_roles = [role for role in roles if role.referent]
            if not referent_roles:
                return {
                    "relation": relation,
                    "mode": record["mode"],
                    "stale": record["stale"],
                    "total": 0,
                    "offset": offset,
                    "roles": [
                        {"name": role.name, "type": role.type, "referent": role.referent}
                        for role in roles
                    ],
                    "rows": [],
                }
            predicate = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
            where = f" WHERE ({predicate})"
            subject_values = [subject] * len(referent_roles)
            total = self._view.query(
                f'SELECT COUNT(*) AS n FROM "{relation}"{where}', subject_values
            )[0]["n"]

        rows = self._view.query(
            f'SELECT * FROM "{relation}"{where}{clause} LIMIT ? OFFSET ?',
            [*subject_values, min(limit, MAX_ROWS), max(0, offset)],
        )
        return {
            "relation": relation,
            "mode": record["mode"],
            "stale": record["stale"],
            "total": total,
            "offset": offset,
            "roles": [
                {"name": role.name, "type": role.type, "referent": role.referent}
                for role in roles
            ],
            "rows": [self._row_out(roles, row) for row in rows],
        }

    def query(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """The SQL surface, unhidden. Read-only by construction upstream."""
        return self._world.query(sql, parameters)

    # -- §8.4 / §8.5 / §8.6 assertion, grounding, derivation ---------------

    def assertion(self, assertion_id: str) -> dict[str, Any]:
        """Everything §8.4 asks for about one tuple, addressed by its id.

        By id rather than by role values because that is what a row and a chip
        both carry, and reconstructing a values map to look a tuple back up is
        an opportunity to get it subtly wrong.
        """
        found = self._view.query(
            "SELECT relation_name, origin, created_revision FROM _tv_assertions "
            "WHERE assertion_id = ?",
            (assertion_id,),
        )
        if not found:
            raise KeyError(f"no assertion {assertion_id!r} in this world")
        relation = found[0]["relation_name"]
        record = self._relation(relation)
        roles = self._roles(record)
        rows = self._view.query(
            f'SELECT * FROM "{relation}" WHERE _assertion_id = ?', (assertion_id,)
        )
        values = {role.name: rows[0][role.column] for role in roles} if rows else {}
        out: dict[str, Any] = {
            "assertion_id": assertion_id,
            "relation": relation,
            "mode": record["mode"],
            "arity": len(roles),
            "roles": [
                {"name": role.name, "type": role.type, "referent": role.referent}
                for role in roles
            ],
            "values": values,
            # The product's origin (who decided this), not the store's
            # (how it got into the table). Both are reported, because a reader
            # asking "why is this here" is served by neither alone.
            "origin": self._origin(assertion_id),
            "assertion_state": found[0]["origin"],
            "created_revision": int(found[0]["created_revision"]),
            "relation_stale": record["stale"],
            "completeness": record["completeness"],
            "grounding": self._grounding("ASSERTION", assertion_id),
        }
        if record["mode"] == "DERIVED":
            out["derivation"] = {
                **(record.get("derivation") or {}),
                "inputs": self.derivation_inputs(relation),
            }
        return out

    # -- §8.7 the unresolved frontier --------------------------------------

    def demand(self) -> dict[str, Any] | None:
        """What a declared purpose asked of this world, and what it did not get.

        Returns `None` when no purpose is loaded, and the caller is expected to
        say so rather than draw an empty frontier: unresolved is not a property
        of the world. It is the join between what a purpose demanded and what
        the world asserts, and with no purpose there is no such thing as an
        unresolved obligation — which is different from there being none.
        """
        document = self._demand_document
        if document is None:
            return None
        obligations = []
        for obligation in document["obligations"]:
            relation = obligation["relation"]
            values = obligation["values"]
            resolved = self._view.assertion_id_for_tuple(relation, values)
            exists = bool(
                self._view.query(
                    f'SELECT 1 FROM "{relation}" WHERE _assertion_id = ? LIMIT 1',
                    (resolved,),
                )
            )
            obligations.append(
                {
                    "relation": relation,
                    "values": values,
                    "demanded_by": obligation["demanded_by"],
                    "state": "ASSERTED" if exists else "UNRESOLVED",
                    "assertion_id": resolved if exists else None,
                }
            )
        return {
            "purpose": document["purpose"],
            "rule": document["generation_rule"],
            "demanded": document["candidate_case_count"],
            "obligations": obligations,
        }


def open_world(path: Path | str, *, world_id: str | None = None) -> WorldExplorerAdapter:
    return WorldExplorerAdapter(path, world_id=world_id)


__all__ = [
    "MAX_ROWS",
    "view_id_of",
    "UNKNOWN_ORIGIN",
    "Role",
    "WorldExplorerAdapter",
    "open_world",
]
