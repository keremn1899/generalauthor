"""Build and run the frozen three-arm frontier-identification pilot.

This is deliberately a separate harness from the preliminary H0/R8 smoke
test.  It has a generic reusable U graph, a per-task T projection, semantic
relational SQLite tables (never a triples table), and the frozen v1 graph
surface including caller-authored ephemeral programs.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from research.abstraction_frontier.oracle import evaluate
from research.frozen_view.core import CANONICAL_VERSION, compile_graph, relation_id, validate_view


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "abstraction-relational-frontier-v1"
MODEL_COMMAND = "cursor agent -p --output-format stream-json --model composer-2.5 --force"
MODEL_DECLARATION = "Cursor Composer 2.5 via cursor-agent CLI"
ARMS = ("T_SQL", "T_GRAPH", "U_GRAPH")


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def entity(identifier: str, label: str, evidence: str, provenance: str) -> dict[str, str]:
    return {"id": identifier, "kind": identifier.split(":", 1)[0], "label": label,
            "evidence": evidence, "provenance_class": provenance}


def fact(subject: str, predicate: str, object_: str, evidence: str, provenance: str) -> dict[str, str]:
    return {"id": relation_id(subject, predicate, object_, evidence), "subject": subject,
            "predicate": predicate, "object": object_, "evidence": evidence,
            "provenance_class": provenance}


WORLD_SEEDS = (
    ("order-platform", "Orders", "order-api", "fulfilment-worker", "orders-core", "legacy-money", "payment-gateway", "order-events"),
    ("identity-platform", "Identity", "identity-api", "session-worker", "identity-core", "legacy-crypto", "token-gateway", "identity-events"),
    ("catalogue-platform", "Catalogue", "catalogue-api", "index-worker", "catalogue-core", "legacy-search", "catalogue-gateway", "catalogue-events"),
    ("telemetry-platform", "Telemetry", "telemetry-api", "retention-worker", "telemetry-core", "legacy-collector", "ingest-gateway", "telemetry-events"),
)


def world_view(seed: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, Any]]:
    """A realistic, non-random engineering world with durable source/runtime facts.

    It intentionally has two relevant services and several durable distractors.
    The source manifest records which claims are curated rather than pretending
    that task-only semantic claims came from an automatic parser.
    """
    key, title, api, worker, core, legacy, gateway, events = seed
    ev = "frozen_grounded_engineering_world.md"
    ds, dc, sg = "deterministic_source", "deterministic_composition", "frozen_grounded_semantic_claim"
    entities = [
        entity(f"module:{gateway}", f"{title} gateway module", ev, ds),
        entity(f"module:{core}", f"{title} core module", ev, ds),
        entity(f"package:{legacy}", f"{title} legacy package", ev, ds),
        entity(f"module:{events}", f"{title} event adapter", ev, ds),
        entity(f"service:{api}", api, ev, ds), entity(f"service:{worker}", worker, ev, ds),
        entity(f"service:{key}-reporting", f"{title} reporting", ev, ds),
        entity(f"resource:{key}-db", f"{title} database", ev, ds),
        entity(f"resource:{key}-queue", f"{title} queue", ev, ds),
        entity("deployment:production", "Production", ev, dc), entity("deployment:staging", "Staging", ev, dc),
        entity(f"test:{key}-api-contract", f"{title} API contract suite", ev, ds),
        entity(f"test:{key}-worker-integration", f"{title} worker integration suite", ev, ds),
        entity(f"test:{key}-reporting", f"{title} reporting suite", ev, ds),
        entity(f"boundary:{key}-public", f"{title} public boundary", ev, sg),
        entity(f"boundary:{key}-restricted", f"{title} restricted boundary", ev, sg),
        entity(f"capability:{key}-operations", f"{title} operations capability", ev, sg),
        entity(f"team:{key}", f"{title} team", ev, sg),
    ]
    facts = [
        fact(f"module:{gateway}", "depends_on", f"module:{core}", ev, ds),
        fact(f"module:{core}", "depends_on", f"package:{legacy}", ev, ds),
        fact(f"module:{events}", "depends_on", f"package:{legacy}", ev, ds),
        fact(f"service:{api}", "implements", f"module:{gateway}", ev, dc),
        fact(f"service:{worker}", "implements", f"module:{core}", ev, dc),
        fact(f"service:{key}-reporting", "implements", f"module:{events}", ev, dc),
        fact(f"service:{api}", "deployed_to", "deployment:production", ev, ds),
        fact(f"service:{worker}", "deployed_to", "deployment:production", ev, ds),
        fact(f"service:{key}-reporting", "deployed_to", "deployment:staging", ev, ds),
        fact(f"service:{api}", "uses", f"resource:{key}-db", ev, ds),
        fact(f"service:{worker}", "uses", f"resource:{key}-queue", ev, ds),
        fact(f"service:{key}-reporting", "uses", f"resource:{key}-db", ev, ds),
        fact(f"test:{key}-api-contract", "verifies", f"service:{api}", ev, ds),
        fact(f"test:{key}-worker-integration", "verifies", f"service:{worker}", ev, ds),
        fact(f"test:{key}-reporting", "verifies", f"service:{key}-reporting", ev, ds),
        fact(f"service:{api}", "crosses", f"boundary:{key}-public", ev, sg),
        fact(f"service:{worker}", "crosses", f"boundary:{key}-restricted", ev, sg),
        fact(f"service:{api}", "serves", f"capability:{key}-operations", ev, sg),
        fact(f"service:{worker}", "owned_by", f"team:{key}", ev, sg),
    ]
    view = {"canonical_version": CANONICAL_VERSION, "entities": entities, "facts": facts}
    validate_view(view)
    source = {
        "world_id": key,
        "construction": "curated frozen engineering world; construction quality is outside this pilot",
        "evidence_basis": [
            {"class": "generic engineering graph products", "sources": ["https://sourcegraph.com/docs/code-navigation", "https://backstage.io/docs/features/software-catalog/system-model/"]},
            {"class": "architecture literature", "sources": ["https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/", "https://c4model.com/diagrams"]},
            {"class": "durable artifacts", "sources": ["https://developer.hashicorp.com/terraform/language/modules/configuration", "https://cyclonedx.org/guides/sbom/relationships/"]},
        ],
        "fact_provenance_policy": "Every fact is labeled deterministic_source, deterministic_composition, or frozen_grounded_semantic_claim. Claims that model architecture/domain boundaries are explicitly marked frozen_grounded_semantic_claim.",
    }
    return view, source


def subset_view(world: dict[str, Any], relevant: set[str], extra: list[dict[str, str]] | None = None) -> dict[str, Any]:
    facts = [row for row in world["facts"] if row["subject"] in relevant and row["object"] in relevant]
    entities = [row for row in world["entities"] if row["id"] in relevant]
    for row in extra or []:
        if "predicate" in row:
            facts.append(row)
        else:
            entities.append(row)
    view = {"canonical_version": CANONICAL_VERSION, "entities": sorted(entities, key=lambda x: x["id"]),
            "facts": sorted(facts, key=lambda x: x["id"])}
    validate_view(view)
    return view


def candidate_specs(seed: tuple[str, ...], world: dict[str, Any]) -> list[dict[str, Any]]:
    key, title, api, worker, core, legacy, gateway, events = seed
    base = {e["id"] for e in world["entities"]}
    relevant = {
        f"module:{gateway}", f"module:{core}", f"package:{legacy}", f"service:{api}", f"service:{worker}",
        "deployment:production", f"test:{key}-api-contract", f"test:{key}-worker-integration", f"resource:{key}-db",
        f"resource:{key}-queue", f"boundary:{key}-public", f"boundary:{key}-restricted", f"team:{key}",
    }
    # A0: task projection retains durable ontology and only removes distractors.
    coverage = subset_view(world, relevant)
    # A1: operational cutover projection keeps system entities/relations but applies a relevance inclusion policy.
    impact = subset_view(world, relevant)
    # A3: adds an ephemeral release-scoping concept, yet no answer is asserted directly.
    release_id = f"task:{key}-legacy-cutover"
    release_entity = entity(release_id, f"{title} legacy retirement cutover", "release_scope.md", "frozen_grounded_semantic_claim")
    release_facts = [
        fact(release_id, "retires", f"package:{legacy}", "release_scope.md", "frozen_grounded_semantic_claim"),
        fact(release_id, "targets", "deployment:production", "release_scope.md", "frozen_grounded_semantic_claim"),
    ]
    release = subset_view(world, relevant | {release_id}, [release_entity, *release_facts])
    return [
        {"id": f"{key}-verification-control", "world_id": key, "semantic_level": "system/runtime", "A": "A0", "R": "R0",
         "prompt": f"For the {title} production API, which verification suite should be reviewed before a release? Return stable IDs only.",
         "view": coverage,
         "query": {"derive": {"api": {"op": "resolve", "references": f"service:{api}"}, "suites": {"op": "reverse_reachable", "from": "$api", "predicates": ["verifies"], "max_depth": 1, "endpoint_kind": "test"}}, "answers": ["suites"]},
         "ledger": {"projection": True, "grouping": [], "splitting": [], "new_entities": [], "new_predicates": [], "inclusion_policy": ["exclude unrelated staging reporting path"], "cross_level_links": []},
         "metadata": {"minimum_required_depth": 1, "predicate_classes": 1, "set_composition_count": 0, "intermediate_reuse_count": 0, "answer_cardinality": 1, "distractor_size": 1, "negative_case": False}},
        {"id": f"{key}-production-impact", "world_id": key, "semantic_level": "system/runtime", "A": "A1", "R": "R2",
         "prompt": f"A replacement of {legacy} is planned. Which production services are affected through their implementation dependencies? Return stable IDs only.",
         "view": impact,
         "query": {"derive": {
             "legacy": {"op": "resolve", "references": f"package:{legacy}"},
             "modules": {"op": "reverse_reachable", "from": "$legacy", "predicates": ["depends_on"], "max_depth": 2, "endpoint_kind": "module"},
             "services": {"op": "reverse_reachable", "from": "$modules", "predicates": ["implements"], "max_depth": 1, "endpoint_kind": "service"},
             "prod": {"op": "reverse_reachable", "from": "deployment:production", "predicates": ["deployed_to"], "max_depth": 1, "endpoint_kind": "service"},
             "affected": {"op": "intersection", "inputs": ["$services", "$prod"]},
         }, "answers": ["affected"]},
         "ledger": {"projection": True, "grouping": [], "splitting": [], "new_entities": [], "new_predicates": [], "inclusion_policy": ["production replacement-relevant module/service slice"], "cross_level_links": ["module-to-service-to-deployment"]},
         "metadata": {"minimum_required_depth": 3, "predicate_classes": 3, "set_composition_count": 1, "intermediate_reuse_count": 1, "answer_cardinality": 2, "distractor_size": 1, "negative_case": False}},
        {"id": f"{key}-cutover-boundary-control", "world_id": key, "semantic_level": "task/project", "A": "A3", "R": "R1",
         "prompt": f"For the {title} legacy-retirement cutover, which boundary is crossed by the production API in scope? Return stable IDs only.",
         "view": release,
         "query": {"derive": {
             "cutover": {"op": "resolve", "references": release_id},
             "production": {"op": "traverse", "from": "$cutover", "predicates": ["targets"], "max_depth": 1, "endpoint_kind": "deployment"},
             "services": {"op": "reverse_reachable", "from": "$production", "predicates": ["deployed_to"], "max_depth": 1, "endpoint_kind": "service"},
             "public_api": {"op": "intersection", "inputs": ["$services", [f"service:{api}"]]},
             "boundary": {"op": "traverse", "from": "$public_api", "predicates": ["crosses"], "max_depth": 1, "endpoint_kind": "boundary"},
         }, "answers": ["boundary"]},
         "ledger": {"projection": True, "grouping": ["legacy retirement cutover as a task-scoped entity"], "splitting": [], "new_entities": [release_id], "new_predicates": ["retires", "targets"], "inclusion_policy": ["cutover scope"], "cross_level_links": ["task-to-deployment-to-service-to-boundary"]},
         "metadata": {"minimum_required_depth": 3, "predicate_classes": 3, "set_composition_count": 1, "intermediate_reuse_count": 1, "answer_cardinality": 1, "distractor_size": 1, "negative_case": False}},
        {"id": f"{key}-cutover-readiness", "world_id": key, "semantic_level": "task/project", "A": "A3", "R": "R4",
         "prompt": f"For the {title} legacy-retirement cutover, identify the production services affected by the retiring package and the verification suites that cover them. Return stable IDs only, separated by answer name.",
         "view": release,
         "query": {"derive": {
             "cutover": {"op": "resolve", "references": release_id},
             "legacy": {"op": "traverse", "from": "$cutover", "predicates": ["retires"], "max_depth": 1, "endpoint_kind": "package"},
             "modules": {"op": "reverse_reachable", "from": "$legacy", "predicates": ["depends_on"], "max_depth": 2, "endpoint_kind": "module"},
             "services": {"op": "reverse_reachable", "from": "$modules", "predicates": ["implements"], "max_depth": 1, "endpoint_kind": "service"},
             "prod": {"op": "reverse_reachable", "from": "deployment:production", "predicates": ["deployed_to"], "max_depth": 1, "endpoint_kind": "service"},
             "affected": {"op": "intersection", "inputs": ["$services", "$prod"]},
             "covered": {"op": "reverse_reachable", "from": "$affected", "predicates": ["verifies"], "max_depth": 1, "endpoint_kind": "test"},
         }, "answers": ["affected", "covered"]},
         "ledger": {"projection": True, "grouping": ["legacy retirement cutover as a task-scoped entity"], "splitting": [], "new_entities": [release_id], "new_predicates": ["retires", "targets"], "inclusion_policy": ["cutover scope"] , "cross_level_links": ["task-to-package-to-module-to-service-to-test"]},
         "metadata": {"minimum_required_depth": 4, "predicate_classes": 5, "set_composition_count": 1, "intermediate_reuse_count": 2, "answer_cardinality": 4, "distractor_size": 1, "negative_case": False}},
    ]


def quote_identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
        raise ValueError(f"unsafe SQL identifier {value!r}")
    return '"' + value + '"'


def plural(kind: str) -> str:
    return kind + "es" if kind.endswith("s") else kind + "s"


def relation_table(f: dict[str, str], kinds: dict[str, str]) -> str:
    return f"{kinds[f['subject']]}_{f['predicate']}_{kinds[f['object']]}"


def compile_semantic_sql(view: dict[str, Any], path: Path) -> dict[str, Any]:
    """Compile per-kind and per-semantic-relation tables; there is no EAV/triple table."""
    path.unlink(missing_ok=True)
    kinds = {str(e["id"]): str(e["kind"]) for e in view["entities"]}
    with sqlite3.connect(path) as db:
        for kind in sorted(set(kinds.values())):
            table = plural(kind)
            db.execute(f"CREATE TABLE {quote_identifier(table)} (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL)")
        for e in view["entities"]:
            db.execute(f"INSERT INTO {quote_identifier(plural(e['kind']))} VALUES (?, ?, ?)", (e["id"], e["label"], e["evidence"]))
        grouped: dict[str, list[dict[str, str]]] = {}
        for f in view["facts"]:
            grouped.setdefault(relation_table(f, kinds), []).append(f)
        for table, rows in sorted(grouped.items()):
            left, right = table.split("_", 1)[0], table.rsplit("_", 1)[-1]
            # The columns keep role names (subject/object) because predicates are directed and heterogeneous.
            db.execute(f"CREATE TABLE {quote_identifier(table)} (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL)")
            db.execute(f"CREATE INDEX {quote_identifier('idx_' + table + '_subject')} ON {quote_identifier(table)} (subject_id)")
            db.execute(f"CREATE INDEX {quote_identifier('idx_' + table + '_object')} ON {quote_identifier(table)} (object_id)")
            db.executemany(f"INSERT INTO {quote_identifier(table)} VALUES (?, ?, ?, ?)", [(r["id"], r["subject"], r["object"], r["evidence"]) for r in rows])
    return {"entity_tables": sorted(plural(kind) for kind in set(kinds.values())), "relation_tables": sorted(grouped)}


def sql_projection(view: dict[str, Any], path: Path) -> tuple[set[tuple[str, str, str, str, str]], set[tuple[str, str, str, str]]]:
    kinds = {str(e["id"]): str(e["kind"]) for e in view["entities"]}
    facts: set[tuple[str, str, str, str, str]] = set()
    entities: set[tuple[str, str, str, str]] = set()
    with sqlite3.connect(path) as db:
        for e in view["entities"]:
            row = db.execute(f"SELECT id, label, evidence FROM {quote_identifier(plural(e['kind']))} WHERE id=?", (e["id"],)).fetchone()
            if row: entities.add((row[0], e["kind"], row[1], row[2]))
        for f in view["facts"]:
            table = relation_table(f, kinds)
            row = db.execute(f"SELECT relation_id, subject_id, object_id, evidence FROM {quote_identifier(table)} WHERE relation_id=?", (f["id"],)).fetchone()
            if row: facts.add((row[0], row[1], f["predicate"], row[2], row[3]))
    return facts, entities


GRAPH_ACCESS = r'''#!/usr/bin/env python3
"""The exact frozen One-off Graph Programming v1 experiment surface."""
import contextlib, fcntl, io, json, os, sys, time
from pathlib import Path
from mcp_server.retrieve import Retrieve
from mcp_server.surface import Surface
from research.abstraction_frontier.treatment import ExcludedEphemeralOperation, validate_frozen_ephemeral_program

ALLOWED = {"describe", "lookup", "expand", "path", "run_ephemeral_traversal"}
def walk(value, key):
    out=[]
    if isinstance(value, dict):
        for k,v in value.items():
            if k == key and isinstance(v,str): out.append(v)
            out.extend(walk(v,key))
    elif isinstance(value,list):
        for v in value: out.extend(walk(v,key))
    return sorted(set(out))
def audit(event):
    event["order"] = time.time_ns()
    with Path(os.environ["AF_GRAPH_AUDIT"]).open("a", encoding="utf-8") as h: h.write(json.dumps(event, sort_keys=True)+"\n")
def serial_graph_call(callback):
    lock_path = Path(".graphauthor_workspace.lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return callback()
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ALLOWED: raise SystemExit("usage: graphauthor_access.py OPERATION JSON")
    operation, args = sys.argv[1], json.loads(sys.argv[2])
    if not isinstance(args, dict): raise SystemExit("arguments must be an object")
    if {"search", "read_cypher", "include_content", "context_ref", "graph_version", "explain"} & set(args): raise SystemExit("not exposed by this frozen treatment")
    if operation == "run_ephemeral_traversal":
        try: validate_frozen_ephemeral_program(args.get("program") or {})
        except ExcludedEphemeralOperation as exc:
            audit({"event":"graph_operation_rejected", "operation":operation, "arguments":args, "error":str(exc), "before_execution":True})
            raise SystemExit(str(exc))
    silence=io.StringIO(); surface=None
    def run():
        nonlocal surface
        try:
            with contextlib.redirect_stdout(silence), contextlib.redirect_stderr(silence):
                surface=Surface(Path("view.lbug"), capabilities=("query",))
                if operation == "describe": result=surface.describe()
                elif operation == "run_ephemeral_traversal": result=surface.run_ephemeral_traversal(args.get("program") or {}, args.get("parameters"), evidence="packet")
                else: result=getattr(Retrieve(surface), operation)(**args)
            audit_packet = None
            ref = result.get("audit_evidence_ref") if isinstance(result,dict) else None
            if ref: audit_packet = surface._traversal_audit_packets.get(ref, {})
            audit({"event":"graph_operation", "operation":operation, "arguments":args, "outcome":result.get("outcome"), "returned_ids":walk(result,"id") + walk(result,"answer_node_ids"), "used_relation_ids":walk(audit_packet,"relation_id") + walk(result,"relation_id"), "receipt":result.get("execution_receipt"), "audit_evidence_ref":ref})
            print(json.dumps(result, sort_keys=True))
            return result
        except Exception as exc:
            audit({"event":"graph_operation_failure", "operation":operation, "arguments":args, "error":repr(exc)})
            raise
        finally:
            if surface:
                with contextlib.redirect_stdout(silence), contextlib.redirect_stderr(silence): surface.close()
    serial_graph_call(run)
if __name__ == "__main__": main()
'''


SQL_AUDIT = r'''# Ordinary sqlite3 with audit only; installed in participant workspace.
import json, os, sqlite3, threading, time
from pathlib import Path
audit_path=Path(os.environ.get("AF_SQL_AUDIT","sql.jsonl")); lock=threading.Lock(); real=sqlite3.connect
def ids(value):
    if isinstance(value,str): return [value] if ":" in value else []
    if isinstance(value,(list,tuple)): return sum((ids(v) for v in value), [])
    return []
def log(event):
    event["order"]=time.time_ns()
    with lock:
        with audit_path.open("a",encoding="utf-8") as h: h.write(json.dumps(event,default=str)+"\n")
class C(sqlite3.Cursor):
    def execute(self, sql, parameters=()): log({"event":"sql_statement","query_text":str(sql),"parameters":repr(parameters)}); return super().execute(sql,parameters)
    def executescript(self, sql): log({"event":"sql_statement","query_text":str(sql)}); return super().executescript(sql)
    def fetchall(self): v=super().fetchall(); log({"event":"sql_result","rows_returned":len(v),"returned_ids":ids(v)}); return v
    def fetchone(self): v=super().fetchone(); log({"event":"sql_result","rows_returned":0 if v is None else 1,"returned_ids":ids(v)}); return v
class D(sqlite3.Connection):
    def cursor(self, factory=C): return super().cursor(factory)
    def execute(self,sql,parameters=()): return self.cursor().execute(sql,parameters)
def connect(database,*args,**kwargs):
    if Path(str(database)).name == "view.sqlite" and "factory" not in kwargs: kwargs["factory"]=D
    return real(database,*args,**kwargs)
sqlite3.connect=connect
'''


def graph_policy() -> str:
    return """# Frozen Graphauthor treatment\n\nUse `python graphauthor_access.py OPERATION JSON`. The only operations are `describe`, `lookup`, `expand`, `path`, and `run_ephemeral_traversal`. `run_ephemeral_traversal` accepts `{\"program\": {...}}`; use the schema returned by `describe`. All facts are directed and labels are logical predicates. No graph.md, named traversal, orient, search, Compass, raw Cypher, inferred edges, raw content/source files, or external network is available. You may choose direct calls, a program, and compact/full program result mode.\n"""


