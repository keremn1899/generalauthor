"""Deterministic Construction IR compiler. No model. No gold. No NPDES primitives."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

FORBIDDEN_KEYS = {"triggers", "trigger_rules", "gold", "expected", "families"}
ALLOWED_SOURCES = {
    "dmr_measurements.csv",
    "permit_limits.csv",
    "document_inventory.json",
}
ROLE_TYPES = {"REFERENT", "TEXT", "INTEGER", "REAL", "BOOLEAN"}
CARDINALITIES = {"ONE", "ZERO_OR_ONE", "AT_LEAST_ONE"}
DIAGNOSTICS = {
    "CARDINALITY_UNDERSATISFIED",
    "CARDINALITY_OVERSATISFIED",
    "NO_MATERIALIZABLE_PATH",
    "MULTIPLE_CANDIDATES",
    "UNINTERPRETED_REQUIRED_CODE",
    "COMPARISON_OPERATOR_REQUIRED",
    "CONFLICTING_APPLICABLE_RELATIONS",
    "UNBOUND_CORRESPONDENCE",
}
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_date(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _ident(name: str, *, kind: str) -> str:
    if not _IDENT.match(name or ""):
        raise ValueError(f"invalid {kind} name {name!r}")
    return name


def load_source(sources_dir: Path, name: str) -> list[dict[str, Any]]:
    path = sources_dir / name
    if not path.exists():
        raise FileNotFoundError(name)
    if name.endswith(".json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [row if isinstance(row, dict) else {"value": row} for row in payload]
        if isinstance(payload, dict):
            return [payload]
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def compile_program(program: dict[str, Any], sources_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(program, dict):
        return _fail(["program.json must be a JSON object"])
    bad = FORBIDDEN_KEYS.intersection(program)
    if bad:
        return _fail([f"forbidden key(s) {sorted(bad)} — do not author triggers or gold"])
    try:
        referents = program.get("referents") or []
        maps = program.get("maps") or []
        relations = program.get("relations") or []
        requirements = program.get("requirements") or []
        if not isinstance(referents, list) or not isinstance(maps, list):
            raise ValueError("referents and maps must be lists")
        if not isinstance(relations, list) or not isinstance(requirements, list):
            raise ValueError("relations and requirements must be lists")
    except ValueError as exc:
        return _fail([str(exc)])

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    spine: dict[str, Any] = {"referents": {}, "relations": {}}
    triggers: list[dict[str, Any]] = []

    try:
        ref_defs = {}
        for item in referents:
            name = _ident(str(item.get("name") or ""), kind="referent")
            key = list(item.get("key") or [])
            if not key:
                raise ValueError(f"referent {name} needs key")
            ref_defs[name] = key
            spine["referents"][name] = 0

        loaded: dict[str, list[dict[str, Any]]] = {}
        map_rows: dict[str, list[dict[str, Any]]] = {}
        for item in maps:
            mid = _ident(str(item.get("id") or ""), kind="map")
            source = str(item.get("source") or "")
            if source not in ALLOWED_SOURCES:
                raise ValueError(f"map {mid}: source must be one of {sorted(ALLOWED_SOURCES)}")
            referent = str(item.get("referent") or "")
            if referent not in ref_defs:
                raise ValueError(f"map {mid}: unknown referent {referent}")
            fields = item.get("fields") or {}
            if not isinstance(fields, dict) or not fields:
                raise ValueError(f"map {mid}: fields required")
            if source not in loaded:
                loaded[source] = load_source(sources_dir, source)
            rows_out = []
            for raw in loaded[source]:
                mapped = {}
                for alias, column in fields.items():
                    mapped[str(alias)] = raw.get(str(column), "")
                key_vals = [str(mapped.get(k, "")).strip() for k in ref_defs[referent]]
                mapped["_referent"] = f"{referent}:" + "|".join(key_vals)
                mapped["_map"] = mid
                mapped["_source"] = source
                rows_out.append(mapped)
            map_rows[mid] = rows_out
            spine["referents"][referent] = spine["referents"].get(referent, 0) + len(rows_out)

        rel_defs: dict[str, dict[str, Any]] = {}
        for item in relations:
            name = _ident(str(item.get("name") or ""), kind="relation")
            kind = str(item.get("kind") or "")
            roles = item.get("roles") or []
            if kind not in {"base", "derived"}:
                raise ValueError(f"relation {name}: kind must be base|derived")
            if not roles:
                raise ValueError(f"relation {name}: roles required")
            for role in roles:
                rname = _ident(str(role.get("name") or ""), kind="role")
                rtype = str(role.get("type") or "")
                if rtype not in ROLE_TYPES:
                    raise ValueError(f"{name}.{rname}: bad type")
            rel_defs[name] = item
            cols = ["_rowid INTEGER PRIMARY KEY"]
            for role in roles:
                cols.append(f'"{role["name"]}" TEXT')
            db.execute(f'DROP TABLE IF EXISTS "{name}"')
            db.execute(f'CREATE TABLE "{name}" ({", ".join(cols)})')
            if kind == "base":
                mid = str(item.get("map") or "")
                if mid not in map_rows:
                    raise ValueError(f"relation {name}: unknown map {mid}")
                n_unbound = 0
                inserted = 0
                for row in map_rows[mid]:
                    values = []
                    unbound = False
                    for role in roles:
                        field = str(role.get("field") or "")
                        val = row.get(field, "")
                        if role.get("type") == "REFERENT" and field == "_referent":
                            val = row.get("_referent", "")
                        if role.get("type") == "REFERENT" and val in (None, ""):
                            unbound = True
                        values.append("" if val is None else str(val))
                    if unbound:
                        n_unbound += 1
                    placeholders = ",".join("?" for _ in roles)
                    role_names = ",".join(f'"{r["name"]}"' for r in roles)
                    db.execute(
                        f'INSERT INTO "{name}" ({role_names}) VALUES ({placeholders})',
                        values,
                    )
                    inserted += 1
                spine["relations"][name] = {"kind": "base", "rows": inserted, "unbound": n_unbound}
                if n_unbound:
                    triggers.append(
                        _trig(
                            "UNBOUND_CORRESPONDENCE",
                            requirement_id=None,
                            relation=name,
                            subject={"unbound_rows": n_unbound},
                            expected="mapped roles populated",
                            observed=f"{n_unbound}/{inserted} rows had empty roles",
                        )
                    )
            else:
                inputs = list(item.get("from") or [])
                match = list(item.get("match") or [])
                where = list(item.get("where") or [])
                if len(inputs) < 2:
                    raise ValueError(f"derived {name}: from needs >=2 relations")
                for src in inputs:
                    if src not in rel_defs and src != name:
                        # allow forward only if already created
                        if src not in spine["relations"] and src not in {r.get("name") for r in relations}:
                            raise ValueError(f"derived {name}: unknown input {src}")
                if len(inputs) > 2:
                    raise ValueError(f"derived {name}: only binary joins in v1")
                left_rows = [dict(r) for r in db.execute(f'SELECT * FROM "{inputs[0]}"')]
                right_rows = [dict(r) for r in db.execute(f'SELECT * FROM "{inputs[1]}"')]
                if len(left_rows) * len(right_rows) > 2_000_000:
                    raise ValueError(
                        f"derived {name}: join {inputs[0]}×{inputs[1]} "
                        f"({len(left_rows)}×{len(right_rows)}) exceeds v1 bound"
                    )
                joined = []
                n_unbound_join = 0
                for lrow in left_rows:
                    for rrow in right_rows:
                        if not _match_ok(lrow, rrow, match, inputs[0], inputs[1]):
                            continue
                        if not _where_ok(lrow, rrow, where, inputs[0], inputs[1]):
                            continue
                        combined = _project_derived(item, lrow, rrow, inputs[0], inputs[1])
                        if any(
                            r.get("type") == "REFERENT" and combined.get(r["name"]) in (None, "")
                            for r in roles
                        ):
                            n_unbound_join += 1
                        joined.append(combined)
                role_names = ",".join(f'"{r["name"]}"' for r in roles)
                placeholders = ",".join("?" for _ in roles)
                for row in joined:
                    db.execute(
                        f'INSERT INTO "{name}" ({role_names}) VALUES ({placeholders})',
                        [row.get(r["name"], "") for r in roles],
                    )
                spine["relations"][name] = {
                    "kind": "derived",
                    "rows": len(joined),
                    "inputs": inputs,
                    "unbound": n_unbound_join,
                }
                if (left_rows and right_rows) and not joined:
                    triggers.append(
                        _trig(
                            "NO_MATERIALIZABLE_PATH",
                            requirement_id=None,
                            relation=name,
                            subject={"inputs": inputs},
                            expected="join produces rows when both inputs are nonempty",
                            observed=f"left={len(left_rows)} right={len(right_rows)} joined=0",
                        )
                    )
                if n_unbound_join:
                    triggers.append(
                        _trig(
                            "UNBOUND_CORRESPONDENCE",
                            requirement_id=None,
                            relation=name,
                            subject={"unbound_rows": n_unbound_join},
                            expected="derived roles populated",
                            observed=f"{n_unbound_join}/{len(joined)} derived rows unbound",
                        )
                    )

        for req in requirements:
            rid = _ident(str(req.get("id") or ""), kind="requirement")
            over = str(req.get("over") or "")
            if over not in rel_defs:
                raise ValueError(f"requirement {rid}: unknown relation {over}")
            purpose = req.get("purpose") or []
            group_by = list(req.get("group_by") or [])
            card = str(req.get("cardinality") or "")
            if card and card not in CARDINALITIES:
                raise ValueError(f"requirement {rid}: bad cardinality")
            role_names = [str(r.get("name")) for r in rel_defs[over].get("roles") or []]
            for g in group_by:
                if g not in role_names:
                    raise ValueError(f"requirement {rid}: group_by {g} not a role of {over}")
            rows = [dict(r) for r in db.execute(f'SELECT * FROM "{over}"')]
            buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
            if group_by:
                for row in rows:
                    key = tuple(str(row.get(g, "")) for g in group_by)
                    buckets[key].append(row)
            else:
                buckets[()] = rows

            if card:
                for key, members in buckets.items():
                    n = len(members)
                    kind = None
                    if card == "ONE" and n == 0:
                        kind = "CARDINALITY_UNDERSATISFIED"
                    elif card == "ONE" and n > 1:
                        kind = "CARDINALITY_OVERSATISFIED"
                    elif card == "ZERO_OR_ONE" and n > 1:
                        kind = "CARDINALITY_OVERSATISFIED"
                    elif card == "AT_LEAST_ONE" and n == 0:
                        kind = "CARDINALITY_UNDERSATISFIED"
                    if kind:
                        failure = kind
                        if kind == "CARDINALITY_OVERSATISFIED":
                            # spec lists MULTIPLE_CANDIDATES as well; emit the cardinality name
                            # and attach alias in observed state.
                            pass
                        triggers.append(
                            _trig(
                                failure,
                                requirement_id=rid,
                                relation=over,
                                purpose=purpose,
                                subject=dict(zip(group_by, key)),
                                expected=f"cardinality {card}",
                                observed={"n_candidates": n, "alias": "MULTIPLE_CANDIDATES" if n > 1 else None},
                                candidates=_preview(members),
                            )
                        )
                        if n > 1:
                            triggers.append(
                                _trig(
                                    "MULTIPLE_CANDIDATES",
                                    requirement_id=rid,
                                    relation=over,
                                    purpose=purpose,
                                    subject=dict(zip(group_by, key)),
                                    expected="unique applicable candidate",
                                    observed={"n_candidates": n},
                                    candidates=_preview(members),
                                )
                            )

            numeric_fields = list(req.get("require_numeric") or [])
            for field in numeric_fields:
                if field not in role_names:
                    raise ValueError(f"requirement {rid}: require_numeric {field} not a role")
            if numeric_fields:
                for key, members in buckets.items():
                    for member in members:
                        missing = []
                        for field in numeric_fields:
                            if not _is_number(member.get(field, "")):
                                missing.append(field)
                        if missing:
                            triggers.append(
                                _trig(
                                    "COMPARISON_OPERATOR_REQUIRED",
                                    requirement_id=rid,
                                    relation=over,
                                    purpose=purpose,
                                    subject=dict(zip(group_by, key)) if group_by else {},
                                    expected=f"numeric {numeric_fields} present for comparison",
                                    observed={"missing": missing, "row": {f: member.get(f, "") for f in numeric_fields}},
                                )
                            )

            code_spec = req.get("require_interpreted_code") or {}
            if code_spec:
                field = str(code_spec.get("field") or "")
                known = {str(x) for x in (code_spec.get("known") or [])}
                if field not in role_names:
                    raise ValueError(f"requirement {rid}: interpreted field {field} not a role")
                for key, members in buckets.items():
                    for member in members:
                        val = str(member.get(field, ""))
                        if val not in known:
                            triggers.append(
                                _trig(
                                    "UNINTERPRETED_REQUIRED_CODE",
                                    requirement_id=rid,
                                    relation=over,
                                    purpose=purpose,
                                    subject=dict(zip(group_by, key)) if group_by else {field: val},
                                    expected=f"{field} in known {sorted(known)[:12]}",
                                    observed={"field": field, "value": val},
                                )
                            )

    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        return _fail(errors)

    groups = _group_triggers(triggers)
    structurally_valid = True
    return {
        "ok": True,
        "structurally_valid": structurally_valid,
        "errors": [],
        "spine": spine,
        "n_trigger_instances": len(triggers),
        "n_trigger_groups": len(groups),
        "trigger_instances": triggers,
        "trigger_groups": groups,
        "relation_row_counts": {k: v.get("rows") for k, v in spine["relations"].items()},
        "referent_counts": spine["referents"],
    }


def _fail(errors: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "structurally_valid": False,
        "errors": errors,
        "spine": {},
        "n_trigger_instances": 0,
        "n_trigger_groups": 0,
        "trigger_instances": [],
        "trigger_groups": [],
        "relation_row_counts": {},
        "referent_counts": {},
    }


def _trig(kind: str, **kwargs: Any) -> dict[str, Any]:
    if kind not in DIAGNOSTICS:
        raise ValueError(kind)
    return {
        "failure_kind": kind,
        "requirement_id": kwargs.get("requirement_id"),
        "relation": kwargs.get("relation"),
        "purpose": kwargs.get("purpose") or [],
        "subject": kwargs.get("subject") or {},
        "expected": kwargs.get("expected"),
        "observed": kwargs.get("observed"),
        "candidates": kwargs.get("candidates") or [],
        "grounding": {
            "relation": kwargs.get("relation"),
            "requirement_id": kwargs.get("requirement_id"),
        },
    }


def _preview(rows: list[dict[str, Any]], n: int = 8) -> list[dict[str, Any]]:
    out = []
    for row in rows[:n]:
        out.append({k: row[k] for k in row.keys() if not str(k).startswith("_rowid")})
    return out


def _split_ref(expr: str) -> tuple[str, str]:
    if "." not in expr:
        raise ValueError(f"expected relation.role, got {expr!r}")
    rel, role = expr.split(".", 1)
    return rel, role


def _match_ok(lrow: dict, rrow: dict, match: list, left_name: str, right_name: str) -> bool:
    for cond in match:
        left_rel, left_role = _split_ref(str(cond.get("left") or ""))
        right_rel, right_role = _split_ref(str(cond.get("right") or ""))
        lval = lrow.get(left_role, "") if left_rel == left_name else rrow.get(left_role, "")
        rval = rrow.get(right_role, "") if right_rel == right_name else lrow.get(right_role, "")
        if str(lval) != str(rval):
            return False
    return True


def _where_ok(lrow: dict, rrow: dict, where: list, left_name: str, right_name: str) -> bool:
    def lookup(expr: str) -> str:
        rel, role = _split_ref(expr)
        if rel == left_name:
            return str(lrow.get(role, "") or "")
        if rel == right_name:
            return str(rrow.get(role, "") or "")
        raise ValueError(f"where ref {expr} not in join inputs")

    for cond in where:
        op = str(cond.get("op") or "")
        if op == "interval_contains":
            point = parse_date(lookup(str(cond.get("point") or "")))
            begin = parse_date(lookup(str(cond.get("begin") or "")))
            end = parse_date(lookup(str(cond.get("end") or "")))
            if point is None or begin is None or end is None:
                return False
            if not (begin <= point <= end):
                return False
        elif op == "eq":
            if lookup(str(cond.get("left") or "")) != lookup(str(cond.get("right") or "")):
                return False
        elif op == "neq":
            if lookup(str(cond.get("left") or "")) == lookup(str(cond.get("right") or "")):
                return False
        elif op == "not_empty":
            if not lookup(str(cond.get("field") or "")).strip():
                return False
        else:
            raise ValueError(f"unknown where.op {op}")
    return True


def _project_derived(item: dict, lrow: dict, rrow: dict, left_name: str, right_name: str) -> dict[str, Any]:
    out = {}
    for role in item.get("roles") or []:
        src = str(role.get("from_role") or "")
        if not src:
            out[role["name"]] = ""
            continue
        rel, rname = _split_ref(src)
        if rel == left_name:
            out[role["name"]] = lrow.get(rname, "")
        elif rel == right_name:
            out[role["name"]] = rrow.get(rname, "")
        else:
            raise ValueError(f"from_role {src} not in join")
    return out


def _is_number(value: Any) -> bool:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def _group_triggers(triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for trig in triggers:
        key = (
            trig.get("requirement_id"),
            trig.get("failure_kind"),
            trig.get("relation"),
        )
        buckets[key].append(trig)
    groups = []
    for i, (key, members) in enumerate(sorted(buckets.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), str(kv[0][2])))):
        groups.append(
            {
                "group_id": f"g{i:03d}",
                "requirement_id": key[0],
                "failure_kind": key[1],
                "relation": key[2],
                "n_instances": len(members),
                "purpose": members[0].get("purpose") if members else [],
                "sample_subjects": [m.get("subject") for m in members[:12]],
                "expected": members[0].get("expected") if members else None,
            }
        )
    return groups


def load_program(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        if not match:
            raise
        payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError("program.json must be a JSON object")
    return payload


def public_diagnostics(result: dict[str, Any]) -> dict[str, Any]:
    """Host-to-agent feedback. No gold. Trigger counts and groups, not expected seams."""

    groups = []
    for group in result.get("trigger_groups") or []:
        groups.append(
            {
                "group_id": group.get("group_id"),
                "requirement_id": group.get("requirement_id"),
                "failure_kind": group.get("failure_kind"),
                "relation": group.get("relation"),
                "n_instances": group.get("n_instances"),
                "purpose": group.get("purpose"),
                "sample_subjects": (group.get("sample_subjects") or [])[:6],
            }
        )
    return {
        "structurally_valid": bool(result.get("structurally_valid")),
        "errors": list(result.get("errors") or []),
        "relation_row_counts": result.get("relation_row_counts") or {},
        "referent_counts": result.get("referent_counts") or {},
        "n_trigger_instances": result.get("n_trigger_instances") or 0,
        "n_trigger_groups": result.get("n_trigger_groups") or 0,
        "trigger_groups": groups,
        "note": (
            "Triggers are compiler diagnostics from your requirements. "
            "They are not gold labels. Revise program.json only if structurally_valid is false."
        ),
    }


def compile_path(program_path: Path, sources_dir: Path) -> dict[str, Any]:
    if not program_path.exists():
        return _fail(["program.json missing"])
    try:
        program = load_program(program_path)
    except Exception as exc:  # noqa: BLE001
        return _fail([f"program.json parse error: {exc}"])
    return compile_program(program, sources_dir)
