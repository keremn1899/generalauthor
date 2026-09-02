"""Freeze the isolated A/B replication manifest.  No inference."""

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
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    ADAPTER,
    DEFAULT_MODEL,
    refuse_expensive_model,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import (
    EXPERIMENT_ID,
    LIVE_ROOT,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.workspaces import (
    ASSETS,
    EXPECTED,
    FROZEN_WORLD,
    ROOT,
    copy_frozen_world_fixture,
    sha256_file,
)
from research.taskview_bom.experiment import FIXTURES, SOURCE_NAMES

N_TRIALS = 10
TASK_IDS = ("analysis_a", "analysis_b")
CONDITIONS = ("raw", "world")
PREDECESSOR = "bom-llm-world-programming-v2"


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


def build_manifest() -> dict:
    refuse_expensive_model(DEFAULT_MODEL, action="freeze")
    world = copy_frozen_world_fixture(force=True)
    return {
        "experiment_id": EXPERIMENT_ID,
        "predecessor": PREDECESSOR,
        "status": "FROZEN_BEFORE_INFERENCE",
        "primary_success_criterion": (
            "PASS iff the saved program executes in a clean condition "
            "environment and canonical JSON matches the frozen expected artifact"
        ),
        "hypotheses": ["H1", "H2", "H3", "H4", "H5"],
        "tasks": list(TASK_IDS),
        "conditions": list(CONDITIONS),
        "n_trials": N_TRIALS,
        "n_runs": N_TRIALS * len(TASK_IDS) * len(CONDITIONS),
        "model": DEFAULT_MODEL,
        "adapter": ADAPTER,
        "agent_mode": "agent (default; write and shell enabled)",
        "sandbox": "disabled (bwrap is the isolation boundary; nested Cursor sandbox cannot start inside bwrap)",
        "isolation": {
            "live_root": str(LIVE_ROOT),
            "method": "bwrap tmpfs over repository, Cursor project dir, and sibling live trials",
            "preflight": "cannot list repo; cannot read expected/human solutions; cannot see sibling trials",
        },
        "open_world": "reads stored TaskView view_id from world.sqlite; does not hardcode view identity",
        "force": True,
        "temperature": "not exposed by cursor-agent CLI",
        "timeout_seconds": TIMEOUT_SECONDS,
        "budget": {
            "timeout_seconds_per_trial": TIMEOUT_SECONDS,
            "identical_for_raw_and_world": True,
            "max_turns": "not exposed by cursor-agent CLI",
            "max_tool_calls": "not exposed; wall-clock timeout is the stop",
        },
        "task_fingerprints": task_fingerprints(),
        "prompt_fingerprints": prompt_fingerprints(),
        "expected_output_fingerprints": expected_fingerprints(),
        "raw_fixture_fingerprint": raw_fixture_fingerprint(),
        "world_fixture_fingerprint": world,
        "world_api_fingerprint": sha256_file(
            ASSETS / "world" / "world_surface.py"
        ),
        "world_api_doc_fingerprint": sha256_file(
            ASSETS / "world" / "WORLD_API.md"
        ),
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
        ],
        "failure_taxonomy": [
            "IDENTITY_RECONCILIATION",
            "SOURCE_PARSING",
            "SOURCE_SCHEMA",
            "CONTEXT_MATCHING",
            "SEMANTIC_ACCEPTANCE",
            "UNKNOWN_AS_FALSE",
            "CONFLICT_INTERPRETATION",
            "RELATION_MISUSE",
            "SQL_OR_PYTHON",
            "OUTPUT_FORMAT",
            "OTHER",
        ],
        "provenance_subtest": "analysis_a support field; scored separately",
        "adjudicated_false_representable": False,
        "task_c": "deferred until A/B isolation-held signal is measured",
        "provider_inference_calls_at_freeze": 0,
        "frozen_world_dir": str(FROZEN_WORLD),
    }


def freeze() -> Path:
    path = ROOT / "experiment_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        raise RuntimeError(
            "refusing to overwrite an existing campaign manifest at "
            f"{path} (experiment_id={existing.get('experiment_id')!r}). "
            "Start a new campaign directory instead."
        )
    manifest = build_manifest()
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    manifest["fingerprint"] = digest
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    path.with_name("experiment_manifest.json.sha256").write_text(
        digest + "\n", encoding="utf-8"
    )
    return path


if __name__ == "__main__":
    path = freeze()
    print(path.read_text(encoding="utf-8"))
