
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
