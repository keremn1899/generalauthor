"""Freeze pass-localization apparatus. Do not overwrite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_integration.domains.diligence.freeze_apparatus import (
    HIDDEN,
    KERNEL,
    PURPOSES,
    SOURCES,
    source_files,
    sha256_file,
)
from research.semantic_integration.domains.diligence.pass_localization.prompts import (
    FORBIDDEN_PROMPT_TOKENS,
    PASS_ORDER,
    PROMPTS,
)

ROOT = Path(__file__).resolve().parent


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def prompt_fingerprints() -> dict[str, str]:
    return {key: sha256_text(PROMPTS[key]) for key in (*PASS_ORDER, "p7_certified", "d_world_only")}


def build_manifest() -> dict:
    for key, text in PROMPTS.items():
        lowered = text
        for token in FORBIDDEN_PROMPT_TOKENS:
            if token in lowered:
                raise RuntimeError(f"prompt {key} contains forbidden token {token!r}")
    return {
        "experiment_id": "diligence-pass-localization-v1",
        "status": "FROZEN_BEFORE_TRIAL_INFERENCE",
        "model": "composer-2.5",
        "model_fast_forbidden": "composer-2.5-fast",
        "n_trials": 5,
        "passes": list(PASS_ORDER),
        "repairs_during_campaign": False,
        "kernel_changes": False,
        "fixture_reuse": "diligence-purpose-driven-construction-v1 sources/purposes/hidden",
        "source_fingerprints": {
            str(path.relative_to(SOURCES)): sha256_file(path) for path in source_files()
        },
        "purpose_fingerprints": {
            path.name: sha256_file(path) for path in sorted(PURPOSES.glob("visible_*.md"))
        },
        "hidden_fingerprints": {
            str(path.relative_to(HIDDEN)): sha256_file(path)
            for path in sorted(HIDDEN.rglob("*"))
            if path.is_file()
        },
        "kernel_fingerprint": sha256_file(KERNEL),
        "prompt_fingerprints": prompt_fingerprints(),
        "d_world_only_uses": "constructor_run/abc/workspace/world/world.sqlite",
    }


def freeze() -> Path:
    path = ROOT / "experiment_manifest.json"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite frozen manifest {path}")
    manifest = build_manifest()
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    manifest["fingerprint"] = digest
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_suffix(".json.sha256").write_text(digest + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    print(freeze())
