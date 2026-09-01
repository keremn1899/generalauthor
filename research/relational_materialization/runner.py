"""Execution and scoring for the pilot.

This module deliberately does not call a model.  It provides a reproducible
agent boundary: an external agent command receives a workspace and writes one
response document.  This keeps model/provider choice, prompts, and pricing
outside the benchmark generator while preserving inspectable artifacts.
"""

from __future__ import annotations

import json
import os
import signal
import sqlite3
import shutil
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .model import Arm


PROTOCOL_VERSION = "relational-materialization-pilot-v3-clean-isolation"

ARM_RULES = {
    Arm.ORDINARY: "Use ordinary workspace tools.",
    Arm.RELATION_STORE: "Use the supplied generic entity/relation SQLite store at relation_store.sqlite.",
    Arm.GRAPHAUTHOR_FORCED: "Construct and use a Graphauthor workbook; write its path in graphauthor_workbook.",
    Arm.GRAPHAUTHOR_OPTIONAL: "Graphauthor is available but optional. Record whether you used it.",
}

ARM_TOOL_POLICIES = {
    Arm.ORDINARY: "Ordinary workspace tools remain unrestricted.",
    Arm.RELATION_STORE: "Use the supplied generic SQLite entity/relation store and ordinary workspace tools.",
    Arm.GRAPHAUTHOR_FORCED: "Graphauthor is supplied and must be used.",
    Arm.GRAPHAUTHOR_OPTIONAL: "Graphauthor is supplied but optional, alongside ordinary tools.",
}

FORBIDDEN_TREATMENT_TERMS = ("graphauthor", ".graphauthor", "graph.lbug", "workbook", "build.py")


@dataclass(frozen=True)
class Score:
    operation_count: int
    exact_operations: int
    answer_precision: float
    answer_recall: float
    materialized: bool
    graphauthor_used: bool

    @property
    def workload_success(self) -> float:
        return self.exact_operations / self.operation_count if self.operation_count else 0.0


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_response(oracle: dict[str, Any], response: dict[str, Any]) -> Score:
    expected = {op["id"]: set(op["answer_ids"]) for op in oracle["operations"]}
    observed = {row.get("operation_id"): set(row.get("answer_ids") or []) for row in response.get("answers") or []}
    true_positive = false_positive = false_negative = exact = 0
    for operation_id, wanted in expected.items():
        got = observed.get(operation_id, set())
        true_positive += len(got & wanted)
        false_positive += len(got - wanted)
        false_negative += len(wanted - got)
        exact += got == wanted
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    artifacts = response.get("artifacts") or {}
    return Score(
        operation_count=len(expected), exact_operations=exact,
        answer_precision=precision, answer_recall=recall,
        materialized=bool(artifacts.get("representation_path")),
        graphauthor_used=bool(artifacts.get("graphauthor_workbook")),
    )


def _artifact_path(declared: object, workspace: Path, run_root: Path) -> Path | None:
    """Resolve a declared artifact only when it remains inside a permitted run root."""
    if not isinstance(declared, str) or not declared:
        return None
    supplied = Path(declared)
    candidates = (supplied,) if supplied.is_absolute() else (workspace / supplied, run_root / supplied)
    for candidate in candidates:
        try:
            candidate.relative_to(workspace)
        except ValueError:
            try:
                candidate.relative_to(run_root)
            except ValueError:
                continue
        if candidate.is_file():
            return candidate
    return None


def _relation_store_is_valid(path: Path) -> bool:
    try:
        with sqlite3.connect(path) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return {"entities", "relations"}.issubset(tables)
    except sqlite3.Error:
        return False


def _prepare_relation_store(workspace: Path) -> None:
    """Supply the thin generic baseline before timing begins."""
    with sqlite3.connect(workspace / "relation_store.sqlite") as connection:
        connection.execute("CREATE TABLE entities (id TEXT PRIMARY KEY, kind TEXT, payload TEXT, provenance TEXT)")
        connection.execute("CREATE TABLE relations (source TEXT, predicate TEXT, target TEXT, provenance TEXT)")


def participant_prompt(arm: Arm, response_path: Path) -> str:
    """Return the exact, arm-isolated prompt saved with every participant run."""
    arm_instruction = {
        Arm.ORDINARY: "Use ordinary workspace tools. You may create any useful representation or use none.",
        Arm.RELATION_STORE: (
            "Use the supplied generic entity/relation SQLite store at relation_store.sqlite. "
            "Populate and use it as your structured representation."
        ),
        Arm.GRAPHAUTHOR_FORCED: (
            "Graphauthor is available locally through the Python environment. Construct and use a Graphauthor "
            "workbook, and report its path in graphauthor_workbook."
        ),
        Arm.GRAPHAUTHOR_OPTIONAL: (
            "Graphauthor is available locally through the Python environment as one optional tool alongside ordinary "
            "tools. Choose any approach you consider appropriate; do not assume a graph is preferred."
        ),
    }[arm]
    response_schema = (
        "The response schema is {answers:[{operation_id,answer_ids}],artifacts:{representation_path}}."
        if arm in {Arm.ORDINARY, Arm.RELATION_STORE}
        else "The response schema is {answers:[{operation_id,answer_ids}],artifacts:{representation_path,graphauthor_workbook}}."
    )
    return "\n".join((
        "You are an independent benchmark participant.",
        "Work only inside the current workspace. Read workload.json and files under sources, then answer every operation accurately.",
        "Write the required JSON response to the path supplied in the RM_RESPONSE_PATH environment variable.",
        response_schema,
        arm_instruction,
        "Do not read evaluator files, parent directories, or the internet.",
        "If you materialize a persistent representation, report its real path in representation_path.",
        "Finish by verifying that the response file exists and is valid JSON.",
    ))


