"""Freeze the Composer 2.5 model-substitution manifest.  No inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.bom.llm_world_programming.prompts import (
    TASKS,
    participant_prompt,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.agent import (
    ADAPTER,
    MODEL,
    MODEL_FAST_FORBIDDEN,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.isolation import (
    EXPERIMENT_ID,
    LIVE_ROOT,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.workspaces import (
    ASSETS,
    EXPECTED,
    FROZEN_WORLD,
    ROOT,
    V3,
    copy_frozen_world_fixture,
    sha256_file,
)
from research.taskview_bom.experiment import FIXTURES, SOURCE_NAMES

N_TRIALS = 5
TASK_IDS = ("analysis_a", "analysis_b")
CONDITIONS = ("raw", "world")
PREDECESSOR = "bom-llm-world-programming-v3"
V3_FINGERPRINT = "sha256:b88da582b1f1a4477c47d444caf5f12945649501f340e4e6ae70906e0e1404f4"


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def raw_fixture_fingerprint() -> dict[str, str]:
    return {name: sha256_file(FIXTURES / name) for name in SOURCE_NAMES}


def expected_fingerprints() -> dict[str, str]:
    return {name: sha256_file(EXPECTED / f"{name}.json") for name in TASK_IDS}


def task_fingerprints() -> dict[str, str]:
    return {task_id: _sha256_text(TASKS[task_id]) for task_id in TASK_IDS}


def prompt_fingerprints() -> dict[str, str]:
    return {
        f"{condition}:{task_id}": _sha256_text(participant_prompt(condition, task_id))
        for condition in CONDITIONS
        for task_id in TASK_IDS
    }


def v3_manifest() -> dict:
    path = V3 / "experiment_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest() -> dict:
    if MODEL != "composer-2.5" or "fast" in MODEL:
        raise RuntimeError(f"refusing to freeze model {MODEL!r}")
    predecessor = v3_manifest()
    if predecessor.get("fingerprint") != V3_FINGERPRINT:
        raise RuntimeError("v3 predecessor fingerprint drifted")
    world = copy_frozen_world_fixture(force=True)
    if world != predecessor["world_fixture_fingerprint"]:
        raise RuntimeError("copied world fixture does not match frozen v3 bytes")
    prompts = prompt_fingerprints()
    if prompts != predecessor["prompt_fingerprints"]:
        raise RuntimeError("prompt fingerprints drifted from frozen v3")
    expected = expected_fingerprints()
    if expected != predecessor["expected_output_fingerprints"]:
        raise RuntimeError("expected-output fingerprints drifted from frozen v3")
    tasks = task_fingerprints()
    if tasks != predecessor["task_fingerprints"]:
        raise RuntimeError("task fingerprints drifted from frozen v3")
    raw = raw_fixture_fingerprint()
    if raw != predecessor["raw_fixture_fingerprint"]:
        raise RuntimeError("RAW fixture fingerprints drifted from frozen v3")
    api = sha256_file(ASSETS / "world" / "world_surface.py")
    if api != predecessor["world_api_fingerprint"]:
        raise RuntimeError("world_surface.py drifted from frozen v3")
    api_doc = sha256_file(ASSETS / "world" / "WORLD_API.md")
    if api_doc != predecessor["world_api_doc_fingerprint"]:
        raise RuntimeError("WORLD_API.md drifted from frozen v3")
    return {
        "experiment_id": EXPERIMENT_ID,
        "predecessor": PREDECESSOR,
        "predecessor_fingerprint": V3_FINGERPRINT,
        "status": "FROZEN_BEFORE_INFERENCE",
        "experimental_variable": "model",
        "primary_success_criterion": (
            "PASS iff the saved program executes in a clean condition "
            "environment and canonical JSON matches the frozen expected artifact"
        ),
        "question": (
            "Can composer-2.5 achieve high programming correctness over compiled "
            "World IR while failing or performing materially worse against the "
            "equivalent heterogeneous RAW sources?"
        ),
        "tasks": list(TASK_IDS),
        "conditions": list(CONDITIONS),
        "n_trials": N_TRIALS,
        "n_runs": N_TRIALS * len(TASK_IDS) * len(CONDITIONS),
        "model": MODEL,
        "model_fast_forbidden": MODEL_FAST_FORBIDDEN,
        "adapter": ADAPTER,
        "agent_mode": "agent (default; write and shell enabled)",
        "sandbox": (
            "disabled (bwrap is the isolation boundary; nested Cursor sandbox "
            "cannot start inside bwrap)"
        ),
        "isolation": {
            "live_root": str(LIVE_ROOT),
            "method": (
                "bwrap tmpfs over repository, Cursor project dir, and sibling live trials"
            ),
            "preflight": (
                "cannot list repo; cannot read expected/human solutions; "
                "cannot see sibling trials"
            ),
            "stop_on_leak": True,
        },
        "open_world": (
            "reads stored TaskView view_id from world.sqlite; does not hardcode view identity"
        ),
        "force": True,
        "temperature": "not exposed by cursor-agent CLI",
        "timeout_seconds": TIMEOUT_SECONDS,
        "budget": {
            "timeout_seconds_per_trial": TIMEOUT_SECONDS,
            "identical_for_raw_and_world": True,
            "max_turns": "not exposed by cursor-agent CLI",
            "max_tool_calls": "not exposed; wall-clock timeout is the stop",
        },
        "task_fingerprints": tasks,
        "prompt_fingerprints": prompts,
        "expected_output_fingerprints": expected,
        "raw_fixture_fingerprint": raw,
        "world_fixture_fingerprint": world,
        "world_api_fingerprint": api,
        "world_api_doc_fingerprint": api_doc,
        "metrics": [
            "exact_task_success",
            "semantic_error_class",
            "acquisition_burden",
            "token_usage_if_exposed",
            "attempts_proxy_from_tool_calls",
            "program_burden",
            "provenance_support_present",
            "unknown_as_false",
            "isolation_preflight",
            "cursor_usage_fields_if_exposed",
            "monetary_cost_if_exposed",
        ],
        "cost_metrics": {
            "prefer": [
                "total campaign cost",
                "cost by condition",
                "cost per successful run",
            ],
            "policy": (
                "Record the best available Cursor usage fields. "
                "Do not fabricate monetary cost from incomplete token fields."
            ),
        },
        "failure_taxonomy": list(predecessor["failure_taxonomy"]),
        "provenance_subtest": "analysis_a support field; scored separately",
        "adjudicated_false_representable": False,
        "task_c": "not in this campaign",
        "provider_inference_calls_at_freeze": 0,
        "frozen_world_dir": str(FROZEN_WORLD),
        "historical_context_only": {
            "experiment_id": PREDECESSOR,
            "model": predecessor["model"],
            "raw_pass": "0/20",
            "world_pass": "18/20",
            "not_pooled": True,
        },
    }


def freeze() -> Path:
    path = ROOT / "manifest.json"
    sidecar = ROOT / "manifest.json.sha256"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        raise RuntimeError(
            "refusing to overwrite an existing campaign manifest at "
            f"{path} (experiment_id={existing.get('experiment_id')!r})."
        )
    manifest = build_manifest()
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    manifest["fingerprint"] = digest
    encoded_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    path.write_text(encoded_text, encoding="utf-8")
    sidecar.write_text(digest + "\n", encoding="utf-8")
    (ROOT / "experiment_manifest.json").write_text(encoded_text, encoding="utf-8")
    (ROOT / "experiment_manifest.json.sha256").write_text(digest + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    path = freeze()
    print(path.read_text(encoding="utf-8"))
