"""SQLite-backed TaskView vertical prototype.

The semantic plane consists of one real typed table per named relation.  Tables
prefixed with ``_tv_`` form the system plane: relation declarations, assertion
identity, grounding, derivations, revisions, and completeness receipts.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from taskview.model import (
    AssertionOrigin,
    AssertionRef,
    Completeness,
    CompletenessStatus,
    DerivationError,
    DerivationResult,
    ExecutionStatus,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
    TaskViewError,
)


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_SYSTEM_PREFIX = "_tv_"


def _identifier(value: str, what: str) -> str:
    text = str(value or "").strip()
    if not _IDENTIFIER.fullmatch(text) or text.startswith(_SYSTEM_PREFIX):
        raise TaskViewError(
            f"{what} must match {_IDENTIFIER.pattern!r} and not use {_SYSTEM_PREFIX!r}"
        )
    return text


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _enum(value: Any, enum_type: type, what: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = [item.value for item in enum_type]
        raise TaskViewError(f"{what} must be one of {allowed}, got {value!r}") from exc


class TaskView:
    """One versioned, task-scoped relational view stored in a SQLite file."""

    def __init__(
        self,
        path: Path | str,
        *,
        view_id: str,
        task_spec_ref: str = "",
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._create_system_schema()
        existing = self._db.execute(
            "SELECT view_id, task_spec_ref FROM _tv_view WHERE singleton = 1"
        ).fetchone()
        if existing is None:
            with self._db:
                self._db.execute(
                    "INSERT INTO _tv_view(singleton, view_id, task_spec_ref, revision) "
                    "VALUES (1, ?, ?, 0)",
                    (str(view_id), str(task_spec_ref)),
                )
        elif existing["view_id"] != str(view_id):
            raise TaskViewError(
                f"database belongs to TaskView {existing['view_id']!r}, not {view_id!r}"
            )
        elif task_spec_ref and existing["task_spec_ref"] != str(task_spec_ref):
            raise TaskViewError(
                "task specification reference differs from the stored TaskView"
            )

    def __enter__(self) -> "TaskView":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._db.close()

    def _create_system_schema(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS _tv_view (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                view_id TEXT NOT NULL UNIQUE,
                task_spec_ref TEXT NOT NULL,
                revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _tv_referents (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS _tv_relations (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT '',
                mode TEXT NOT NULL CHECK(mode IN ('BASE', 'DERIVED')),
                relation_version INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS _tv_roles (
                relation_name TEXT NOT NULL REFERENCES _tv_relations(name) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                role_type TEXT NOT NULL,
                column_name TEXT NOT NULL,
                PRIMARY KEY(relation_name, ordinal),
                UNIQUE(relation_name, role_name),
                UNIQUE(relation_name, column_name)
            );
            CREATE TABLE IF NOT EXISTS _tv_assertions (
                assertion_id TEXT PRIMARY KEY,
                relation_name TEXT NOT NULL REFERENCES _tv_relations(name) ON DELETE CASCADE,
                origin TEXT NOT NULL CHECK(origin IN ('ASSERTED', 'DERIVED')),
                created_revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _tv_groundings (
                grounding_id TEXT PRIMARY KEY,
                subject_type TEXT NOT NULL CHECK(subject_type IN ('REFERENT', 'ASSERTION')),
                subject_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('SOURCE', 'WORLD', 'ASSERTION', 'DERIVATION')),
                reference TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                UNIQUE(subject_type, subject_id, kind, reference, detail)
            );
            CREATE TABLE IF NOT EXISTS _tv_derivations (
                relation_name TEXT PRIMARY KEY REFERENCES _tv_relations(name) ON DELETE CASCADE,
                sql TEXT NOT NULL,
                definition_revision INTEGER NOT NULL,
                execution_status TEXT NOT NULL,
                last_run_view_revision INTEGER,
                result_fingerprint TEXT NOT NULL DEFAULT '',
                output_cardinality INTEGER,
                last_error TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS _tv_derivation_inputs (
                relation_name TEXT NOT NULL REFERENCES _tv_derivations(relation_name) ON DELETE CASCADE,
                input_relation TEXT NOT NULL REFERENCES _tv_relations(name),
                PRIMARY KEY(relation_name, input_relation)
            );
            CREATE TABLE IF NOT EXISTS _tv_derivation_run_inputs (
                relation_name TEXT NOT NULL REFERENCES _tv_derivations(relation_name) ON DELETE CASCADE,
                input_relation TEXT NOT NULL REFERENCES _tv_relations(name),
                relation_version INTEGER NOT NULL,
                cardinality INTEGER NOT NULL,
                PRIMARY KEY(relation_name, input_relation)
            );
            CREATE TABLE IF NOT EXISTS _tv_completeness (
                receipt_id TEXT PRIMARY KEY,
                target_relation TEXT NOT NULL REFERENCES _tv_relations(name),
                universe_relation TEXT NOT NULL REFERENCES _tv_relations(name),
                status TEXT NOT NULL CHECK(status IN ('COMPLETE', 'INCOMPLETE', 'UNKNOWN')),
                basis TEXT NOT NULL DEFAULT '',
                known_gaps_json TEXT NOT NULL DEFAULT '[]',
                view_revision INTEGER NOT NULL,
                execution_status TEXT NOT NULL,
                input_versions_json TEXT NOT NULL,
                input_cardinalities_json TEXT NOT NULL,
                output_cardinality INTEGER NOT NULL,
                result_fingerprint TEXT NOT NULL,
                execution_environment TEXT NOT NULL
            );
            """
        )
        self._db.commit()

    @property
    def revision(self) -> int:
        row = self._db.execute(
            "SELECT revision FROM _tv_view WHERE singleton = 1"
        ).fetchone()
        return int(row[0])

    def _bump_view(self) -> int:
        self._db.execute(
            "UPDATE _tv_view SET revision = revision + 1 WHERE singleton = 1"
        )
        return self.revision

    def _bump_relation(self, relation: str) -> None:
        self._db.execute(
            "UPDATE _tv_relations SET relation_version = relation_version + 1 "
            "WHERE name = ?",
            (relation,),
        )

    def add_referent(
        self,
        referent_id: str,
        *,
        label: str = "",
        grounding: Iterable[Grounding] = (),
    ) -> str:
        """Create or enrich a thin referent while preserving its stable ID."""

        identity = str(referent_id or "").strip()
        if not identity:
            raise TaskViewError("referent identity must be non-empty")
        row = self._db.execute(
            "SELECT label FROM _tv_referents WHERE id = ?", (identity,)
        ).fetchone()
        changed = row is None
        with self._db:
            if row is None:
                self._db.execute(
                    "INSERT INTO _tv_referents(id, label) VALUES (?, ?)",
                    (identity, str(label or "")),
                )
            elif label and row["label"] != str(label):
                self._db.execute(
                    "UPDATE _tv_referents SET label = ? WHERE id = ?",
                    (str(label), identity),
                )
                changed = True
            self._add_groundings("REFERENT", identity, grounding)
            if changed:
                self._bump_view()
        return identity

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
    ) -> str:
        relation = _identifier(name, "relation name")
        relation_mode = _enum(mode, RelationMode, "relation mode")
        if not roles:
            raise TaskViewError("a named relation needs at least one role")
        normalized: list[tuple[str, RoleType, str]] = []
        seen_roles: set[str] = set()
        seen_columns: set[str] = set()
        for role in roles:
            role_name = _identifier(role.name, "role name")
            role_type = _enum(role.type, RoleType, "role type")
            column = f"{role_name}_id" if role_type == RoleType.REFERENT else role_name
            if role_name in seen_roles or column in seen_columns:
                raise TaskViewError(f"duplicate role or physical column in {relation!r}")
            seen_roles.add(role_name)
            seen_columns.add(column)
            normalized.append((role_name, role_type, column))

        existing = self._db.execute(
            "SELECT name FROM _tv_relations WHERE name = ?", (relation,)
        ).fetchone()
        if existing is not None:
            actual = self.relation_schema(relation)
            expected = {
                "name": relation,
                "description": str(description),
                "mode": relation_mode.value,
                "roles": [
                    {"name": r, "type": t.value, "column": c}
                    for r, t, c in normalized
                ],
            }
            comparable = {key: actual[key] for key in expected}
            if comparable != expected:
                raise TaskViewError(f"relation {relation!r} already has a different schema")
            return relation

        column_sql = []
        for _role, role_type, column in normalized:
            if role_type == RoleType.REFERENT:
                definition = (
                    f"{_quote(column)} TEXT NOT NULL "
                    "REFERENCES _tv_referents(id)"
                )
            elif role_type == RoleType.TEXT:
                definition = f"{_quote(column)} TEXT NOT NULL"
            elif role_type == RoleType.INTEGER:
                definition = f"{_quote(column)} INTEGER NOT NULL"
            elif role_type == RoleType.REAL:
                definition = f"{_quote(column)} REAL NOT NULL"
            else:
                definition = (
                    f"{_quote(column)} INTEGER NOT NULL "
                    f"CHECK ({_quote(column)} IN (0, 1))"
                )
            column_sql.append(definition)
        unique = ", ".join(_quote(column) for _, _, column in normalized)
        ddl = (
            f"CREATE TABLE {_quote(relation)} ("
            "_assertion_id TEXT PRIMARY KEY, "
            + ", ".join(column_sql)
            + f", UNIQUE ({unique}))"
        )
        with self._db:
            self._db.execute(
                "INSERT INTO _tv_relations(name, description, mode) VALUES (?, ?, ?)",
                (relation, str(description), relation_mode.value),
            )
            self._db.executemany(
                "INSERT INTO _tv_roles"
                "(relation_name, ordinal, role_name, role_type, column_name) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (relation, index, role, role_type.value, column)
                    for index, (role, role_type, column) in enumerate(normalized)
                ],
            )
            self._db.execute(ddl)
        return relation

    def _relation_record(self, relation: str) -> sqlite3.Row:
        name = _identifier(relation, "relation name")
        row = self._db.execute(
            "SELECT * FROM _tv_relations WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            raise TaskViewError(f"unknown relation {name!r}")
        return row

    def _roles(self, relation: str) -> list[sqlite3.Row]:
        self._relation_record(relation)
        return list(
            self._db.execute(
                "SELECT * FROM _tv_roles WHERE relation_name = ? ORDER BY ordinal",
                (relation,),
            )
        )

    def relation_schema(self, relation: str) -> dict[str, Any]:
        record = self._relation_record(relation)
        return {
            "name": record["name"],
            "description": record["description"],
            "mode": record["mode"],
            "roles": [
                {
                    "name": row["role_name"],
                    "type": row["role_type"],
                    "column": row["column_name"],
                }
                for row in self._roles(relation)
            ],
        }

    def _normalize_values(
        self, relation: str, values: Mapping[str, Any]
    ) -> tuple[list[Any], list[str]]:
        roles = self._roles(relation)
        expected = {row["role_name"] for row in roles}
        if set(values) != expected:
            raise TaskViewError(
                f"{relation!r} expects roles {sorted(expected)}, got {sorted(values)}"
            )
        normalized: list[Any] = []
        columns: list[str] = []
        for row in roles:
            role_name = row["role_name"]
            role_type = RoleType(row["role_type"])
            value = values[role_name]
            if role_type == RoleType.REFERENT:
                value = str(value or "").strip()
                exists = self._db.execute(
                    "SELECT 1 FROM _tv_referents WHERE id = ?", (value,)
                ).fetchone()
                if not value or exists is None:
                    raise TaskViewError(
                        f"{relation}.{role_name} names unknown referent {value!r}"
                    )
            elif role_type == RoleType.TEXT:
                if not isinstance(value, str):
                    raise TaskViewError(f"{relation}.{role_name} must be TEXT")
            elif role_type == RoleType.INTEGER:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TaskViewError(f"{relation}.{role_name} must be INTEGER")
            elif role_type == RoleType.REAL:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TaskViewError(f"{relation}.{role_name} must be REAL")
                value = float(value)
            elif role_type == RoleType.BOOLEAN:
                if value not in (True, False, 0, 1):
                    raise TaskViewError(f"{relation}.{role_name} must be BOOLEAN")
                value = int(bool(value))
            normalized.append(value)
            columns.append(row["column_name"])
        return normalized, columns

    def assert_tuple(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        grounding: Iterable[Grounding] = (),
    ) -> AssertionRef:
        record = self._relation_record(relation)
        if record["mode"] != RelationMode.BASE.value:
            raise TaskViewError(f"derived relation {relation!r} cannot be manually edited")
        normalized, columns = self._normalize_values(relation, values)
        assertion_id = _stable_id(
            "assertion", [relation, list(zip(columns, normalized, strict=True))]
        )
        existing = self._db.execute(
            "SELECT assertion_id FROM _tv_assertions WHERE assertion_id = ?",
            (assertion_id,),
        ).fetchone()
        semantic_change = existing is None
        with self._db:
            if existing is None:
                next_revision = self.revision + 1
                placeholders = ", ".join("?" for _ in normalized)
                self._db.execute(
                    f"INSERT INTO {_quote(relation)}"
                    f"(_assertion_id, {', '.join(_quote(c) for c in columns)}) "
                    f"VALUES (?, {placeholders})",
                    [assertion_id, *normalized],
                )
                self._db.execute(
                    "INSERT INTO _tv_assertions"
                    "(assertion_id, relation_name, origin, created_revision) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        assertion_id,
                        relation,
                        AssertionOrigin.ASSERTED.value,
                        next_revision,
                    ),
                )
            self._add_groundings("ASSERTION", assertion_id, grounding)
            if semantic_change:
                self._bump_relation(relation)
                self._bump_view()
        return AssertionRef(assertion_id=assertion_id, inserted=existing is None)

    def assertion_id_for_tuple(
        self, relation: str, values: Mapping[str, Any]
    ) -> str:
        """Resolve the hidden identity from the complete semantic tuple."""

        normalized, columns = self._normalize_values(relation, values)
        return _stable_id(
            "assertion", [relation, list(zip(columns, normalized, strict=True))]
        )

    def retract_tuple(self, relation: str, values: Mapping[str, Any]) -> bool:
        """Retract a BASE assertion by semantic role values, never an internal ID."""

        return self.retract(relation, self.assertion_id_for_tuple(relation, values))

    def retract(self, relation: str, assertion_id: str) -> bool:
        record = self._relation_record(relation)
        if record["mode"] != RelationMode.BASE.value:
            raise TaskViewError(f"derived relation {relation!r} cannot be manually edited")
        exists = self._db.execute(
            "SELECT 1 FROM _tv_assertions WHERE assertion_id = ? AND relation_name = ?",
            (assertion_id, relation),
        ).fetchone()
        if exists is None:
            return False
        with self._db:
            self._db.execute(
                "DELETE FROM _tv_groundings WHERE subject_type = 'ASSERTION' "
                "AND subject_id = ?",
                (assertion_id,),
            )
            self._db.execute(
                f"DELETE FROM {_quote(relation)} WHERE _assertion_id = ?",
                (assertion_id,),
            )
            self._db.execute(
                "DELETE FROM _tv_assertions WHERE assertion_id = ?", (assertion_id,)
            )
            self._bump_relation(relation)
            self._bump_view()
        return True

    def _add_groundings(
        self, subject_type: str, subject_id: str, grounds: Iterable[Grounding]
    ) -> None:
        for ground in grounds:
            kind = str(ground.kind.value if hasattr(ground.kind, "value") else ground.kind)
            reference = str(ground.reference or "").strip()
            if not reference:
                raise TaskViewError("grounding reference must be non-empty")
            grounding_id = _stable_id(
                "ground", [subject_type, subject_id, kind, reference, ground.detail]
            )
            self._db.execute(
                "INSERT OR IGNORE INTO _tv_groundings"
                "(grounding_id, subject_type, subject_id, kind, reference, detail) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    grounding_id,
                    subject_type,
                    subject_id,
                    kind,
                    reference,
                    str(ground.detail),
                ),
            )

    def groundings(self, subject_type: str, subject_id: str) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._db.execute(
                "SELECT kind, reference, detail FROM _tv_groundings "
                "WHERE subject_type = ? AND subject_id = ? "
                "ORDER BY kind, reference, detail",
                (subject_type, subject_id),
            )
        ]

    def inspect_tuple(
        self, relation: str, values: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        """On-demand origin/grounding detail for one active semantic tuple."""

        assertion_id = self.assertion_id_for_tuple(relation, values)
        assertion = self._db.execute(
            "SELECT origin, created_revision FROM _tv_assertions "
            "WHERE assertion_id = ? AND relation_name = ?",
            (assertion_id, relation),
        ).fetchone()
        if assertion is None:
            return None
        out: dict[str, Any] = {
            "relation": relation,
            "tuple": dict(values),
            "origin": assertion["origin"],
            "created_revision": int(assertion["created_revision"]),
            "grounding": self.groundings("ASSERTION", assertion_id),
        }
        if assertion["origin"] == AssertionOrigin.DERIVED.value:
            out["derivation"] = relation
            out["input_versions"] = {
                row["input_relation"]: int(row["relation_version"])
                for row in self._db.execute(
                    "SELECT input_relation, relation_version "
                    "FROM _tv_derivation_run_inputs WHERE relation_name = ? "
                    "ORDER BY input_relation",
                    (relation,),
                )
            }
        return out

    def register_derivation(
        self,
        relation: str,
        *,
        sql: str,
        inputs: Sequence[str],
    ) -> None:
        record = self._relation_record(relation)
        if record["mode"] != RelationMode.DERIVED.value:
            raise TaskViewError(f"base relation {relation!r} cannot have a derivation")
        query = str(sql or "").strip().rstrip(";").strip()
        if not query or not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
            raise TaskViewError("derivation SQL must be one SELECT or WITH query")
        declared_inputs = sorted({_identifier(value, "input relation") for value in inputs})
        if relation in declared_inputs:
            raise TaskViewError("a derivation cannot declare its own output as an input")
        for input_relation in declared_inputs:
            self._relation_record(input_relation)
        previous = self._db.execute(
            "SELECT sql, definition_revision FROM _tv_derivations "
            "WHERE relation_name = ?",
            (relation,),
        ).fetchone()
        previous_inputs = {
            row[0]
            for row in self._db.execute(
                "SELECT input_relation FROM _tv_derivation_inputs "
                "WHERE relation_name = ?",
                (relation,),
            )
        }
        if previous is not None and previous["sql"] == query and previous_inputs == set(
            declared_inputs
        ):
            return
        definition_revision = (
            int(previous["definition_revision"]) + 1 if previous is not None else 1
        )
        status = (
            ExecutionStatus.STALE.value
            if previous is not None
            else ExecutionStatus.NEVER_RUN.value
        )
        with self._db:
            self._db.execute(
                "INSERT INTO _tv_derivations"
                "(relation_name, sql, definition_revision, execution_status) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(relation_name) DO UPDATE SET "
                "sql=excluded.sql, definition_revision=excluded.definition_revision, "
                "execution_status=excluded.execution_status, last_error=''",
                (relation, query, definition_revision, status),
            )
            self._db.execute(
                "DELETE FROM _tv_derivation_inputs WHERE relation_name = ?", (relation,)
            )
            self._db.executemany(
                "INSERT INTO _tv_derivation_inputs(relation_name, input_relation) "
                "VALUES (?, ?)",
                [(relation, input_relation) for input_relation in declared_inputs],
            )

    def query(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        """Run ordinary read-only SQL against semantic or inspection tables."""

        self._db.commit()
        self._db.execute("PRAGMA query_only = ON")
        try:
            cursor = self._db.execute(sql, parameters)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self._db.execute("PRAGMA query_only = OFF")

    def query_semantic(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        """Run read-only SQL restricted to declared semantic relation tables."""

        statement = str(sql or "").strip().rstrip(";").strip()
        if not re.match(r"^(SELECT|WITH)\b", statement, re.IGNORECASE):
            raise TaskViewError("query_sql accepts one SELECT or WITH statement")
        if re.search(
            r"(?i)(?<![a-z0-9_])(?:[_\"`\[])?_assertion_id(?:[\"`\]])?(?![a-z0-9_])",
            statement,
        ):
            raise TaskViewError("query_sql cannot expose hidden assertion IDs")

        allowed_tables = {
            row[0] for row in self._db.execute("SELECT name FROM _tv_relations")
        }

        def semantic_only(
            action: int,
            table: str | None,
            _column: str | None,
            _database: str | None,
            _trigger: str | None,
        ) -> int:
            if action == sqlite3.SQLITE_READ and table not in allowed_tables:
                return sqlite3.SQLITE_DENY
            if (
                action == sqlite3.SQLITE_READ
                and str(_column or "").startswith("_")
                and _column != "_assertion_id"
            ):
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_PRAGMA:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        self._db.commit()
        self._db.execute("PRAGMA query_only = ON")
        self._db.set_authorizer(semantic_only)
        try:
            cursor = self._db.execute(statement, parameters)
            return [
                {
                    key: value
                    for key, value in dict(row).items()
                    if not key.startswith("_")
                }
                for row in cursor.fetchall()
            ]
        finally:
            self._db.set_authorizer(None)
            self._db.execute("PRAGMA query_only = OFF")

    def _relation_version(self, relation: str) -> int:
        return int(self._relation_record(relation)["relation_version"])

    def _cardinality(self, relation: str) -> int:
        self._relation_record(relation)
        return int(
            self._db.execute(
                f"SELECT count(*) FROM {_quote(relation)}"
            ).fetchone()[0]
        )

    def run_derivation(
        self,
        relation: str,
        *,
        completeness: Completeness,
    ) -> DerivationResult:
        relation_record = self._relation_record(relation)
        if relation_record["mode"] != RelationMode.DERIVED.value:
            raise TaskViewError(f"base relation {relation!r} cannot be derived")
        derivation = self._db.execute(
            "SELECT * FROM _tv_derivations WHERE relation_name = ?", (relation,)
        ).fetchone()
        if derivation is None:
            raise TaskViewError(f"derived relation {relation!r} has no registered SQL")
        universe = _identifier(completeness.universe, "universe relation")
        self._relation_record(universe)
        completeness_status = _enum(
            completeness.status, CompletenessStatus, "completeness status"
        )
        if completeness_status == CompletenessStatus.COMPLETE and completeness.known_gaps:
            raise TaskViewError("a COMPLETE receipt cannot declare known gaps")

        declared_inputs = [
            row[0]
            for row in self._db.execute(
                "SELECT input_relation FROM _tv_derivation_inputs "
                "WHERE relation_name = ? ORDER BY input_relation",
                (relation,),
            )
        ]
        for input_relation in declared_inputs:
            input_record = self._relation_record(input_relation)
            if input_record["mode"] == RelationMode.DERIVED.value:
                state = self.derivation_state(input_relation)
                if state != ExecutionStatus.SUCCEEDED.value:
                    raise DerivationError(
                        f"cannot run {relation!r}: derived input {input_relation!r} "
                        f"is {state.lower()}"
                    )
        receipt_inputs = sorted(set(declared_inputs) | {universe})
        input_versions = {
            input_relation: self._relation_version(input_relation)
            for input_relation in receipt_inputs
        }
        input_cardinalities = {
            input_relation: self._cardinality(input_relation)
            for input_relation in receipt_inputs
        }

        expected_columns = [row["column_name"] for row in self._roles(relation)]
        read_tables: set[str] = set()

        def record_reads(
            action: int,
            table: str | None,
            _column: str | None,
            _database: str | None,
            _trigger: str | None,
        ) -> int:
            if action == sqlite3.SQLITE_READ and table:
                read_tables.add(str(table))
            return sqlite3.SQLITE_OK

        try:
            self._db.commit()
            self._db.execute("PRAGMA query_only = ON")
            self._db.set_authorizer(record_reads)
            try:
                cursor = self._db.execute(derivation["sql"])
                actual_columns = [item[0] for item in cursor.description or ()]
                raw_rows = cursor.fetchall()
            finally:
                self._db.set_authorizer(None)
                self._db.execute("PRAGMA query_only = OFF")
            semantic_tables = {
                row[0] for row in self._db.execute("SELECT name FROM _tv_relations")
            }
            undeclared = sorted(
                (read_tables & semantic_tables) - set(declared_inputs)
            )
            if undeclared:
                raise DerivationError(
                    f"{relation!r} SQL reads undeclared input relations {undeclared}"
                )
            if actual_columns != expected_columns:
                raise DerivationError(
                    f"{relation!r} derivation must return columns {expected_columns}, "
                    f"got {actual_columns}"
                )
            logical_roles = [row["role_name"] for row in self._roles(relation)]
            normalized_rows = [
                self._normalize_values(
                    relation, dict(zip(logical_roles, tuple(row), strict=True))
                )[0]
                for row in raw_rows
            ]
            deduplicated = sorted(
                {tuple(values) for values in normalized_rows},
                key=lambda row: json.dumps(row, separators=(",", ":"), default=str),
            )
        except (sqlite3.Error, TaskViewError) as exc:
            with self._db:
                self._db.execute(
                    "UPDATE _tv_derivations SET execution_status = ?, last_error = ? "
                    "WHERE relation_name = ?",
                    (ExecutionStatus.FAILED.value, str(exc), relation),
                )
            if isinstance(exc, DerivationError):
                raise
            raise DerivationError(f"derivation {relation!r} failed: {exc}") from exc

        fingerprint = _stable_id("result", [relation, deduplicated])
        receipt_id = f"receipt:{uuid.uuid4().hex}"
        roles = self._roles(relation)
        columns = [row["column_name"] for row in roles]
        current_assertions = [
            row[0]
            for row in self._db.execute(
                f"SELECT _assertion_id FROM {_quote(relation)}"
            )
        ]
        with self._db:
            if current_assertions:
                placeholders = ",".join("?" for _ in current_assertions)
                self._db.execute(
                    f"DELETE FROM _tv_groundings WHERE subject_type = 'ASSERTION' "
                    f"AND subject_id IN ({placeholders})",
                    current_assertions,
                )
            self._db.execute(f"DELETE FROM {_quote(relation)}")
            self._db.execute(
                "DELETE FROM _tv_assertions WHERE relation_name = ?", (relation,)
            )
            for values in deduplicated:
                assertion_id = _stable_id(
                    "assertion", [relation, list(zip(columns, values, strict=True))]
                )
                placeholders = ", ".join("?" for _ in values)
                self._db.execute(
                    f"INSERT INTO {_quote(relation)}"
                    f"(_assertion_id, {', '.join(_quote(c) for c in columns)}) "
                    f"VALUES (?, {placeholders})",
                    [assertion_id, *values],
                )
                self._db.execute(
                    "INSERT INTO _tv_assertions"
                    "(assertion_id, relation_name, origin, created_revision) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        assertion_id,
                        relation,
                        AssertionOrigin.DERIVED.value,
                        self.revision,
                    ),
                )
                self._add_groundings(
                    "ASSERTION",
                    assertion_id,
                    [Grounding(kind=GroundingKind.DERIVATION, reference=relation)],
                )
            self._bump_relation(relation)
            self._db.execute(
                "DELETE FROM _tv_derivation_run_inputs WHERE relation_name = ?",
                (relation,),
            )
            self._db.executemany(
                "INSERT INTO _tv_derivation_run_inputs"
                "(relation_name, input_relation, relation_version, cardinality) "
                "VALUES (?, ?, ?, ?)",
                [
                    (
                        relation,
                        input_relation,
                        input_versions[input_relation],
                        input_cardinalities[input_relation],
                    )
                    for input_relation in receipt_inputs
                ],
            )
            self._db.execute(
                "UPDATE _tv_derivations SET execution_status = ?, "
                "last_run_view_revision = ?, result_fingerprint = ?, "
                "output_cardinality = ?, last_error = '' WHERE relation_name = ?",
                (
                    ExecutionStatus.SUCCEEDED.value,
                    self.revision,
                    fingerprint,
                    len(deduplicated),
                    relation,
                ),
            )
            self._db.execute(
                "INSERT INTO _tv_completeness"
                "(receipt_id, target_relation, universe_relation, status, basis, "
                "known_gaps_json, view_revision, execution_status, "
                "input_versions_json, input_cardinalities_json, output_cardinality, "
                "result_fingerprint, execution_environment) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt_id,
                    relation,
                    universe,
                    completeness_status.value,
                    str(completeness.basis),
                    json.dumps(list(completeness.known_gaps), sort_keys=True),
                    self.revision,
                    ExecutionStatus.SUCCEEDED.value,
                    json.dumps(input_versions, sort_keys=True),
                    json.dumps(input_cardinalities, sort_keys=True),
                    len(deduplicated),
                    fingerprint,
                    f"sqlite:{sqlite3.sqlite_version}",
                ),
            )
        return DerivationResult(
            relation=relation,
            row_count=len(deduplicated),
            result_fingerprint=fingerprint,
            view_revision=self.revision,
            completeness_receipt_id=receipt_id,
        )

    def is_stale(self, relation: str, _visiting: set[str] | None = None) -> bool:
        record = self._relation_record(relation)
        if record["mode"] != RelationMode.DERIVED.value:
            return False
        derivation = self._db.execute(
            "SELECT execution_status FROM _tv_derivations WHERE relation_name = ?",
            (relation,),
        ).fetchone()
        if derivation is None or derivation["execution_status"] in {
            ExecutionStatus.NEVER_RUN.value,
            ExecutionStatus.FAILED.value,
            ExecutionStatus.STALE.value,
        }:
            return derivation is not None and derivation["execution_status"] == ExecutionStatus.STALE.value
        visiting = set(_visiting or ())
        if relation in visiting:
            raise TaskViewError(f"cyclic derivation dependency involving {relation!r}")
        visiting.add(relation)
        run_inputs = list(
            self._db.execute(
                "SELECT input_relation, relation_version FROM _tv_derivation_run_inputs "
                "WHERE relation_name = ?",
                (relation,),
            )
        )
        if not run_inputs:
            return True
        for row in run_inputs:
            input_relation = row["input_relation"]
            if self._relation_version(input_relation) != int(row["relation_version"]):
                return True
            input_record = self._relation_record(input_relation)
            if (
                input_record["mode"] == RelationMode.DERIVED.value
                and self.is_stale(input_relation, visiting)
            ):
                return True
        return False

    def stale_relations(self) -> list[str]:
        return [
            row[0]
            for row in self._db.execute(
                "SELECT name FROM _tv_relations WHERE mode = 'DERIVED' ORDER BY name"
            )
            if self.is_stale(row[0])
        ]

    def derivation_state(self, relation: str) -> str:
        record = self._relation_record(relation)
        if record["mode"] != RelationMode.DERIVED.value:
            raise TaskViewError(f"base relation {relation!r} has no derivation state")
        derivation = self._db.execute(
            "SELECT execution_status FROM _tv_derivations WHERE relation_name = ?",
            (relation,),
        ).fetchone()
        if derivation is None:
            return ExecutionStatus.NEVER_RUN.value
        if self.is_stale(relation):
            return ExecutionStatus.STALE.value
        return str(derivation["execution_status"])

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        self._relation_record(relation)
        row = self._db.execute(
            "SELECT * FROM _tv_completeness WHERE target_relation = ? "
            "ORDER BY rowid DESC LIMIT 1",
            (relation,),
        ).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["known_gaps"] = json.loads(out.pop("known_gaps_json"))
        out["input_versions"] = json.loads(out.pop("input_versions_json"))
        out["input_cardinalities"] = json.loads(
            out.pop("input_cardinalities_json")
        )
        out["stale"] = self.is_stale(relation)
        out["current"] = not out["stale"]
        return out

    def universe_is_sufficient(self, universe: str) -> bool:
        """Whether a named universe may support exhaustive negative reasoning.

        A BASE universe is authoritative by extension: the claim is over the
        explicitly listed set, not that the set models the whole world. A
        DERIVED universe must itself be current and explicitly COMPLETE.
        """

        record = self._relation_record(universe)
        if record["mode"] == RelationMode.BASE.value:
            return True
        receipt = self.latest_completeness(universe)
        return bool(
            receipt
            and receipt["current"]
            and receipt["execution_status"] == ExecutionStatus.SUCCEEDED.value
            and receipt["status"] == CompletenessStatus.COMPLETE.value
        )

    def completeness_state(self, relation: str) -> str:
        """Currentness of the latest receipt without changing its declared status."""

        receipt = self.latest_completeness(relation)
        if receipt is None:
            return "NONE"
        if not receipt["current"]:
            return "STALE"
        if not self.universe_is_sufficient(receipt["universe_relation"]):
            return "UNIVERSE_NOT_COMPLETE"
        return "CURRENT"

    def absence_is_exhaustive(self, relation: str) -> bool:
        receipt = self.latest_completeness(relation)
        return bool(
            receipt
            and self._cardinality(relation) == 0
            and receipt["status"] == CompletenessStatus.COMPLETE.value
            and receipt["execution_status"] == ExecutionStatus.SUCCEEDED.value
            and not receipt["stale"]
            and self.universe_is_sufficient(receipt["universe_relation"])
        )

    def describe(self) -> dict[str, Any]:
        view = dict(
            self._db.execute(
                "SELECT view_id, task_spec_ref, revision FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        )
        relations = []
        for row in self._db.execute(
            "SELECT * FROM _tv_relations ORDER BY name"
        ):
            schema = self.relation_schema(row["name"])
            item = {
                **schema,
                "relation_version": int(row["relation_version"]),
                "row_count": self._cardinality(row["name"]),
                "stale": self.is_stale(row["name"]),
                "completeness": self.latest_completeness(row["name"]),
            }
            if row["mode"] == RelationMode.DERIVED.value:
                derivation = self._db.execute(
                    "SELECT definition_revision, execution_status, "
                    "last_run_view_revision, output_cardinality, last_error "
                    "FROM _tv_derivations WHERE relation_name = ?",
                    (row["name"],),
                ).fetchone()
                item["derivation"] = {
                    "state": self.derivation_state(row["name"]),
                    "definition_revision": (
                        int(derivation["definition_revision"]) if derivation else None
                    ),
                    "last_run_view_revision": (
                        derivation["last_run_view_revision"] if derivation else None
                    ),
                    "output_cardinality": (
                        derivation["output_cardinality"] if derivation else None
                    ),
                    "last_error": derivation["last_error"] if derivation else "",
                    "inputs": [
                        value[0]
                        for value in self._db.execute(
                            "SELECT input_relation FROM _tv_derivation_inputs "
                            "WHERE relation_name = ? ORDER BY input_relation",
                            (row["name"],),
                        )
                    ],
                }
            relations.append(item)
        return {"view": view, "relations": relations}

    def describe_text(self) -> str:
        lines = [
            f"TaskView {self.describe()['view']['view_id']} revision {self.revision}"
        ]
        for relation in self.describe()["relations"]:
            signature = ", ".join(
                f"{role['name']} {role['type']}" for role in relation["roles"]
            )
            suffix = " STALE" if relation["stale"] else ""
            lines.append(
                f"{relation['name']}({signature}) {relation['mode']}{suffix}"
            )
            if relation["description"]:
                lines.append(f"  {relation['description']}")
            if relation["completeness"]:
                completeness = relation["completeness"]
                lines.append(
                    "  completeness: "
                    f"{completeness['status']} over {completeness['universe_relation']}"
                )
        return "\n".join(lines)
