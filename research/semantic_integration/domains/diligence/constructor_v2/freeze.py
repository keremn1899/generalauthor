"""Freeze constructor v2 apparatus. Do not overwrite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.axis_a_apparatus import (
    write_apparatus,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.contracts import (
    contract_to_dict,
    IDENTITY_CONTRACT,
)
from research.semantic_integration.domains.diligence.freeze_apparatus import (
    HIDDEN,
    KERNEL,
    PURPOSES,
    SOURCES,
    sha256_file,
    source_files,
)

ROOT = Path(__file__).resolve().parent


def freeze() -> Path:
    path = ROOT / "experiment_manifest.json"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite frozen manifest {path}")
    write_apparatus()
    manifest = {
        "experiment_id": "diligence-constructor-v2-repair",
        "model": "composer-2.5",
        "model_fast_forbidden": "composer-2.5-fast",
        "repairs": ["R1", "R2", "R3", "R4"],
        "kernel_changes": False,
        "semantic_family_behavior": False,
        "fixture": "diligence repair fixture",
        "axis_a_trials": 10,
        "axis_d_trials": 5,
        "identity_contract": contract_to_dict(IDENTITY_CONTRACT),
        "axis_a_packet_fingerprints": {
            p.name: sha256_file(p) for p in sorted((ROOT / "axis_a_apparatus" / "packets").glob("*.json"))
        },
        "axis_a_obligations": sha256_file(ROOT / "axis_a_apparatus" / "obligations.json"),
        "source_fingerprints": {
            str(p.relative_to(SOURCES)): sha256_file(p) for p in source_files()
        },
        "purpose_fingerprints": {
            p.name: sha256_file(p) for p in sorted(PURPOSES.glob("visible_*.md"))
        },
        "hidden_fingerprints": {
            str(p.relative_to(HIDDEN)): sha256_file(p)
            for p in sorted(HIDDEN.rglob("*"))
            if p.is_file()
        },
        "kernel_fingerprint": sha256_file(KERNEL),
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    manifest["fingerprint"] = digest
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    path.with_suffix(".json.sha256").write_text(digest + "\n")
    return path


if __name__ == "__main__":
    print(freeze())
