"""Freeze hashes before any constructor model call."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
MANIFESTS = NPDES / "fixture" / "manifests"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


SKIP_PARTS = {"__pycache__", "trials", "reports"}
SKIP_NAMES = {"campaign.json", "ABORTED.json", "resume.out", "resume.pid"}


def sha256_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in SKIP_PARTS for part in path.parts) or path.suffix == ".pyc" or path.name in SKIP_NAMES:
            continue
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(bytes.fromhex(sha256_file(path)))
    return h.hexdigest()


def main() -> None:
    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "note": "Frozen before constructor inference. No tuning after this point.",
        "hashes": {
            "participant_sources": sha256_tree(NPDES / "fixture" / "participant_sources"),
            "evaluator_only": sha256_tree(NPDES / "fixture" / "evaluator_only"),
            "column_keep_remove": sha256_file(MANIFESTS / "column_keep_remove.json"),
            "facility_selection": sha256_file(MANIFESTS / "facility_selection.json"),
            "suitability": sha256_file(MANIFESTS / "suitability.json"),
            "source_manifest": sha256_file(
                NPDES / "fixture" / "participant_sources" / "sources" / "source_manifest.json"
            ),
            "purpose_a": sha256_file(NPDES / "fixture" / "participant_sources" / "purposes" / "visible_a.md"),
            "purpose_b": sha256_file(NPDES / "fixture" / "participant_sources" / "purposes" / "visible_b.md"),
            "purpose_c": sha256_file(NPDES / "fixture" / "participant_sources" / "purposes" / "visible_c.md"),
            "purpose_d_evaluator_only": sha256_file(NPDES / "fixture" / "evaluator_only" / "purpose_d.md"),
            "gold_m": sha256_file(NPDES / "fixture" / "evaluator_only" / "gold_m.json"),
            "gold_s": sha256_file(NPDES / "fixture" / "evaluator_only" / "gold_s.json"),
            "gold_e": sha256_file(NPDES / "fixture" / "evaluator_only" / "gold_e.json"),
            "constructor_v3_1_1_runtime": sha256_tree(
                REPO / "research" / "semantic_integration" / "domains" / "diligence" / "constructor_v3_1_1"
            ),
            "npdes_campaign_prompts": sha256_file(ROOT / "prompts.py"),
            "npdes_campaign": sha256_tree(ROOT),
            "kernel_assets": sha256_file(NPDES / "kernel_assets" / "KERNEL.md"),
            "taskview": sha256_tree(REPO / "taskview"),
        },
        "model": {
            "requested": "composer-2.5",
            "adapter": "cursor-agent-bwrap-isolated-constructor-v3-1-1-npdes",
        },
        "scope": {
            "domain": "EPA NPDES individual permit compliance",
            "jurisdiction": "New Mexico",
            "period": "Federal FY2025 2024-10-01 through 2025-09-30 inclusive",
            "facilities": ["NM0020583", "NM0028762", "NM0000116"],
            "substitution": False,
        },
    }
    dest = MANIFESTS / "manifest.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