def _assert_prompt_isolation(arm: Arm, prompt: str) -> None:
    lowered = prompt.lower()
    if arm in {Arm.ORDINARY, Arm.RELATION_STORE}:
        forbidden = [term for term in FORBIDDEN_TREATMENT_TERMS if term in lowered]
        if forbidden:
            raise AssertionError(f"treatment disclosure in {arm.value} prompt: {forbidden}")
    if arm is Arm.GRAPHAUTHOR_FORCED and "graphauthor" not in lowered:
        raise AssertionError("forced Graphauthor prompt is missing its treatment")
    if arm is Arm.GRAPHAUTHOR_OPTIONAL and ("graphauthor" not in lowered or "optional" not in lowered):
        raise AssertionError("optional Graphauthor prompt is missing neutral availability")


def _graphauthor_artifacts(workspace: Path) -> list[str]:
    """Find actual Graphauthor artifacts, independently of participant declarations."""
    found: list[str] = []
    for path in workspace.rglob("*"):
        relative = path.relative_to(workspace).as_posix()
        if path.name in {".graphauthor", "graph.lbug"} or "/.graphauthor/" in f"/{relative}":
            found.append(relative)
        elif path.is_file() and path.name == "encoding.json" and path.parent.name == "out" and (path.parent.parent / "build.py").is_file():
            found.append(relative)
    return sorted(set(found))


def _classify_representation(workspace: Path, stdout: str, stderr: str) -> tuple[str, list[str], list[str]]:
    """Classify visible artifacts and visible tool calls; never inspect model reasoning."""
    artifacts: list[str] = []
    categories: set[str] = set()
    for path in workspace.rglob("*"):
        if not path.is_file() or "sources" in path.relative_to(workspace).parts:
            continue
        relative = path.relative_to(workspace).as_posix()
        suffix = path.suffix.lower()
        name = path.name.lower()
        if suffix in {".sqlite", ".sqlite3", ".db"}:
            categories.add("sqlite")
            artifacts.append(relative)
        elif suffix == ".duckdb":
            categories.add("duckdb")
            artifacts.append(relative)
        elif path.name in {"graph.lbug", "encoding.json"} or ".graphauthor" in path.parts:
            categories.add("graph")
            artifacts.append(relative)
        elif any(token in name for token in ("relation", "entity", "adjacency", "networkx", "graph")):
            categories.add("custom_relational")
            artifacts.append(relative)
        elif any(token in name for token in ("representation", "index", "cache")):
            categories.add("custom_other")
            artifacts.append(relative)
        elif suffix in {".csv", ".tsv", ".parquet"}:
            categories.add("table")
            artifacts.append(relative)
    tool_text: list[str] = []
    for line in (stdout + "\n" + stderr).splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "tool_call":
            tool_text.append(json.dumps(event).lower())
    trajectory = "\n".join(tool_text)
    operation_terms = {
        "reverse_lookup": ("reverse", "incoming"), "join": (" join ", "join("),
        "neighborhood": ("neighbor", "neighbour"), "reachability": ("reachab",),
        "path": ("shortest_path", "find_path", " path"), "recursive_query": ("with recursive",),
        "set_intersection": ("intersection", " & "),
    }
    observed = [name for name, terms in operation_terms.items() if any(term in trajectory for term in terms)]
    if not categories:
        return "none", [], observed
    precedence = ("graph", "duckdb", "sqlite", "custom_relational", "table", "custom_other")
    return next(category for category in precedence if category in categories), sorted(set(artifacts)), observed


def _verify_arm(arm: Arm, workspace: Path, run_root: Path, response: dict[str, Any]) -> list[str]:
    artifacts = response.get("artifacts") or {}
    symptoms: list[str] = []
    if arm is Arm.RELATION_STORE:
        path = _artifact_path(artifacts.get("representation_path"), workspace, run_root)
        if path is None:
            symptoms.append("missing_relation_store_artifact")
        elif not _relation_store_is_valid(path):
            symptoms.append("invalid_relation_store_schema")
    if arm is Arm.GRAPHAUTHOR_FORCED:
        workbook = artifacts.get("graphauthor_workbook", "")
        if not workbook or not (workspace / workbook / "out" / "encoding.json").is_file():
            symptoms.append("missing_graphauthor_encoding")
    actual_graphauthor = _graphauthor_artifacts(workspace)
    if arm in {Arm.ORDINARY, Arm.RELATION_STORE} and (artifacts.get("graphauthor_workbook") or actual_graphauthor):
        symptoms.append("forbidden_graphauthor_artifact")
    return symptoms


