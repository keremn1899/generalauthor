"""Constructor workspace: sources, visible purposes, kernel. No hidden artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCES = ROOT / "domain" / "sources"
PURPOSES = ROOT / "domain" / "purposes"
KERNEL = ROOT / "kernel_assets" / "KERNEL.md"
TASKVIEW_SRC = REPO / "taskview"
CONSTRUCTOR_OUT = ROOT / "constructor_run"


README = """# Diligence data room (constructor)

You are the constructor participant. Compile a semantic World for purposes A, B, and C.

You have sources, three visible purposes, and a frozen World kernel. You do not have a gold ontology, expected outputs, or any other purpose.

Read KERNEL.md and the purpose files before writing code.

Required layout in this workspace:

```text
construction/compilation_spec.md
construction/vocabulary.json
construction/mechanical_compiler/   (your C0/C1 code)
construction/semantic_frontier/
construction/evidence_selector/
construction/derivations/
world/world.sqlite
world/obligations.json
purpose_ir/a/output.json
purpose_ir/b/output.json
purpose_ir/c/output.json
reports/construction_notes.md
```

`vocabulary.json` must list every relation with: name, ordered roles, role types, one-sentence semantics, admission WORLD|PURPOSE, construction class MECHANICAL|SEMANTIC|DERIVED, required_by, grounding contract, construction rule, and if SEMANTIC the unresolved judgment plus allowed dispositions.

Run Python with PYTHONPATH=. so `import taskview` works.
"""

TASK = """Compile a purpose-driven semantic World for this data room.

Follow KERNEL.md. Do not add a semantic primitive. Do not read files outside this workspace.

Visible purposes are in purposes/visible_a.md, visible_b.md, visible_c.md.

Begin from the purposes. Discover the smallest useful vocabulary. Classify each relation WORLD or PURPOSE. Mechanically compile everything deterministic. Generate a bounded semantic frontier for remaining judgments. Resolve with grounded ACCEPT/REJECT/UNRESOLVED. Derive purpose outputs with ordinary Python/SQL.

Write purpose_ir/a/output.json, purpose_ir/b/output.json, and purpose_ir/c/output.json exactly in the schemas those files specify.

Save the compiled TaskView as world/world.sqlite.

Do not invent closed-world false. Do not force universal identity. Do not reread sources from purpose programs if World already holds the compiled state; purpose JSON may be written by a derivation over World.
"""


def build_constructor_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copytree(SOURCES, destination / "sources")
    purposes = destination / "purposes"
    purposes.mkdir()
    for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
        shutil.copy2(PURPOSES / name, purposes / name)
    shutil.copy2(KERNEL, destination / "KERNEL.md")
    dest_tv = destination / "taskview"
    dest_tv.mkdir()
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        shutil.copy2(TASKVIEW_SRC / name, dest_tv / name)
    (destination / "README.md").write_text(README, encoding="utf-8")
    (destination / "CONSTRUCTION_TASK.md").write_text(TASK, encoding="utf-8")
    for name in (
        "construction",
        "construction/mechanical_compiler",
        "construction/semantic_frontier",
        "construction/evidence_selector",
        "construction/derivations",
        "world",
        "purpose_ir/a",
        "purpose_ir/b",
        "purpose_ir/c",
        "reports",
    ):
        (destination / name).mkdir(parents=True, exist_ok=True)
