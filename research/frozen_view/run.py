"""Instrumented paired executor runner for frozen SQL/Graphauthor views.

This module intentionally prepares and records executions; it does not launch
new experimental cases by itself.  Admission is checked before either arm can
be run.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from research.frozen_view.core import (
    CANONICAL_VERSION,
    CONSTRUCTION_AGENT_AUTHORED,
    assert_agent_authored_admission,
    construction_coverage,
    relation_id,
    validate_view,
)
from research.frozen_view.taxonomy import taxonomy_for_oracle
from research.relational_materialization.runner import score_response


PROTOCOL_VERSION = "frozen-relational-view-v2"
_ROOT = Path(__file__).resolve().parents[2]


def _json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def _cursor_usage(stdout: str) -> dict[str, int] | None:
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        usage = event.get("usage") if event.get("type") == "result" else None
        if isinstance(usage, dict) and all(isinstance(value, int) for value in usage.values()):
            return usage
    return None


def _tool_calls(stdout: str, stderr: str) -> list[dict[str, Any]]:
    calls = []
    for line in (stdout + "\n" + stderr).splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "tool_call":
            calls.append({"order": len(calls) + 1, "event": event})
    return calls


_SQL_TABLE_PREDICATES = {
    "service_dependencies": "depends_on", "service_ownerships": "owned_by",
    "service_capabilities": "provides", "service_deployments": "deployed_in",
    "integration_test_coverage": "covers", "runbook_capability_coverage": "covers_capability",
}


def _sql_used_relation_ids(frozen: Path, events: list[dict[str, Any]]) -> set[str]:
    """Conservatively attribute visible table reads to returned/mentioned facts.

    This is post-execution accounting only. It does not alter SQL capability or
    add an agent-facing helper: a relation is credited only where a logged
    query names its semantic table and either its visible values or immediate
    returned IDs name one endpoint of that fact.
    """
    canonical = json.loads((frozen / "canonical.json").read_text(encoding="utf-8"))
    facts = list(canonical["facts"])
    used: set[str] = set()
    active_predicates: set[str] = set()
    for event in events:
        query = str(event.get("query_text") or "").lower()
        if event.get("event") in {"sql_query", "sql_query_many", "sql_cli"}:
            active_predicates = {predicate for table, predicate in _SQL_TABLE_PREDICATES.items() if table in query}
            values = str(event.get("parameters") or "") + " " + str(event.get("query_text") or "")
            for fact in facts:
                if fact["predicate"] in active_predicates and (fact["subject"] in values or fact["object"] in values):
                    used.add(fact["id"])
        elif event.get("event") == "sql_result" and active_predicates:
            returned = {str(value) for value in event.get("returned_ids", [])}
            for fact in facts:
                if fact["predicate"] in active_predicates and ({fact["subject"], fact["object"]} & returned):
                    used.add(fact["id"])
    return used


_SQL_AUDIT = r'''# Installed by frozen_view.run; ordinary sqlite3 API, audit only.
import json, os, re, sqlite3, threading, time
from pathlib import Path
_audit = Path(os.environ.get("FROZEN_VIEW_SQL_AUDIT", "sql_queries.jsonl"))
_lock = threading.Lock()
_real_connect = sqlite3.connect

def _ids(value):
    if isinstance(value, str): return [value] if ":" in value else []
    if isinstance(value, (list, tuple)): return sum((_ids(x) for x in value), [])
    return []
def _emit(event):
    event["order"] = time.time_ns()
    with _lock:
        with _audit.open("a", encoding="utf-8") as h: h.write(json.dumps(event, default=str) + "\n")
class AuditCursor(sqlite3.Cursor):
    def execute(self, sql, parameters=()):
        _emit({"event": "sql_query", "query_text": str(sql), "parameters": repr(parameters)})
        return super().execute(sql, parameters)
    def executemany(self, sql, parameters):
        _emit({"event": "sql_query_many", "query_text": str(sql)})
        return super().executemany(sql, parameters)
    def executescript(self, script):
        _emit({"event": "sql_script", "query_text": str(script)})
        return super().executescript(script)
    def fetchone(self):
        value = super().fetchone(); _emit({"event": "sql_result", "returned_ids": _ids(value)}); return value
    def fetchall(self):
        value = super().fetchall(); _emit({"event": "sql_result", "returned_ids": _ids(value)}); return value
class AuditConnection(sqlite3.Connection):
    def cursor(self, factory=AuditCursor): return super().cursor(factory)
    def execute(self, sql, parameters=()): return self.cursor().execute(sql, parameters)
    def executemany(self, sql, parameters): return self.cursor().executemany(sql, parameters)
    def executescript(self, script): return self.cursor().executescript(script)
def connect(database, *args, **kwargs):
    if Path(str(database)).name == "view.sqlite" and "factory" not in kwargs:
        kwargs["factory"] = AuditConnection
    return _real_connect(database, *args, **kwargs)
sqlite3.connect = connect
'''


_GRAPH_ACCESS = r'''#!/usr/bin/env python3
"""Bounded Graphauthor retrieval client installed by the experiment harness."""
import contextlib, io, json, os, sys, time
from pathlib import Path
from mcp_server.retrieve import Retrieve
from mcp_server.surface import Surface

def ids(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "id" and isinstance(item, str): found.append(item)
            else: found.extend(ids(item))
    elif isinstance(value, list):
        for item in value: found.extend(ids(item))
    return sorted(set(found))
def relation_ids(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "relation_id" and isinstance(item, str) and item.startswith("rel:"):
                found.append(item)
            if key in {"edge_label", "label"} and isinstance(item, str):
                parts = item.split("|", 2)
                if len(parts) == 3 and parts[2].startswith("rel:"): found.append(parts[2])
            found.extend(relation_ids(item))
    elif isinstance(value, list):
        for item in value: found.extend(relation_ids(item))
    return sorted(set(found))
def audit(event):
    path = Path(os.environ["FROZEN_VIEW_GRAPH_AUDIT"])
    event["order"] = time.time_ns()
    with path.open("a", encoding="utf-8") as h: h.write(json.dumps(event, sort_keys=True) + "\n")
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"lookup", "expand", "path"}:
        raise SystemExit("usage: graphauthor_access.py lookup|expand|path '<JSON arguments object>'")
    operation, kwargs = sys.argv[1], json.loads(sys.argv[2])
    if not isinstance(kwargs, dict): raise SystemExit("arguments must be a JSON object")
    forbidden = {"search", "read_cypher", "include_content", "context_ref", "graph_version"}
    if forbidden.intersection(kwargs): raise SystemExit("this experiment exposes only bounded non-content graph reads")
    # Surface initialization maintains version/receipt state and may emit
    # diagnostic structural-index messages. Those diagnostics contain derived
    # topology labels and are deliberately not participant-visible.
    diagnostics = io.StringIO()
    surface = None
    try:
        with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
            surface = Surface(Path("view.lbug"), capabilities=("query",))
            method = getattr(Retrieve(surface), operation)
            result = method(**kwargs)
        audit({"event": "graph_operation", "operation": operation, "arguments": kwargs,
               "returned_ids": ids(result), "used_relation_ids": relation_ids(result), "outcome": result.get("outcome")})
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        audit({"event": "graph_operation_failure", "operation": operation, "arguments": kwargs, "error": repr(exc)})
        raise
    finally:
        if surface is not None:
            with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics): surface.close()
if __name__ == "__main__": main()
'''


def _sqlite_cli_wrapper(real_sqlite: str) -> str:
    return f'''#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path
proc = subprocess.run([{real_sqlite!r}, *sys.argv[1:]], text=True, capture_output=True)
query = sys.argv[-1] if len(sys.argv) > 2 else ""
event = {{"event":"sql_cli", "order":time.time_ns(), "query_text":query, "returned_ids":[x for x in proc.stdout.split() if ":" in x]}}
with Path(os.environ["FROZEN_VIEW_SQL_AUDIT"]).open("a", encoding="utf-8") as h: h.write(json.dumps(event) + "\\n")
sys.stdout.write(proc.stdout); sys.stderr.write(proc.stderr); raise SystemExit(proc.returncode)
'''


def _access_policy(arm: str) -> str:
    if arm == "S":
        return """# SQL-native access\n\n`view.sqlite` is the frozen relational projection. Inspect its schema and use ordinary SQLite SQL (including joins, aggregates and recursive CTEs). No benchmark-supplied neighbour, expand, traversal, reachability or path helper exists. Raw source files and source-fetch tools are unavailable.\n"""
    return """# Bounded Graphauthor access\n\nUse `python graphauthor_access.py OPERATION JSON_ARGUMENTS` against the frozen graph. The only exposed operations are actual Graphauthor `lookup`, `expand` (depth 1–3), and `path` (1–6 hops). `search`, raw Cypher, embeddings, content paging, summaries, inferred edges, inverse edges and source-fetch tools are unavailable. All graph edges are directed frozen facts: their labels are canonical logical predicates, while evidence and relation IDs are separate edge provenance fields.\n\nExamples: `python graphauthor_access.py lookup '{\"references\":[\"resource:redis-west\"]}'`; `python graphauthor_access.py expand '{\"node_ids\":[\"resource:redis-west\"],\"direction\":\"incoming\",\"depth\":1}'`.\n"""


