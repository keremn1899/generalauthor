"""Freeze the research fixture before constructor inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_integration.domains.research.workspaces import README, TASK

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "domain" / "sources"
PURPOSES = ROOT / "domain" / "purposes"
HIDDEN = ROOT / "hidden"
KERNEL = ROOT / "kernel_assets" / "KERNEL.md"
TASKVIEW = ROOT.parents[3] / "taskview"
CONSTRUCTOR_AGENT = ROOT / "constructor_agent.py"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCES.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )


def build_manifest() -> dict:
    sources = {
        str(path.relative_to(SOURCES)): sha256_file(path) for path in source_files()
    }
    purposes = {
        path.name: sha256_file(path) for path in sorted(PURPOSES.glob("visible_*.md"))
    }
    hidden = {
        str(path.relative_to(HIDDEN)): sha256_file(path)
        for path in sorted(HIDDEN.rglob("*"))
        if path.is_file()
    }
    taskview = {
        name: sha256_file(TASKVIEW / name)
        for name in ("__init__.py", "model.py", "store.py", "agent_surface.py")
    }
    return {
        "experiment_id": "research-purpose-driven-construction-v1",
        "label": "PRE_REPAIR_CONSTRUCTOR_BASELINE",
        "status": "FROZEN_BEFORE_CONSTRUCTOR_INFERENCE",
        "domain": "fictional_research_evidence_integration",
        "model": "composer-2.5",
        "model_fast_forbidden": "composer-2.5-fast",
        "constructor_version": "pre-repair-diligence-equivalent-v1",
        "constructor_sees": [
            "domain/sources",
            "domain/purposes/visible_a.md",
            "domain/purposes/visible_b.md",
            "domain/purposes/visible_c.md",
            "kernel_assets/KERNEL.md",
            "taskview sources",
        ],
        "constructor_must_not_see": [
            "hidden/",
            "purpose D",
            "expected outputs",
            "designer annotations",
            "BOM ontology",
            "diligence ontology",
            "prior constructor reports",
        ],
        "visible_purposes": ["A", "B", "C"],
        "held_out_purpose": "D",
        "source_fingerprints": sources,
        "purpose_fingerprints": purposes,
        "hidden_fingerprints": hidden,
        "kernel_fingerprint": sha256_file(KERNEL),
        "constructor_agent_fingerprint": sha256_file(CONSTRUCTOR_AGENT),
        "prompt_fingerprints": {
            "README.md": sha256_text(README),
            "CONSTRUCTION_TASK.md": sha256_text(TASK),
        },
        "taskview_fingerprints": taskview,
        "timeout_seconds": 2400,
        "isolation": "bwrap tmpfs over repository, Cursor projects, sibling trials",
        "provider_inference_calls_at_freeze": 0,
        "new_primitive_allowed": False,
        "raw_vs_world_programming": False,
        "diligence_repairs_forbidden": True,
    }


def freeze() -> Path:
    path = ROOT / "experiment_manifest.json"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite frozen manifest {path}")
    manifest = build_manifest()
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    manifest["fingerprint"] = digest
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    path.with_suffix(".json.sha256").write_text(digest + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    path = freeze()
    print(f"froze {path}")
    print(path.read_text(encoding="utf-8"))
