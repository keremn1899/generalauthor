"""Independent scorer.  Expected outputs never enter the model workspace."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.workspaces import (
    EXPECTED,
    build_raw_workspace,
    build_world_workspace,
)

CORE_KEYS = {"support"}


def load_expected(task_id: str) -> dict[str, Any]:
    return json.loads((EXPECTED / f"{task_id}.json").read_text(encoding="utf-8"))


def strip_support(document: Any) -> Any:
    if isinstance(document, dict):
        return {
            key: strip_support(value)
            for key, value in document.items()
            if key not in CORE_KEYS
        }
    if isinstance(document, list):
        return [strip_support(item) for item in document]
    return document


def indoor_case(document: dict[str, Any]) -> dict[str, Any] | None:
    for case in document.get("cases", []):
        if "indoor" in str(case.get("context", "")):
            return case
    return None


def classify_failure(
    *,
    task_id: str,
    expected: dict[str, Any],
    actual: dict[str, Any] | None,
    executes: bool,
    parses: bool,
    schema_valid: bool,
    exact: bool,
) -> str | None:
    if exact:
        return None
    if not executes:
        return "SQL_OR_PYTHON"
    if not parses:
        return "OUTPUT_FORMAT"
    if not schema_valid:
        return "OUTPUT_FORMAT"
    if actual is None:
        return "OUTPUT_FORMAT"
    indoor = indoor_case(actual)
    if indoor is not None:
        semantic = str(indoor.get("semantic_state", "")).lower()
        epistemic = str(indoor.get("epistemic", "")).lower()
        if any(
            token in semantic or token in epistemic
            for token in ("false", "rejected", "ineligible", "denied")
        ):
            return "UNKNOWN_AS_FALSE"
        if task_id == "analysis_b" and "semantic_acceptance" in indoor.get(
            "prevents_viability", []
        ):
            return "UNKNOWN_AS_FALSE"
        if indoor.get("semantic_state") not in {None, "unresolved"} and expected:
            exp_indoor = indoor_case(expected)
            if exp_indoor and indoor.get("semantic_state") != exp_indoor.get(
                "semantic_state"
            ):
                return "SEMANTIC_ACCEPTANCE"
    text = json.dumps(actual, sort_keys=True)
    if task_id == "analysis_c":
        if "X100" not in text and "part:X100" not in text:
            return "CONFLICT_INTERPRETATION"
        if "28" not in text or "24" not in text:
            return "CONFLICT_INTERPRETATION"
    if "part:" not in text and "bom:" not in text:
        return "IDENTITY_RECONCILIATION"
    if task_id in {"analysis_a", "analysis_b"} and "indoor" not in text:
        return "CONTEXT_MATCHING"
    return "OTHER"


def schema_valid(task_id: str, document: dict[str, Any]) -> bool:
    if task_id == "analysis_a":
        return document.get("task") == "replacement_state" and isinstance(
            document.get("cases"), list
        )
    if task_id == "analysis_b":
        return document.get("task") == "qualification_bottlenecks" and isinstance(
            document.get("cases"), list
        )
    if task_id == "analysis_c":
        return document.get("task") == "spec_conflict_review" and isinstance(
            document.get("conflicts"), list
        )
    return False


def run_saved_program(
    *,
    condition: str,
    program: Path,
    clean_root: Path,
) -> dict[str, Any]:
    if condition == "raw":
        build_raw_workspace(clean_root)
    else:
        build_world_workspace(clean_root)
    target = clean_root / "analysis.py"
    target.write_text(program.read_text(encoding="utf-8"), encoding="utf-8")
    env_python = ["python3"]
    if condition == "world":
        command = env_python + ["analysis.py"]
        extra_env = {"PYTHONPATH": str(clean_root)}
    else:
        command = env_python + ["analysis.py"]
        extra_env = {}
    import os

    env = os.environ.copy()
    env.update(extra_env)
    try:
        completed = subprocess.run(
            command,
            cwd=clean_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "executes": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "TIMEOUT",
        }
    output_path = clean_root / "output.json"
    parsed = None
    parses = False
    if output_path.exists():
        try:
            parsed = json.loads(output_path.read_text(encoding="utf-8"))
            parses = True
        except json.JSONDecodeError:
            parsed = None
    if parsed is None and completed.stdout.strip():
        try:
            parsed = json.loads(completed.stdout.strip())
            parses = True
        except json.JSONDecodeError:
            start = completed.stdout.find("{")
            end = completed.stdout.rfind("}")
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(completed.stdout[start : end + 1])
                    parses = True
                except json.JSONDecodeError:
                    parsed = None
    return {
        "executes": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "parses": parses,
        "output": parsed,
    }


def score_run(
    *,
    condition: str,
    task_id: str,
    trial_dir: Path,
    clean_root: Path,
) -> dict[str, Any]:
    expected = load_expected(task_id)
    program = trial_dir / "analysis.py"
    if not program.exists():
        for candidate in trial_dir.glob("*.py"):
            if candidate.name in {"world_surface.py"} or "taskview" in candidate.parts:
                continue
            if candidate.name == "analysis.py" or candidate.name.startswith("final"):
                program = candidate
                break
        else:
            program = trial_dir / "analysis.py"
    result = {
        "program_exists": program.exists(),
        "program_path": str(program) if program.exists() else None,
        "executes": False,
        "parses": False,
        "schema_valid": False,
        "exact": False,
        "pass": False,
        "failure_class": "SQL_OR_PYTHON",
        "support_present": False,
        "unknown_as_false": False,
        "indoor": None,
    }
    if not program.exists():
        return result
    executed = run_saved_program(
        condition=condition, program=program, clean_root=clean_root
    )
    result.update(
        {
            "executes": executed["executes"],
            "parses": executed["parses"],
            "run_stderr": executed.get("stderr"),
        }
    )
    actual = executed.get("output")
    if isinstance(actual, dict):
        result["support_present"] = "support" in actual
        core = strip_support(actual)
        result["schema_valid"] = schema_valid(task_id, core)
        result["exact"] = core == expected
        result["indoor"] = indoor_case(core)
        indoor = result["indoor"]
        if indoor is not None:
            semantic = str(indoor.get("semantic_state", "")).lower()
            result["unknown_as_false"] = any(
                token in semantic
                or token in str(indoor.get("epistemic", "")).lower()
                for token in ("false", "rejected")
            )
            if task_id == "analysis_b" and "semantic_acceptance" in indoor.get(
                "prevents_viability", []
            ):
                result["unknown_as_false"] = True
    result["failure_class"] = classify_failure(
        task_id=task_id,
        expected=expected,
        actual=strip_support(actual) if isinstance(actual, dict) else None,
        executes=result["executes"],
        parses=result["parses"],
        schema_valid=result["schema_valid"],
        exact=result["exact"],
    )
    result["pass"] = bool(result["exact"] and result["executes"])
    if result["pass"]:
        result["failure_class"] = None
    return result