def prepare_frozen_case(case: Path, frozen: Path, view: dict[str, Any], construction_receipt: dict[str, Any]) -> dict[str, Any]:
    """Freeze, compile and audit one admitted case before S/G assignment."""
    from research.frozen_view.core import compile_graph, compile_sql, freeze, parity_audit
    oracle = json.loads((case / "evaluator" / "oracle.json").read_text(encoding="utf-8"))
    coverage = construction_coverage(view, list(oracle.get("oracle_relation_ids") or []), construction_receipt)
    assert_agent_authored_admission(construction_receipt, coverage)
    frozen.mkdir(parents=True, exist_ok=True)
    digest = freeze(view, frozen / "canonical.json", construction_receipt)
    compile_sql(view, frozen / "sql.sqlite")
    compile_graph(view, frozen / "graph.lbug")
    problems = parity_audit(view, frozen / "sql.sqlite", frozen / "graph.lbug")
    if problems:
        raise ValueError(f"semantic parity audit failed: {problems}")
    manifest = {"protocol_version": PROTOCOL_VERSION, "canonical_sha256": digest, "semantic_parity": "passed",
                "construction_coverage": coverage, "offline_operation_taxonomy": taxonomy_for_oracle(oracle)}
    (frozen / "audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _normalise_builder_view(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Add deterministic accounting IDs without adding or repairing facts."""
    raw_view = payload.get("canonical_view", payload)
    if not isinstance(raw_view, dict):
        raise ValueError("builder output must contain a canonical_view object")
    entities = raw_view.get("entities")
    facts = raw_view.get("facts")
    if not isinstance(entities, list) or not isinstance(facts, list):
        raise ValueError("builder output requires entities and facts arrays")
    normal_facts = []
    for fact in facts:
        if not isinstance(fact, dict):
            raise ValueError("builder facts must be objects")
        subject, predicate, object_, evidence = (str(fact.get(key) or "") for key in ("subject", "predicate", "object", "evidence"))
        normal_facts.append({"id": relation_id(subject, predicate, object_, evidence), "subject": subject,
                             "predicate": predicate, "object": object_, "evidence": evidence})
    view = {"canonical_version": CANONICAL_VERSION, "entities": entities, "facts": normal_facts}
    validate_view(view)
    declared = payload.get("construction_program") or "participant-declared builder program"
    scope = payload.get("source_scope") or []
    if not isinstance(scope, list):
        raise ValueError("builder source_scope must be a list")
    receipt = {"construction_mode": CONSTRUCTION_AGENT_AUTHORED, "treatment_assignment_known": False,
               "source_scope": [str(item) for item in scope], "construction_program": str(declared),
               "discovered_relation_ids": [fact["id"] for fact in normal_facts]}
    return view, receipt


def run_builder(case: Path, out: Path, timeout: int = 180, command: str | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run the upstream, treatment-blind builder against sources only.

    This workspace has neither an S/G artifact nor a workload/oracle, making
    treatment assignment impossible for the builder to observe.
    """
    root, workspace = out / case.name / "builder", out / case.name / "builder" / "workspace"
    if workspace.exists(): shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copytree(case / "agent" / "sources", workspace / "sources")
    output = root / "builder_output.json"; root.mkdir(parents=True, exist_ok=True)
    prompt = """You are the upstream construction agent for a representation-neutral relational-view experiment. Work only in this workspace and inspect sources/. You are not assigned any downstream treatment and must not read parent directories, evaluator files, or the internet. Construct the complete factual canonical view using only these fields: entities [{id,kind,label,evidence}] and facts [{subject,predicate,object,evidence}]. Use these directed predicates where supported by sources: depends_on (service->resource), owned_by (service->team), provides (service->capability), deployed_in (service->environment), covers (test->service), covers_capability (runbook->capability). Preserve every source ID exactly. For derived capability entities and every provides/covers_capability object, use `capability:<capability value>`; environments already use their source `environment:*` IDs. Include every entity referenced by a fact. Evidence must be the source-relative filename (for example `world.json`, never `sources/world.json`). Write only valid JSON to $FROZEN_BUILDER_OUTPUT with {canonical_view:{entities,facts},source_scope:[...],construction_program:"..."}. Do not create SQL, a graph, adjacency lists, paths, closures, inverse facts, summaries, or derived facts."""
    (root / "builder_prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    if command is None:
        command = "cursor agent -p --output-format stream-json --model composer-2.5 --force " + shlex.quote(prompt)
    env = os.environ | {"FROZEN_BUILDER_OUTPUT": str(output), "PYTHONPATH": str(_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    started = time.perf_counter()
    process = subprocess.Popen(command, shell=True, cwd=workspace, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    while process.poll() is None:
        if output.exists() and time.perf_counter() - started >= 3:
            os.killpg(process.pid, signal.SIGTERM); break
        if time.perf_counter() - started >= timeout:
            os.killpg(process.pid, signal.SIGTERM); timed_out = True; break
        time.sleep(0.1)
    stdout, stderr = process.communicate()
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
        view, receipt = _normalise_builder_view(payload)
        status = "completed" if not timed_out else "timeout_after_output"
    except (OSError, ValueError) as exc:
        record = {"protocol_version": PROTOCOL_VERSION, "case": case.name, "construction_status": "failed",
                  "timed_out": timed_out, "returncode": process.returncode, "wall_seconds": time.perf_counter() - started,
                  "error": repr(exc), "stdout": stdout, "stderr": stderr, "model_usage": _cursor_usage(stdout)}
        (root / "builder_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise ValueError(f"builder did not produce a valid canonical view: {exc}") from exc
    record = {"protocol_version": PROTOCOL_VERSION, "case": case.name, "construction_status": status,
              "timed_out": timed_out, "returncode": process.returncode, "wall_seconds": time.perf_counter() - started,
              "source_scope": receipt["source_scope"], "construction_mode": receipt["construction_mode"],
              "treatment_assignment_known": False, "entity_count": len(view["entities"]), "fact_count": len(view["facts"]),
              "stdout": stdout, "stderr": stderr, "model_usage": _cursor_usage(stdout)}
    (root / "builder_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return view, receipt, record


def _copy_arm_artifacts(frozen: Path, workspace: Path, arm: str) -> tuple[Path, Path]:
    sql_audit, graph_audit = workspace / "sql_queries.jsonl", workspace / "graph_operations.jsonl"
    (workspace / "access-policy.md").write_text(_access_policy(arm), encoding="utf-8")
    if arm == "S":
        shutil.copy2(frozen / "sql.sqlite", workspace / "view.sqlite")
        (workspace / "sitecustomize.py").write_text(_SQL_AUDIT, encoding="utf-8")
        bin_dir = workspace / "bin"; bin_dir.mkdir()
        real_sqlite = shutil.which("sqlite3")
        if real_sqlite:
            cli = bin_dir / "sqlite3"; cli.write_text(_sqlite_cli_wrapper(real_sqlite), encoding="utf-8"); cli.chmod(0o755)
    elif arm == "G":
        shutil.copy2(frozen / "graph.lbug", workspace / "view.lbug")
        metadata = Path(str(frozen / "graph.lbug") + ".metadata.json")
        if metadata.exists(): shutil.copy2(metadata, Path(str(workspace / "view.lbug") + ".metadata.json"))
        client = workspace / "graphauthor_access.py"; client.write_text(_GRAPH_ACCESS, encoding="utf-8"); client.chmod(0o755)
    else:
        raise ValueError("arm must be S or G")
    return sql_audit, graph_audit


def run_executor(case: Path, frozen: Path, arm: str, out: Path, timeout: int = 180, command: str | None = None) -> dict[str, Any]:
    """Run one fresh executor with all required visible-event instrumentation."""
    manifest_path = frozen / "audit_manifest.json"
    if not manifest_path.exists():
        raise ValueError("run prepare_frozen_case and parity audit before executing an arm")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root, workspace = out / case.name / arm, out / case.name / arm / "workspace"
    if workspace.exists(): shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copy2(case / "agent" / "workload.json", workspace / "workload.json")
    sql_audit, graph_audit = _copy_arm_artifacts(frozen, workspace, arm)
    response = root / "response.json"; root.mkdir(parents=True, exist_ok=True)
    prompt = "Work only in the workspace. Read workload.json and access-policy.md. Answer every operation and write JSON to $RM_RESPONSE_PATH with {answers:[{operation_id,answer_ids}],artifacts:{representation_path}}. Do not read parent directories, raw sources, evaluator files or the internet."
    (root / "participant_prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    if command is None:
        command = "cursor agent -p --output-format stream-json --model composer-2.5 --force " + shlex.quote(prompt)
    env = os.environ | {"RM_RESPONSE_PATH": str(response), "FROZEN_VIEW_SQL_AUDIT": str(sql_audit),
                        "FROZEN_VIEW_GRAPH_AUDIT": str(graph_audit), "PYTHONPATH": str(_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""),
                        "PATH": str(workspace / "bin") + os.pathsep + os.environ.get("PATH", "")}
    started = time.perf_counter()
    process = subprocess.Popen(command, shell=True, cwd=workspace, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False; response_seen: float | None = None; terminated_after_response = False
    while process.poll() is None:
        now = time.perf_counter()
        if response.exists():
            response_seen = response_seen or now
            if now - response_seen >= 3:
                os.killpg(process.pid, signal.SIGTERM); terminated_after_response = True; break
        if now - started >= timeout:
            os.killpg(process.pid, signal.SIGTERM); timed_out = True; break
        time.sleep(0.1)
    stdout, stderr = process.communicate(); elapsed = time.perf_counter() - started
    oracle = json.loads((case / "evaluator" / "oracle.json").read_text(encoding="utf-8"))
    try:
        response_payload = json.loads(response.read_text(encoding="utf-8")) if response.exists() else {"answers": [], "artifacts": {}}
        response_valid = isinstance(response_payload, dict)
    except ValueError:
        response_payload, response_valid = {"answers": [], "artifacts": {}}, False
    score = score_response(oracle, response_payload)
    sql_events, graph_events = _json_lines(sql_audit), _json_lines(graph_audit)
    used = {rid for event in graph_events for rid in event.get("used_relation_ids", [])}
    used.update(rid for event in sql_events for rid in event.get("returned_ids", []) if isinstance(rid, str) and rid.startswith("rel:"))
    used.update(_sql_used_relation_ids(frozen, sql_events))
    coverage = manifest["construction_coverage"]
    execution_relations = [{**row, "used": row["relation_id"] in used} for row in coverage["relations"]]
    tool_calls = _tool_calls(stdout, stderr)
    record = {"protocol_version": PROTOCOL_VERSION, "case": case.name, "arm": arm,
              "canonical_sha256": manifest["canonical_sha256"], "semantic_parity": manifest["semantic_parity"],
              "response_completed": response.exists(), "response_valid": response_valid, "returncode": process.returncode,
              "timed_out": timed_out, "terminated_after_response": terminated_after_response,
              "execution_status": "completed" if response_valid and not timed_out else "timeout" if timed_out else "invalid_or_missing_response",
              "valid_execution": response_valid and not timed_out, "wall_seconds": elapsed,
              "score": score_response(oracle, response_payload).__dict__, "workload_success": score.workload_success,
              "sql_queries": sql_events, "graph_operations": graph_events,
              "operation_ordering": sorted(sql_events + graph_events, key=lambda event: event.get("order", 0)),
              "tool_calls": tool_calls, "tool_call_count": len(tool_calls), "raw_source_access": "withheld", "raw_source_fallback_count": 0,
              "model_usage": _cursor_usage(stdout), "oracle_relation_accounting": {**coverage, "relations": execution_relations},
              "offline_operation_taxonomy": manifest["offline_operation_taxonomy"], "stdout": stdout, "stderr": stderr}
    (root / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return record