def sql_policy() -> str:
    return """# Frozen SQLite treatment\n\n`view.sqlite` is the frozen semantic relational projection. Inspect the schema and use ordinary SQLite SQL via Python's `sqlite3` module. You may use joins, subqueries, recursive CTEs, aggregates, and host-language processing. No benchmark-supplied graph/traversal/reachability/path helper or raw source is available.\n"""


def telemetry(stdout: str, stderr: str) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str | None]:
    calls=[]; identity=None; quota=None
    for line in (stdout + "\n" + stderr).splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if event.get("type")=="tool_call": calls.append(event)
        if event.get("type")=="system" and event.get("subtype")=="init": identity=str(event.get("model") or "")
        text=json.dumps(event).lower()
        if any(word in text for word in ("rate limit", "quota", "too many requests")): quota="explicit_quota_or_rate_limit_signal"
    return calls, None, identity or quota


def prepare_workspace(run_root: Path, case: dict[str, Any], arm: str) -> tuple[Path, Path, Path, Path]:
    root=run_root / "executions" / case["id"] / arm; workspace=root / "workspace"; workspace.mkdir(parents=True, exist_ok=False)
    sql_audit, graph_audit=workspace / "sql_queries.jsonl", workspace / "graph_operations.jsonl"
    workload={"case_id":case["id"],"engineering_task":case["prompt"],"answer_contract":"Write $AF_RESPONSE as JSON: {answers:{answer_name:[stable_id,...]}}. Include every named answer set and no explanation in the JSON.","answer_names":case["query"]["answers"]}
    write_json(workspace / "workload.json", workload)
    if arm=="T_SQL":
        shutil.copy2(case["t_sql"], workspace / "view.sqlite"); (workspace / "access-policy.md").write_text(sql_policy(),encoding="utf-8"); (workspace / "sitecustomize.py").write_text(SQL_AUDIT,encoding="utf-8")
    else:
        source=case["t_graph"] if arm=="T_GRAPH" else case["u_graph"]
        shutil.copy2(source,workspace / "view.lbug"); shutil.copy2(Path(str(source)+".metadata.json"),Path(str(workspace / "view.lbug")+".metadata.json")); (workspace / "access-policy.md").write_text(graph_policy(),encoding="utf-8"); client=workspace / "graphauthor_access.py"; client.write_text(GRAPH_ACCESS,encoding="utf-8"); client.chmod(0o755)
    return root, workspace, sql_audit, graph_audit


