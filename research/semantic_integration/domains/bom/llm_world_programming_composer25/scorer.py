"""Independent scorer.  Expected outputs never enter the model workspace."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.scorer import (
    classify_failure,
    indoor_case,
    load_expected,
    schema_valid,
    strip_support,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.workspaces import (
    build_raw_workspace,
    build_world_workspace,
)


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
    extra_env = {"PYTHONPATH": str(clean_root)} if condition == "world" else {}
    env = os.environ.copy()
    env.update(extra_env)
    try:
        completed = subprocess.run(
            ["python3", "analysis.py"],
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
