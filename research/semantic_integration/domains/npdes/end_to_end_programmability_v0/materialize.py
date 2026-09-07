"""Compile disposable World copies to sqlite. Construction uses sources; consumers do not."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.compose import (
    write_state_c_construction,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    PARTICIPANT,
    PFPS,
    STATES,
    T5_CONSTRUCTION,
    T5_RUNNER,
    T5_SOURCE,
    T5_WORLD_API,
    WD_CONSTRUCTION,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import (
    document_inventory,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seed_compile_workspace(dest: Path, construction: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    sources = dest / "sources"
    sources.mkdir()
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "dmr_measurements.csv", sources / "dmr_measurements.csv")
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "permit_limits.csv", sources / "permit_limits.csv")
    (sources / "document_inventory.json").write_text(
        json.dumps(document_inventory(), indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(T5_SOURCE, dest / "source.py")
    shutil.copy2(T5_WORLD_API, dest / "world_api.py")
    shutil.copy2(T5_RUNNER, dest / "_run_construction.py")
    shutil.copy2(construction, dest / "construction.py")


def run_construction(workspace: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(workspace / "_run_construction.py")],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads((completed.stdout or "").strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError, ValueError):
        payload = {"ok": False, "errors": [completed.stdout[-2000:], completed.stderr[-2000:]]}
    payload["returncode"] = completed.returncode
    payload["stderr_tail"] = (completed.stderr or "")[-2000:]
    if completed.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(f"construction failed in {workspace}: {payload}")
    return payload


def _sql_type(role_type: str) -> str:
    return {"INTEGER": "INTEGER", "BOOLEAN": "INTEGER", "REAL": "REAL"}.get(role_type, "TEXT")


def _cell(value: Any, role_type: str) -> Any:
    if role_type == "BOOLEAN":
        if value in (True, 1, "1", "true", "True"):
            return 1
        if value in (False, 0, "0", "false", "False", "", None):
            return 0
        return 1 if value else 0
    if role_type == "INTEGER":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if role_type == "REAL":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def dump_world_sqlite(workspace: Path, sqlite_path: Path) -> dict[str, Any]:
    import os

    prev_cwd = Path.cwd()
    sys.path.insert(0, str(workspace))
    os.chdir(workspace)
    try:
        import world_api  # type: ignore
        from source import Source  # type: ignore
        from world_api import Purpose, World  # type: ignore

        world_api.reset()
        ns: dict[str, Any] = {
            "__name__": "construction",
            "Source": Source,
            "World": World,
            "Purpose": Purpose,
            "source": Source("sources"),
        }
        code = (workspace / "construction.py").read_text(encoding="utf-8")
        exec(compile(code, "construction.py", "exec"), ns, ns)
        worlds = world_api.instances()
        if not worlds:
            world = World()
            purpose = Purpose(world)
            ns["construct"](ns["source"], world, purpose)
            worlds = world_api.instances()
        world = worlds[-1]
    finally:
        os.chdir(prev_cwd)
        if sys.path and sys.path[0] == str(workspace):
            sys.path.pop(0)
        for mod in ("world_api", "source"):
            sys.modules.pop(mod, None)

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute(
            "CREATE TABLE _relation_meta (name TEXT PRIMARY KEY, mode TEXT, derived INTEGER, description TEXT, roles_json TEXT, inputs_json TEXT, grounding_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE _referent (id TEXT PRIMARY KEY, kind TEXT, key_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE _requirement (name TEXT, kind TEXT, relation TEXT, field TEXT, known_json TEXT, purpose_json TEXT, spec_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE _hole (requirement TEXT, failure_kind TEXT, relation TEXT, purpose_json TEXT, subject_json TEXT, expected TEXT, observed_json TEXT, grounding_json TEXT)"
        )
        for rid, spec in world.referents.items():
            conn.execute(
                "INSERT INTO _referent(id, kind, key_json) VALUES (?,?,?)",
                (rid, spec.get("kind"), json.dumps(spec.get("key") or {}, sort_keys=True, default=str)),
            )
        for req in world.requirements:
            conn.execute(
                "INSERT INTO _requirement(name, kind, relation, field, known_json, purpose_json, spec_json) VALUES (?,?,?,?,?,?,?)",
                (
                    req.get("name"),
                    req.get("kind"),
                    req.get("relation"),
                    req.get("field"),
                    json.dumps(req.get("known") or [], default=str),
                    json.dumps(req.get("purpose") or [], default=str),
                    json.dumps(req, default=str),
                ),
            )
        for hole in world.holes:
            conn.execute(
                "INSERT INTO _hole(requirement, failure_kind, relation, purpose_json, subject_json, expected, observed_json, grounding_json) VALUES (?,?,?,?,?,?,?,?)",
                (
                    hole.get("requirement"),
                    hole.get("failure_kind"),
                    hole.get("relation"),
                    json.dumps(hole.get("purpose") or [], default=str),
                    json.dumps(hole.get("subject") or {}, sort_keys=True, default=str),
                    str(hole.get("expected") or ""),
                    json.dumps(hole.get("observed") or {}, default=str),
                    json.dumps(hole.get("grounding") or {}, default=str),
                ),
            )
        counts: dict[str, int] = {}
        for name, spec in world.relations.items():
            roles = spec.get("roles") or []
            cols = []
            for role in roles:
                cols.append(f'"{role["name"]}" {_sql_type(role["type"])}')
            conn.execute(f'CREATE TABLE "{name}" ({", ".join(cols)})')
            role_names = [r["name"] for r in roles]
            role_types = {r["name"]: r["type"] for r in roles}
            rows = spec.get("rows") or []
            placeholders = ",".join("?" for _ in role_names)
            quoted = ",".join(f'"{n}"' for n in role_names)
            for row in rows:
                conn.execute(
                    f'INSERT INTO "{name}" ({quoted}) VALUES ({placeholders})',
                    [_cell(row.get(n), role_types[n]) for n in role_names],
                )
            counts[name] = len(rows)
            conn.execute(
                "INSERT INTO _relation_meta(name, mode, derived, description, roles_json, inputs_json, grounding_json) VALUES (?,?,?,?,?,?,?)",
                (
                    name,
                    spec.get("mode"),
                    1 if spec.get("derived") else 0,
                    spec.get("description") or "",
                    json.dumps(roles),
                    json.dumps(spec.get("inputs") or []),
                    json.dumps(spec.get("grounding") or [], default=str),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    snap = world.snapshot()
    return {
        "n_referents": snap.get("n_referents"),
        "n_hole_instances": snap.get("n_hole_instances"),
        "n_hole_groups": snap.get("n_hole_groups"),
        "relation_row_counts": counts,
        "requirement_names": [r.get("name") for r in world.requirements],
        "hole_requirements": sorted({h.get("requirement") for h in world.holes}),
        "ok": True,
    }


def write_sidecars(state_dir: Path, meta: dict[str, Any], *, admission: dict[str, str], origins: dict) -> None:
    accepted = state_dir / "accepted"
    accepted.mkdir(parents=True, exist_ok=True)
    purposes = {
        "A": (PARTICIPANT / "purposes" / "visible_a.md").read_text(encoding="utf-8"),
        "B": (PARTICIPANT / "purposes" / "visible_b.md").read_text(encoding="utf-8"),
        "C": (PARTICIPANT / "purposes" / "visible_c.md").read_text(encoding="utf-8"),
    }
    (accepted / "world.sqlite.origins.json").write_text(json.dumps(origins, indent=2) + "\n", encoding="utf-8")
    (accepted / "world.admission.json").write_text(json.dumps(admission, indent=2) + "\n", encoding="utf-8")
    (accepted / "world.purpose.json").write_text(json.dumps(purposes, indent=2) + "\n", encoding="utf-8")
    (state_dir / "compile_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _admission_from_sqlite(db: Path) -> dict[str, str]:
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT name, mode FROM _relation_meta ORDER BY name").fetchall()
    finally:
        conn.close()
    return {name: mode for name, mode in rows}


def _origins_from_sqlite(db: Path, construction_hash: str, proposal_ids: list[str]) -> dict:
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT name, mode, derived, grounding_json FROM _relation_meta ORDER BY name"
        ).fetchall()
    finally:
        conn.close()
    return {
        "construction_sha256": construction_hash,
        "proposals": proposal_ids,
        "relations": [
            {
                "name": name,
                "mode": mode,
                "derived": bool(derived),
                "grounding": json.loads(grounding or "[]"),
            }
            for name, mode, derived, grounding in rows
        ],
    }


def materialize_state(state_id: str, construction_src: Path, *, proposal_ids: list[str]) -> dict[str, Any]:
    state_dir = STATES / state_id
    compile_dir = state_dir / "compile"
    seed_compile_workspace(compile_dir, construction_src)
    run_construction(compile_dir)
    accepted = state_dir / "accepted"
    accepted.mkdir(parents=True, exist_ok=True)
    sqlite_path = accepted / "world.sqlite"
    dump_meta = dump_world_sqlite(compile_dir, sqlite_path)
    construction_hash = sha256_file(compile_dir / "construction.py")
    shutil.copy2(compile_dir / "construction.py", state_dir / "construction.py")
    admission = _admission_from_sqlite(sqlite_path)
    origins = _origins_from_sqlite(sqlite_path, construction_hash, proposal_ids)
    meta = {
        "state_id": state_id,
        "construction_src": str(construction_src),
        "construction_sha256": construction_hash,
        "world_sha256": sha256_file(sqlite_path),
        "proposal_ids": proposal_ids,
        **dump_meta,
    }
    write_sidecars(state_dir, meta, admission=admission, origins=origins)
    return meta


def materialize_all() -> dict[str, Any]:
    STATES.mkdir(parents=True, exist_ok=True)
    state_c_src = STATES / "state_c" / "construction.py"
    write_state_c_construction(state_c_src)
    results = {
        "state_a": materialize_state("state_a", T5_CONSTRUCTION, proposal_ids=[]),
        "state_b": materialize_state(
            "state_b",
            WD_CONSTRUCTION,
            proposal_ids=["obligation_v1/T1/when_discharging"],
        ),
        "state_c": materialize_state(
            "state_c",
            state_c_src,
            proposal_ids=[
                "obligation_v1/T1/when_discharging",
                "obligation_v1/T3/pass_fail",
            ],
        ),
    }
    return results
