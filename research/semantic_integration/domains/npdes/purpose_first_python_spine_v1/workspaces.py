"""Participant workspaces. Gold, freeze, and prior probes never enter."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import (
    FROZEN,
    PARTICIPANT,
    ROOT,
    STRUCTURED,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.prompts import PASS_TASK


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def document_inventory() -> list[dict]:
    manifest = json.loads((PARTICIPANT / "sources" / "source_manifest.json").read_text(encoding="utf-8"))
    rows = []
    for item in manifest.get("permit_files") or []:
        path = str(item.get("path") or "")
        filename = Path(path).name
        rows.append(
            {
                "path": path,
                "filename": filename,
                "document_kind": Path(filename).stem,
                "permit": item.get("permit"),
                "bytes": item.get("bytes"),
                "sha256": item.get("sha256"),
                "origin": item.get("origin"),
            }
        )
    return rows


def freeze_input_manifest() -> dict:
    files = {
        "purposes/visible_a.md": PARTICIPANT / "purposes" / "visible_a.md",
        "purposes/visible_b.md": PARTICIPANT / "purposes" / "visible_b.md",
        "purposes/visible_c.md": PARTICIPANT / "purposes" / "visible_c.md",
        "sources/dmr_measurements.csv": STRUCTURED / "dmr_measurements.csv",
        "sources/permit_limits.csv": STRUCTURED / "permit_limits.csv",
        "source.py": ROOT / "source.py",
        "world_api.py": ROOT / "world_api.py",
        "frozen/principles.md": FROZEN / "principles.md",
        "frozen/WORLD_API.md": FROZEN / "WORLD_API.md",
    }
    listed = []
    for rel, path in files.items():
        listed.append({"workspace_path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    inventory = document_inventory()
    listed.append(
        {
            "workspace_path": "sources/document_inventory.json",
            "n_documents": len(inventory),
            "filenames": [row["filename"] for row in inventory],
        }
    )
    return {
        "experiment_id": "npdes-purpose-first-python-spine-v1",
        "participant_visible": True,
        "hidden": [
            "permit/fact-sheet/SOB prose",
            "GOLD M/S/E",
            "Purpose D",
            "triggerability classification",
            "constructor outputs",
            "prose-probe results",
            "spine-compiler-probe-v1 results",
            "KERNEL.md TaskView API",
            "expected ontology / triggers",
        ],
        "files": listed,
        "document_inventory": inventory,
    }


def seed_workspace(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    purposes = dest / "purposes"
    sources = dest / "sources"
    purposes.mkdir()
    sources.mkdir()
    for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
        shutil.copy2(PARTICIPANT / "purposes" / name, purposes / name)
    shutil.copy2(STRUCTURED / "dmr_measurements.csv", sources / "dmr_measurements.csv")
    shutil.copy2(STRUCTURED / "permit_limits.csv", sources / "permit_limits.csv")
    (sources / "document_inventory.json").write_text(
        json.dumps(document_inventory(), indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(ROOT / "source.py", dest / "source.py")
    shutil.copy2(ROOT / "world_api.py", dest / "world_api.py")
    shutil.copy2(FROZEN / "principles.md", dest / "PRINCIPLES.md")
    shutil.copy2(FROZEN / "WORLD_API.md", dest / "WORLD_API.md")
    (dest / "PASS_TASK.md").write_text(PASS_TASK, encoding="utf-8")
    (dest / "README.md").write_text(
        "Isolated purpose-first Python spine probe. Purposes A/B/C and structured sources only. No gold.\n",
        encoding="utf-8",
    )