def _cursor_usage(stdout: str) -> dict[str, int] | None:
    """Preserve Cursor's durable token counts when stream-json is used."""
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = event.get("usage") if event.get("type") == "result" else None
        if isinstance(usage, dict) and all(isinstance(value, int) for value in usage.values()):
            return usage
    return None


def run_case(
    case: Path,
    arm: Arm,
    command: str,
    results_dir: Path,
    *,
    timeout: int = 180,
    attempt_id: str | None = None,
    prompt_path_override: Path | None = None,
) -> dict[str, Any]:
    """Run an external agent command once against a visible workload.

    The command is executed in a throwaway copy, so no agent can access the
    evaluator oracle. It must write JSON at ``$RM_RESPONSE_PATH``:
    ``{"answers":[{"operation_id":"op-01","answer_ids":[...]}],
    "artifacts":{"representation_path":"...","graphauthor_workbook":"..."}}``.
    """
    base_run_root = results_dir / case.name / arm.value
    run_root = base_run_root / attempt_id if attempt_id else base_run_root
    workspace = run_root / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(case / "agent", workspace)
    response_path = run_root / "response.json"
    run_root.mkdir(parents=True, exist_ok=True)
    if arm is Arm.RELATION_STORE:
        _prepare_relation_store(workspace)
    prompt = prompt_path_override.read_text(encoding="utf-8").rstrip("\n") if prompt_path_override else participant_prompt(arm, response_path)
    _assert_prompt_isolation(arm, prompt)
    prompt_path = run_root / "participant_prompt.txt"
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    repository_root = str(Path(__file__).resolve().parents[2])
    environment = os.environ | {
        "RM_AGENT_WORKSPACE": str(workspace), "RM_RESPONSE_PATH": str(response_path),
        "RM_ARM": arm.value, "RM_ARM_RULE": ARM_RULES[arm], "RM_PROTOCOL": PROTOCOL_VERSION,
        "RM_ARM_TOOL_POLICY": ARM_TOOL_POLICIES[arm], "RM_PARTICIPANT_PROMPT_PATH": str(prompt_path),
    }
    if arm in {Arm.GRAPHAUTHOR_FORCED, Arm.GRAPHAUTHOR_OPTIONAL}:
        environment["PYTHONPATH"] = repository_root + os.pathsep + os.environ.get("PYTHONPATH", "")
    started = time.perf_counter()
    # Cursor's print-mode process can remain alive after it has written the
    # required response. Do not charge an experiment run for terminal cleanup:
    # give it a short grace period, then end its own process group while
    # preserving the completed response and captured trajectory.
    process = subprocess.Popen(command, shell=True, cwd=workspace, env=environment, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    response_seen_at: float | None = None
    terminated_after_response = False
    timed_out_before_response = False
    while process.poll() is None:
        now = time.perf_counter()
        if response_path.is_file():
            response_seen_at = response_seen_at or now
            if now - response_seen_at >= 3:
                os.killpg(process.pid, signal.SIGTERM)
                terminated_after_response = True
                break
        if now - started >= timeout:
            os.killpg(process.pid, signal.SIGTERM)
            timed_out_before_response = not response_path.is_file()
            break
        time.sleep(0.2)
    stdout, stderr = process.communicate()
    elapsed = time.perf_counter() - started
    oracle = _load(case / "evaluator" / "oracle.json")
    response: dict[str, Any] = _load(response_path) if response_path.is_file() else {"answers": [], "artifacts": {}}
    score = score_response(oracle, response)
    representation, representation_artifacts, relational_operations = _classify_representation(workspace, stdout, stderr)
    record = {
        "protocol_version": PROTOCOL_VERSION, "case": case.name, "cell": oracle["cell"], "arm": arm.value,
        "attempt_id": attempt_id or "attempt-1",
        "returncode": process.returncode, "response_completed": response_path.is_file(),
        "terminated_after_response": terminated_after_response, "timed_out_before_response": timed_out_before_response,
        "wall_seconds": elapsed, "score": asdict(score),
        "workload_success": score.workload_success, "symptoms": _verify_arm(arm, workspace, run_root, response),
        "participant_prompt_path": str(prompt_path), "materialized_representation": representation,
        "representation_artifacts": representation_artifacts, "relational_operations_observed": relational_operations,
        "stdout": stdout, "stderr": stderr,
    }
    usage = _cursor_usage(stdout)
    if usage is not None:
        record["model_usage"] = usage
    (run_root / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def reference_command() -> str:
    """A deterministic harness smoke-test participant, not an experimental arm.

    It derives answers from visible source files. It is intentionally named
    reference so it cannot be mistaken for an agent result.
    """
    participant = Path(__file__).with_name("reference_participant.py")
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(participant))}"


def iter_records(results_dir: Path) -> Iterable[dict[str, Any]]:
    for record in sorted(results_dir.glob("*/*/record.json")):
        yield _load(record)
