"""Mechanical dry-run / commit diffs. Counts are diagnostic, not correctness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_fingerprints(root: Path) -> dict[str, str]:
    sources = root / "sources"
    names = ("dmr_measurements.csv", "permit_limits.csv", "document_inventory.json")
    return {name: sha256_file(sources / name) if (sources / name).exists() else "" for name in names}


def digest_from_run(run_dir: Path) -> dict[str, Any]:
    public = _load(run_dir / "run_public.json") or _load(run_dir / "rerun_public.json") or {}
    spine = _load(run_dir / "spine.json") or {}
    requirements = spine.get("requirements") or []
    relations = spine.get("relations") or {}
    hole_groups = public.get("hole_groups") or spine.get("hole_groups") or []
    req_names = [r.get("name") for r in requirements] if requirements else (public.get("requirement_names") or [])
    return {
        "ok": public.get("ok"),
        "errors": public.get("errors") or [],
        "relation_row_counts": public.get("relation_row_counts") or spine.get("relation_row_counts") or {},
        "n_hole_groups": public.get("n_hole_groups") if public.get("n_hole_groups") is not None else spine.get("n_hole_groups"),
        "n_hole_instances": public.get("n_hole_instances") if public.get("n_hole_instances") is not None else spine.get("n_hole_instances"),
        "requirement_names": req_names,
        "requirements": [
            {
                "name": r.get("name"),
                "kind": r.get("kind"),
                "purpose": r.get("purpose"),
                "cardinality": r.get("cardinality"),
                "relation": r.get("relation") or r.get("candidates"),
                "field": r.get("field"),
                "known": r.get("known"),
            }
            for r in requirements
        ],
        "relation_modes": {name: (spec or {}).get("mode") for name, spec in relations.items()},
        "hole_group_keys": [
            f"{g.get('requirement')}|{g.get('failure_kind')}|{g.get('n_instances')}"
            for g in hole_groups
        ],
        "hole_requirements": sorted({g.get("requirement") for g in hole_groups if g.get("requirement")}),
    }


def _index_reqs(items: list[dict]) -> dict[str, dict]:
    return {str(r.get("name")): r for r in items if r.get("name")}


def delta(baseline: dict[str, Any], proposed: dict[str, Any]) -> dict[str, Any]:
    b_counts = baseline.get("relation_row_counts") or {}
    p_counts = proposed.get("relation_row_counts") or {}
    count_changes = {}
    for key in sorted(set(b_counts) | set(p_counts)):
        if b_counts.get(key) != p_counts.get(key):
            count_changes[key] = {"baseline": b_counts.get(key), "proposed": p_counts.get(key)}
    b_req = set(baseline.get("requirement_names") or [])
    p_req = set(proposed.get("requirement_names") or [])
    b_idx = _index_reqs(baseline.get("requirements") or [])
    p_idx = _index_reqs(proposed.get("requirements") or [])
    changed = []
    for name in sorted(b_req & p_req):
        if b_idx.get(name) != p_idx.get(name):
            changed.append({"name": name, "baseline": b_idx.get(name), "proposed": p_idx.get(name)})
    b_modes = baseline.get("relation_modes") or {}
    p_modes = proposed.get("relation_modes") or {}
    mode_changes = {}
    for name in sorted(set(b_modes) | set(p_modes)):
        if b_modes.get(name) != p_modes.get(name):
            mode_changes[name] = {"baseline": b_modes.get(name), "proposed": p_modes.get(name)}
    world_semantics_changed = bool(mode_changes) or any(
        (b_idx.get(n) or {}).get("purpose") != (p_idx.get(n) or {}).get("purpose") and not (p_idx.get(n) or {}).get("purpose")
        for n in sorted(set(b_idx) | set(p_idx))
    )
    purpose_semantics_changed = any(
        (b_idx.get(n) or {}).get("purpose") != (p_idx.get(n) or {}).get("purpose")
        for n in sorted(set(b_idx) | set(p_idx))
    ) or bool(count_changes)
    return {
        "relation_count_changes": count_changes,
        "requirements_added": sorted(p_req - b_req),
        "requirements_removed": sorted(b_req - p_req),
        "requirements_changed": changed,
        "relation_mode_changes": mode_changes,
        "n_hole_groups": {"baseline": baseline.get("n_hole_groups"), "proposed": proposed.get("n_hole_groups")},
        "n_hole_instances": {"baseline": baseline.get("n_hole_instances"), "proposed": proposed.get("n_hole_instances")},
        "hole_requirements_added": sorted(set(proposed.get("hole_requirements") or []) - set(baseline.get("hole_requirements") or [])),
        "hole_requirements_removed": sorted(set(baseline.get("hole_requirements") or []) - set(proposed.get("hole_requirements") or [])),
        "WORLD_semantics_changed": world_semantics_changed,
        "PURPOSE_semantics_changed": purpose_semantics_changed,
        "ok": {"baseline": baseline.get("ok"), "proposed": proposed.get("ok")},
    }


def deltas_match(a: dict[str, Any], b: dict[str, Any]) -> bool:
    keys = (
        "relation_count_changes",
        "requirements_added",
        "requirements_removed",
        "n_hole_groups",
        "n_hole_instances",
    )
    for key in keys:
        if a.get(key) != b.get(key):
            return False
    a_changed = {(c.get("name"), json.dumps(c.get("proposed"), sort_keys=True, default=str)) for c in a.get("requirements_changed") or []}
    b_changed = {(c.get("name"), json.dumps(c.get("proposed"), sort_keys=True, default=str)) for c in b.get("requirements_changed") or []}
    return a_changed == b_changed
