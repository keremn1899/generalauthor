"""Clean deterministic execution of construction.py. Host overwrites world_api/source."""

from __future__ import annotations

import json
import shutil
import traceback
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import host_python
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.isolation import run_isolated
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import (
    ROOT,
    RUNNER_TIMEOUT_SECONDS,
)

DRIVER = r'''
import json
import sys
import traceback
from pathlib import Path

from source import Source
import world_api
from world_api import Purpose, World, dump_snapshot

def main() -> None:
    world_api.reset()
    path = Path("construction.py")
    if not path.exists():
        print(json.dumps({"ok": False, "errors": ["construction.py missing"]}))
        raise SystemExit(1)
    ns = {"Source": Source, "World": World, "Purpose": Purpose, "source": Source("sources")}
    try:
        code = path.read_text(encoding="utf-8")
        exec(compile(code, "construction.py", "exec"), ns, ns)
        if callable(ns.get("construct")):
            world = ns.get("world") if isinstance(ns.get("world"), World) else World()
            purpose = ns.get("purpose") if isinstance(ns.get("purpose"), Purpose) else Purpose(world)
            src = ns.get("source") if isinstance(ns.get("source"), Source) else Source("sources")
            ns["construct"](src, world, purpose)
        worlds = world_api.instances()
        if not worlds:
            print(json.dumps({"ok": False, "errors": ["construction.py did not create a World"]}))
            raise SystemExit(2)
        snap = worlds[-1].snapshot()
        dump_snapshot(snap, Path("."))
        public = {
            "ok": True,
            "errors": [],
            "n_referents": snap.get("n_referents"),
            "referent_kinds": snap.get("referent_kinds"),
            "relation_row_counts": snap.get("relation_row_counts"),
            "relations": snap.get("relations"),
            "n_requirements": len(snap.get("requirements") or []),
            "requirement_names": [r.get("name") for r in (snap.get("requirements") or [])],
            "n_hole_instances": snap.get("n_hole_instances"),
            "n_hole_groups": snap.get("n_hole_groups"),
            "hole_groups": snap.get("hole_groups"),
        }
        Path("run_public.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "n_hole_groups": public["n_hole_groups"]}))
    except Exception as exc:
        err = {"ok": False, "errors": [f"{type(exc).__name__}: {exc}"], "traceback": traceback.format_exc()[-8000:]}
        Path("run_public.json").write_text(json.dumps(err, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(err))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
'''

SEEDED_PY = ("source.py", "world_api.py")


def prepare_clean_run(live: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copytree(live / "sources", dest / "sources")
    shutil.copy2(ROOT / "source.py", dest / "source.py")
    shutil.copy2(ROOT / "world_api.py", dest / "world_api.py")
    if (live / "construction.py").exists():
        shutil.copy2(live / "construction.py", dest / "construction.py")
    for path in live.glob("*.py"):
        if path.name in SEEDED_PY or path.name == "construction.py":
            continue
        if path.name.startswith("_"):
            continue
        shutil.copy2(path, dest / path.name)
    (dest / "_run_construction.py").write_text(DRIVER, encoding="utf-8")


def run_construction(clean: Path) -> dict[str, Any]:
    completed = run_isolated(
        clean,
        [host_python(), "_run_construction.py"],
        timeout=RUNNER_TIMEOUT_SECONDS,
    )
    public_path = clean / "run_public.json"
    if public_path.exists():
        try:
            payload = json.loads(public_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"ok": False, "errors": ["run_public.json parse error"]}
    else:
        payload = {"ok": False, "errors": ["runner produced no run_public.json"]}
    payload["returncode"] = completed.returncode
    payload["stdout_tail"] = (completed.stdout or "")[-4000:]
    payload["stderr_tail"] = (completed.stderr or "")[-4000:]
    if completed.returncode != 0:
        payload["ok"] = False
        payload.setdefault("errors", [])
        if not payload["errors"]:
            payload["errors"] = [f"runner exit {completed.returncode}"]
    return payload


def public_feedback(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return {
            "ok": False,
            "errors": result.get("errors") or [],
            "traceback": (result.get("traceback") or result.get("stderr_tail") or "")[-4000:],
            "note": "Fix construction.py. Do not author trigger instances. Host will re-run from scratch.",
        }
    groups = []
    for group in result.get("hole_groups") or []:
        groups.append(
            {
                "group_id": group.get("group_id"),
                "requirement": group.get("requirement"),
                "failure_kind": group.get("failure_kind"),
                "relation": group.get("relation"),
                "n_instances": group.get("n_instances"),
                "sample_subjects": (group.get("sample_subjects") or [])[:6],
            }
        )
    return {
        "ok": True,
        "errors": [],
        "relation_row_counts": result.get("relation_row_counts") or {},
        "referent_kinds": result.get("referent_kinds") or {},
        "n_hole_instances": result.get("n_hole_instances") or 0,
        "n_hole_groups": result.get("n_hole_groups") or 0,
        "hole_groups": groups,
        "note": "Holes are failed purpose requirements, not gold labels. Revise only if ok is false.",
    }