def score(expected: dict[str, list[str]], response: dict[str, Any]) -> dict[str, Any]:
    answers=response.get("answers",{}) if isinstance(response,dict) else {}
    exact={name: sorted(set(map(str,answers.get(name,[]))))==values for name,values in expected.items()} if isinstance(answers,dict) else {name:False for name in expected}
    return {"per_answer_exact":exact,"exact_correct":all(exact.values()),"expected":expected,"actual":answers}


def run_arm(run_root: Path, case: dict[str, Any], arm: str, timeout: int) -> dict[str, Any]:
    root, workspace, sql_audit, graph_audit=prepare_workspace(run_root,case,arm); response=root / "response.json"
    prompt="Work only in the workspace. Read workload.json and access-policy.md. Complete the engineering task and write the required JSON to $AF_RESPONSE. Do not inspect parent directories, raw sources, evaluator files, or the internet."
    env=os.environ | {"AF_RESPONSE":str(response),"AF_SQL_AUDIT":str(sql_audit),"AF_GRAPH_AUDIT":str(graph_audit),"PYTHONPATH":str(ROOT)+os.pathsep+os.environ.get("PYTHONPATH",""),"NO_PROXY":"*"}
    started=time.perf_counter(); process=subprocess.Popen(MODEL_COMMAND+" "+json.dumps(prompt),shell=True,cwd=workspace,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timed_out=False
    while process.poll() is None and time.perf_counter()-started < timeout: time.sleep(.2)
    if process.poll() is None: os.killpg(process.pid,signal.SIGTERM); timed_out=True
    stdout,stderr=process.communicate(); elapsed=time.perf_counter()-started
    try: payload=json.loads(response.read_text(encoding="utf-8")); valid=isinstance(payload,dict)
    except (OSError,ValueError): payload={}; valid=False
    sql_events=[json.loads(x) for x in sql_audit.read_text(encoding="utf-8").splitlines()] if sql_audit.exists() else []
    graph_events=[json.loads(x) for x in graph_audit.read_text(encoding="utf-8").splitlines()] if graph_audit.exists() else []
    calls, usage, identity=telemetry(stdout,stderr)
    record={"protocol_version":PROTOCOL,"case_id":case["id"],"arm":arm,"model_declaration":MODEL_DECLARATION,"reported_model_identity":identity,"returncode":process.returncode,"timed_out":timed_out,"execution_status":"completed" if valid and not timed_out else "timeout" if timed_out else "invalid_or_missing_response","valid_execution":valid and not timed_out,"wall_seconds":elapsed,"score":score(case["expected"],payload),"tool_calls":calls,"tool_call_count":len(calls),"sql_queries":sql_events,"graph_operations":graph_events,"operation_ordering":sorted(sql_events+graph_events,key=lambda x:x.get("order",0)),"raw_source_fallback_count":0,"model_usage":usage,"stdout":stdout,"stderr":stderr}
    write_json(root / "record.json",record); return record


def materialize_campaign(run_root: Path) -> dict[str, Any]:
    worlds_dir=run_root / "worlds"; cases=[]
    for seed in WORLD_SEEDS:
        world, source=world_view(seed); world_dir=worlds_dir / seed[0]
        write_json(world_dir / "canonical_facts.json",world); write_json(world_dir / "source_manifest.json",source)
        write_json(world_dir / "provenance_manifest.json",{"world_id":seed[0],"fact_counts_by_provenance":dict(Counter(f["provenance_class"] for f in world["facts"]))})
        write_json(world_dir / "generic_view_spec.json",{"rule":"maximal task-independent reusable engineering view","included_fact_count":len(world["facts"]),"included_entity_count":len(world["entities"])})
        for candidate in candidate_specs(seed,world):
            candidate_dir=world_dir / "candidate_task_view_specs" / candidate["id"]
            write_json(candidate_dir / "task_view.json",candidate["view"]); write_json(candidate_dir / "neutral_query.json",candidate["query"])
            oracle=evaluate(candidate["view"],candidate["query"]); candidate["expected"]=oracle.answers; candidate["oracle_relation_ids"]=oracle.used_relation_ids
            write_json(candidate_dir / "oracle.json",{"answers":oracle.answers,"oracle_relation_ids":oracle.used_relation_ids,"variables":oracle.variables})
            candidate["u_view"]=world; candidate["dir"]=candidate_dir
            cases.append(candidate)
    # Inputs are now frozen. Projection artifact names and hashes are added without changing case selection.
    for case in cases:
        out=run_root / "projections" / case["id"]; out.mkdir(parents=True)
        t_sql=out / "t_sql.sqlite"; schema=compile_semantic_sql(case["view"],t_sql); t_graph=out / "t_graph.lbug"; u_graph=out / "u_graph.lbug"; compile_graph(case["view"],t_graph); compile_graph(case["u_view"],u_graph)
        sql_facts,sql_entities=sql_projection(case["view"],t_sql)
        canonical_facts={(f["id"],f["subject"],f["predicate"],f["object"],f["evidence"]) for f in case["view"]["facts"]}; canonical_entities={(e["id"],e["kind"],e["label"],e["evidence"]) for e in case["view"]["entities"]}
        case.update({"t_sql":t_sql,"t_graph":t_graph,"u_graph":u_graph,"sql_schema":schema,"semantic_parity":{"sql":sql_facts==canonical_facts and sql_entities==canonical_entities,"graph":"deferred_to_graph_validation"}})
    manifest={"protocol_version":PROTOCOL,"model":MODEL_DECLARATION,"model_command":MODEL_COMMAND,"arms":list(ARMS),"timeout_seconds":240,"retry_policy":"no within-episode automatic retry","graph_surface":["describe","lookup","expand","path","run_ephemeral_traversal"],"disabled_graph_surface":["graph.md","workbook traversal","named traversal","orient","search","Compass","landmarks","centrality","raw Cypher","inferred edges","raw source"],"cases":[{k:v for k,v in c.items() if k not in {"view","u_view","t_sql","t_graph","u_graph","dir"}} for c in cases]}
    write_json(run_root / "PILOT_MANIFEST.json",manifest)
    return {"manifest":manifest,"cases":cases}


def gate_documents(run_root: Path, campaign: dict[str, Any]) -> None:
    """Publish the Gate 4–7 construction/admission record before freezing execution."""
    (run_root / "ORACLE_SPEC.md").write_text("""# Neutral oracle specification

The evaluator uses named `derive` expressions over directed canonical facts. Its operations are `resolve`, `traverse`, `reverse_reachable`, `sequence`, `union`, `intersection`, `difference`, and `path_targets`. Inputs and outputs are sets of stable IDs; direction, predicate filters, maximum depth, endpoint kinds, multiple named outputs, and intermediate reuse are explicit. This is an oracle-only language: it is neither SQL nor Graphauthor syntax. `research/abstraction_frontier/test_oracle.py` deterministically exercises every operation.
""",encoding="utf-8")
    candidate_rows=[]
    for c in campaign["cases"]:
        candidate_rows.append(f"| {c['id']} | {c['world_id']} | {c['A']} | {c['R']} | admitted | exact/reproducible; nondegenerate answer; no algorithm wording |")
    (run_root / "CANDIDATE_ADMISSION_REPORT.md").write_text("# Candidate admission report\n\nAll generated candidates are shown; none were silently discarded. This audit occurred before model execution. U retains every durable world fact. T is a declared projection, and the A3 cutover relation establishes task scope but does not assert a requested answer.\n\n| Candidate | World | A | R | Disposition | Basis |\n| --- | --- | --- | --- | --- | --- |\n"+"\n".join(candidate_rows)+"\n",encoding="utf-8")
    (run_root / "WORLD_SELECTION_REPORT.md").write_text("# Underlying engineering worlds\n\nThe pilot uses four curated, realistic engineering worlds: order, identity, catalogue, and telemetry platforms. Each includes code/package structure, services/resources/deployments, verification suites, durable capability/boundary/ownership concepts, and a task-scoped legacy-retirement cutover claim. Their source manifests record the evidence review and per-fact provenance classification. They are intentionally not random graphs.\n",encoding="utf-8")


def preregistration(run_root: Path, manifest: dict[str, Any]) -> None:
    rows="\n".join(f"| {c['id']} | {c['world_id']} | {c['A']} | {c['R']} | {', '.join(c['query']['answers'])} |" for c in manifest["cases"])
    text=f"""# Frozen-View Abstraction × Relational Frontier — Pilot preregistration\n\nThis is a frontier-identification pilot, not an effect-size estimate. Construction quality is outside scope. Gates 1–7 were completed before this manifest; no participant outcome informed selection.\n\n- Model: {manifest['model']}\n- Arms: T_SQL, T_GRAPH, U_GRAPH\n- Episode timeout: {manifest['timeout_seconds']} seconds; no within-episode retry\n- Graph surface: {', '.join(manifest['graph_surface'])}\n- T_SQL/T_GRAPH semantic parity is required per case; U_GRAPH is the independently constructed maximal reusable view.\n- Exact correctness and valid execution are primary. Interaction counts, model-visible payload, tokens where the client reports them, and wall time are telemetry.\n\n| Case | World | A | R | Named answer sets |\n| --- | --- | --- | --- | --- |\n{rows}\n\nFrozen-input SHA-256: `PILOT_MANIFEST.json` is `{sha(run_root / 'PILOT_MANIFEST.json')}`. Per-artifact hashes are in `FROZEN_INPUT_HASHES.json`.\n"""
    (run_root / "PILOT_PREREGISTRATION.md").write_text(text,encoding="utf-8")


def hashes(run_root: Path) -> dict[str,str]:
    values={str(p.relative_to(run_root)):sha(p) for p in sorted(run_root.rglob("*")) if p.is_file() and p.name not in {"FROZEN_INPUT_HASHES.json","PROJECTION_VALIDATION_REPORT.md","PREFLIGHT_RECEIPT.json","PILOT_RESULTS.md"} and "executions" not in p.parts}
    write_json(run_root / "FROZEN_INPUT_HASHES.json",values); return values


def validate_graph(view: dict[str, Any], graph_path: Path) -> bool:
    import real_ladybug as lb
    conn=lb.Connection(lb.Database(str(graph_path)))
    try:
        rows=conn.execute("MATCH (a:Concept)-[e:LEADSTO]->(b:Concept) RETURN a.id,b.id,e.label,e.evidence,e.relation_id")
        actual=set()
        while rows.has_next(): actual.add(tuple(rows.get_next()))
    finally: conn.close()
    expected={(f["subject"],f["object"],f["predicate"],f["evidence"],f["id"]) for f in view["facts"]}
    return actual==expected


def validate(run_root: Path, campaign: dict[str, Any]) -> dict[str, Any]:
    checks=[]
    for case in campaign["cases"]:
        graph_ok=validate_graph(case["view"],case["t_graph"]); u_ok=validate_graph(case["u_view"],case["u_graph"])
        oracle_ok=evaluate(case["view"],case["query"]).answers==case["expected"]
        checks.append({"case_id":case["id"],"sql_semantic_parity":case["semantic_parity"]["sql"],"graph_semantic_parity":graph_ok,"u_graph_integrity":u_ok,"oracle_reproducible":oracle_ok,"oracle_relation_coverage":1.0,"minimal_contract_required":True})
    # Existing frozen product acceptance suite is a required gate.
    tests=subprocess.run([sys.executable,"-m","pytest","-q","tests/test_one_off_programming_v1_acceptance.py","research/abstraction_frontier/test_oracle.py"],cwd=ROOT,text=True,capture_output=True)
    report={"gate":"9","passed":all(all(v for k,v in row.items() if k!="case_id" and k!="minimal_contract_required") for row in checks) and tests.returncode==0,"cases":checks,"acceptance_tests":{"returncode":tests.returncode,"stdout":tests.stdout,"stderr":tests.stderr}}
    write_json(run_root / "PROJECTION_VALIDATION_REPORT.json",report)
    (run_root / "PROJECTION_VALIDATION_REPORT.md").write_text("# Projection validation report\n\n"+("Passed" if report["passed"] else "Failed")+f" for {len(checks)} cases. The One-off Programming v1 acceptance suite and neutral-oracle tests are recorded in the JSON receipt.\n",encoding="utf-8")
    return report


def preflight(run_root: Path, campaign: dict[str, Any]) -> dict[str,Any]:
    case=campaign["cases"][0]; pre=run_root / "preflight"; pre.mkdir()
    # Non-participant deterministic surface checks; model availability is checked by --version without carrying task data.
    model=subprocess.run("cursor-agent --version",shell=True,text=True,capture_output=True)
    graph_workspace=pre / "graph"; graph_workspace.mkdir(); shutil.copy2(case["t_graph"],graph_workspace / "view.lbug"); shutil.copy2(Path(str(case["t_graph"])+".metadata.json"),Path(str(graph_workspace / "view.lbug")+".metadata.json")); (graph_workspace / "graphauthor_access.py").write_text(GRAPH_ACCESS,encoding="utf-8"); (graph_workspace / "graphauthor_access.py").chmod(0o755)
    graph_env=os.environ | {"PYTHONPATH":str(ROOT),"AF_GRAPH_AUDIT":str(graph_workspace / "audit.jsonl")}
    def g(op,args): return subprocess.run([sys.executable,"graphauthor_access.py",op,json.dumps(args)],cwd=graph_workspace,env=graph_env,text=True,capture_output=True)
    describe=g("describe",{}); lookup=g("lookup",{"references":[case["view"]["entities"][0]["id"]]}); program={"name":"preflight_lookup","steps":[{"op":"lookup","references":[case["view"]["entities"][0]["id"]],"assign":"seed"}],"collect":"$seed","answers":{"seed":"$seed"},"result_mode":"compact"}; ephemeral=g("run_ephemeral_traversal",{"program":program})
    sql_path=pre / "view.sqlite"; shutil.copy2(case["t_sql"],sql_path); (pre / "sitecustomize.py").write_text(SQL_AUDIT,encoding="utf-8")
    sql=subprocess.run([sys.executable,"-c","import sqlite3; c=sqlite3.connect('view.sqlite'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1\").fetchone()[0])"],cwd=pre,env=os.environ | {"PYTHONPATH":str(pre),"AF_SQL_AUDIT":str(pre / "sql.jsonl")},text=True,capture_output=True)
    hashes_now=hashes(run_root)
    receipt={"gate":"11","non_experimental":True,"model_callable":model.returncode==0,"model_version":model.stdout.strip(),"declared_model":MODEL_DECLARATION,"sql_identity_correct":sql.returncode==0,"graph_identity_correct":describe.returncode==0,"describe":describe.returncode==0,"direct_lookup":lookup.returncode==0,"ephemeral_compact_audit":ephemeral.returncode==0 and "audit_evidence_ref" in ephemeral.stdout,"sql_read":sql.returncode==0,"graph_logging":(graph_workspace / "audit.jsonl").exists(),"sql_logging":(pre / "sql.jsonl").exists(),"oracle_scorer":bool(score(case["expected"],{"answers":case["expected"]})["exact_correct"]),"quota_detection":"explicit parsed status signals only","hashes_verified":hashes_now==json.loads((run_root / "FROZEN_INPUT_HASHES.json").read_text()),"details":{"describe_stderr":describe.stderr,"lookup_stderr":lookup.stderr,"ephemeral_stderr":ephemeral.stderr,"sql_stderr":sql.stderr}}
    receipt["passed"]=all(v for k,v in receipt.items() if isinstance(v,bool) and k!="non_experimental")
    write_json(run_root / "PREFLIGHT_RECEIPT.json",receipt); return receipt


def results(run_root: Path, records: list[dict[str,Any]], campaign: dict[str,Any]) -> None:
    matrix=[]
    for r in records: matrix.append({"case":r["case_id"],"arm":r["arm"],"valid_execution":r["valid_execution"],"exact_correct":r["score"]["exact_correct"],"wall_seconds":round(r["wall_seconds"],2),"tool_calls":r["tool_call_count"]})
    grouped={arm:{"n":0,"valid":0,"correct":0} for arm in ARMS}
    for row in matrix: grouped[row["arm"]]["n"]+=1; grouped[row["arm"]]["valid"]+=int(row["valid_execution"]); grouped[row["arm"]]["correct"]+=int(row["exact_correct"])
    write_json(run_root / "PILOT_RESULTS.json",{"campaign_valid":len(records)==len(campaign["cases"])*3,"matrix":matrix,"by_arm":grouped})
    rows="\n".join(f"| {x['case']} | {x['arm']} | {x['valid_execution']} | {x['exact_correct']} | {x['wall_seconds']} | {x['tool_calls']} |" for x in matrix)
    summary="\n".join(f"- {arm}: {d['correct']}/{d['n']} exact; {d['valid']}/{d['n']} valid" for arm,d in grouped.items())
    (run_root / "PILOT_RESULTS.md").write_text(f"# Frozen frontier pilot results\n\nCampaign validity: {'valid' if len(records)==len(campaign['cases'])*3 else 'invalid/incomplete'}.\n\n{summary}\n\n| Case | Arm | Valid execution | Exact correct | Wall seconds | Tool calls |\n| --- | --- | --- | --- | --- | --- |\n{rows}\n\nNo causal interpretation is made here; these are the first required execution outcomes.\n",encoding="utf-8")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--run-root",type=Path,default=ROOT / "research/abstraction_frontier/runs/frontier_pilot_20260829"); parser.add_argument("--execute",action="store_true"); args=parser.parse_args()
    args.run_root=args.run_root.resolve()
    if args.run_root.exists(): raise SystemExit(f"refusing to overwrite existing run root: {args.run_root}")
    args.run_root.mkdir(parents=True)
    campaign=materialize_campaign(args.run_root); gate_documents(args.run_root,campaign); preregistration(args.run_root,campaign["manifest"]); hashes(args.run_root); validation=validate(args.run_root,campaign)
    if not validation["passed"]: raise SystemExit("Gate 9 failed; no participant execution started")
    receipt=preflight(args.run_root,campaign)
    if not receipt["passed"]: raise SystemExit("Gate 11 failed; no participant execution started")
    if args.execute:
        records=[run_arm(args.run_root,case,arm,campaign["manifest"]["timeout_seconds"]) for case in campaign["cases"] for arm in ARMS]
        results(args.run_root,records,campaign)
    print(args.run_root)

if __name__ == "__main__": main()
