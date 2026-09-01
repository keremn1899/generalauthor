"""Frozen-view preparation for the SQL-native versus Graphauthor experiment.

The canonical object is an interchange artifact, never a participant-facing
database. ``canonical_from_world`` is retained solely for the original
oracle/harness smoke test; it is deliberately ineligible for the
agent-authored experiment.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from graph_storage.records import GraphEdge, GraphNode, MaterializedGraph
from graph_storage.writer import write_graph_records


CANONICAL_VERSION = "frozen-relational-view-v2"
CONSTRUCTION_AGENT_AUTHORED = "agent_authored_treatment_blind"
CONSTRUCTION_ORACLE_SMOKE = "oracle_harness_smoke"


def relation_id(subject: str, predicate: str, object_: str, evidence: str) -> str:
    """A stable identity for accounting, not an additional semantic relation."""
    return "rel:" + hashlib.sha256("\0".join((subject, predicate, object_, evidence)).encode()).hexdigest()[:20]


def _fact(subject: str, predicate: str, object_: str, evidence: str = "world.json") -> dict[str, str]:
    return {"id": relation_id(subject, predicate, object_, evidence), "subject": subject,
            "predicate": predicate, "object": object_, "evidence": evidence}


def canonical_from_world(world: dict[str, Any]) -> dict[str, Any]:
    """Build the old deterministic smoke-test view from evaluator world data.

    It must not be used as an upstream agent construction for a treatment case.
    """
    entities: list[dict[str, str]] = []
    facts: list[dict[str, str]] = []
    for collection, kind in (("resources", "resource"), ("teams", "team"), ("services", "service"), ("tests", "test"), ("runbooks", "runbook")):
        for row in world.get(collection, []):
            entities.append({"id": row["id"], "kind": kind, "label": row.get("name", row["id"]), "evidence": "world.json"})
    for service in world["services"]:
        for predicate, target in (("depends_on", service["resource"]), ("owned_by", service["owner"]), ("provides", f"capability:{service['capability']}"), ("deployed_in", service["environment"])):
            facts.append(_fact(service["id"], predicate, target))
    for test in world["tests"]:
        facts.append(_fact(test["id"], "covers", test["service"]))
    for runbook in world["runbooks"]:
        facts.append(_fact(runbook["id"], "covers_capability", f"capability:{runbook['capability']}"))
    known = {item["id"] for item in entities}
    for fact in facts:
        if fact["object"] not in known:
            entities.append({"id": fact["object"], "kind": fact["object"].split(":", 1)[0], "label": fact["object"], "evidence": "world.json"})
            known.add(fact["object"])
    return {"canonical_version": CANONICAL_VERSION, "entities": sorted(entities, key=lambda x: x["id"]),
            "facts": sorted(facts, key=lambda x: (x["subject"], x["predicate"], x["object"], x["id"]))}


def smoke_construction_receipt(view: dict[str, Any]) -> dict[str, Any]:
    """Receipt for the preliminary apparatus; it explicitly fails admission."""
    return {"construction_mode": CONSTRUCTION_ORACLE_SMOKE, "treatment_assignment_known": None,
            "source_scope": ["evaluator world"], "construction_program": "canonical_from_world",
            "discovered_relation_ids": [fact["id"] for fact in view["facts"]]}


def validate_view(view: dict[str, Any]) -> None:
    entities, facts = view.get("entities"), view.get("facts")
    if not isinstance(entities, list) or not isinstance(facts, list):
        raise ValueError("canonical view requires entities and facts lists")
    entity_ids = [str(row.get("id") or "") for row in entities]
    if not all(entity_ids) or len(entity_ids) != len(set(entity_ids)):
        raise ValueError("canonical entity IDs must be non-empty and unique")
    fact_ids: set[str] = set()
    for fact in facts:
        if any(not str(fact.get(key) or "") for key in ("id", "subject", "predicate", "object", "evidence")):
            raise ValueError("canonical facts require id, subject, predicate, object, evidence")
        if fact["id"] != relation_id(fact["subject"], fact["predicate"], fact["object"], fact["evidence"]):
            raise ValueError(f"noncanonical relation ID: {fact['id']}")
        if fact["id"] in fact_ids:
            raise ValueError(f"duplicate canonical relation ID: {fact['id']}")
        fact_ids.add(fact["id"])
        if fact["subject"] not in entity_ids or fact["object"] not in entity_ids:
            raise ValueError(f"fact endpoints must be canonical entities: {fact['id']}")


def canonical_payload(view: dict[str, Any]) -> str:
    validate_view(view)
    normalized = {"canonical_version": view.get("canonical_version", CANONICAL_VERSION),
                  "entities": sorted(view["entities"], key=lambda x: x["id"]),
                  "facts": sorted(view["facts"], key=lambda x: (x["subject"], x["predicate"], x["object"], x["id"]))}
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def freeze(view: dict[str, Any], path: Path, construction_receipt: dict[str, Any] | None = None) -> str:
    """Write a frozen content-addressed canonical artifact and optional receipt."""
    payload = canonical_payload(view)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    path.write_text(json.dumps({"sha256": digest, **json.loads(payload)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if construction_receipt is not None:
        path.with_name("construction_receipt.json").write_text(json.dumps(construction_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return digest


def construction_coverage(view: dict[str, Any], oracle_relation_ids: list[str], receipt: dict[str, Any]) -> dict[str, Any]:
    """Account for every oracle-relevant relation before downstream execution."""
    validate_view(view)
    persisted = {fact["id"] for fact in view["facts"]}
    discovered = {str(value) for value in receipt.get("discovered_relation_ids", [])}
    rows = [{"relation_id": rid, "discovered": rid in discovered, "persisted": rid in persisted, "used": False}
            for rid in sorted(set(oracle_relation_ids))]
    count = sum(row["persisted"] for row in rows)
    return {"oracle_relevant_relation_count": len(rows), "persisted_count": count,
            "canonical_oracle_relation_coverage": count / len(rows) if rows else 1.0, "relations": rows}


def assert_agent_authored_admission(receipt: dict[str, Any], coverage: dict[str, Any]) -> None:
    if receipt.get("construction_mode") != CONSTRUCTION_AGENT_AUTHORED:
        raise ValueError("frozen treatment case requires an agent-authored construction receipt")
    if receipt.get("treatment_assignment_known") is not False:
        raise ValueError("builder receipt must attest treatment-blind construction")
    if coverage["canonical_oracle_relation_coverage"] != 1.0:
        raise ValueError("all oracle-relevant relations must be persisted before execution")


def compile_sql(view: dict[str, Any], path: Path) -> None:
    """Compile an idiomatic semantic relational schema, never a triple table."""
    validate_view(view)
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript("""
CREATE TABLE resources (id TEXT PRIMARY KEY, name TEXT NOT NULL, environment TEXT, evidence TEXT NOT NULL);
CREATE TABLE teams (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE capabilities (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE environments (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE services (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE integration_tests (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE runbooks (id TEXT PRIMARY KEY, name TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE service_dependencies (relation_id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), resource_id TEXT NOT NULL REFERENCES resources(id), evidence TEXT NOT NULL);
CREATE TABLE service_ownerships (relation_id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), team_id TEXT NOT NULL REFERENCES teams(id), evidence TEXT NOT NULL);
CREATE TABLE service_capabilities (relation_id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), capability_id TEXT NOT NULL REFERENCES capabilities(id), evidence TEXT NOT NULL);
CREATE TABLE service_deployments (relation_id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), environment_id TEXT NOT NULL REFERENCES environments(id), evidence TEXT NOT NULL);
CREATE TABLE integration_test_coverage (relation_id TEXT PRIMARY KEY, test_id TEXT NOT NULL REFERENCES integration_tests(id), service_id TEXT NOT NULL REFERENCES services(id), evidence TEXT NOT NULL);
CREATE TABLE runbook_capability_coverage (relation_id TEXT PRIMARY KEY, runbook_id TEXT NOT NULL REFERENCES runbooks(id), capability_id TEXT NOT NULL REFERENCES capabilities(id), evidence TEXT NOT NULL);
CREATE INDEX service_dependencies_resource ON service_dependencies(resource_id);
CREATE INDEX service_ownerships_service ON service_ownerships(service_id);
CREATE INDEX service_capabilities_service ON service_capabilities(service_id);
CREATE INDEX service_deployments_service ON service_deployments(service_id);
CREATE INDEX integration_test_coverage_service ON integration_test_coverage(service_id);
CREATE INDEX runbook_capability_coverage_capability ON runbook_capability_coverage(capability_id);
""")
        tables = {"resource": "resources", "team": "teams", "capability": "capabilities", "environment": "environments", "service": "services", "test": "integration_tests", "runbook": "runbooks"}
        for entity in view["entities"]:
            table = tables.get(entity["kind"])
            if table is None:
                raise ValueError(f"unsupported canonical entity kind: {entity['kind']}")
            db.execute(f"INSERT INTO {table} (id, name, evidence) VALUES (?, ?, ?)", (entity["id"], entity["label"], entity["evidence"]))
        projections = {"depends_on": ("service_dependencies", "service_id", "resource_id"), "owned_by": ("service_ownerships", "service_id", "team_id"), "provides": ("service_capabilities", "service_id", "capability_id"), "deployed_in": ("service_deployments", "service_id", "environment_id"), "covers": ("integration_test_coverage", "test_id", "service_id"), "covers_capability": ("runbook_capability_coverage", "runbook_id", "capability_id")}
        for fact in view["facts"]:
            table, left, right = projections.get(fact["predicate"], (None, None, None))
            if table is None:
                raise ValueError(f"unsupported canonical predicate: {fact['predicate']}")
            db.execute(f"INSERT INTO {table} (relation_id, {left}, {right}, evidence) VALUES (?, ?, ?, ?)", (fact["id"], fact["subject"], fact["object"], fact["evidence"]))


def compile_graph(view: dict[str, Any], path: Path) -> None:
    """Materialize Graphauthor's actual Ladybug retrieval substrate.

    All edges use LEADSTO as a mechanical carrier. The edge label is the
    logical canonical predicate; provenance and stable relation identity are
    independent relationship properties. No inverse edges, closure, summaries,
    embeddings, or search index are materialized.
    """
    validate_view(view)
    path.unlink(missing_ok=True)
    nodes = {e["id"]: GraphNode(id=e["id"], kind=e["kind"], label=e["label"], text_content="", semantic_anchor="", source_unit_ids=[]) for e in view["entities"]}
    graph = MaterializedGraph(id="frozen-canonical-view", domain="frozen-relational-view", nodes=nodes,
                              edges=[GraphEdge(f["subject"], f["object"], "leadsto", f["predicate"], f["evidence"], f["id"]) for f in view["facts"]])
    write_graph_records(path, graph, embed=False)
    Path(str(path) + ".metadata.json").write_text(json.dumps({"embedding_status": "NOT_BUILT"}, indent=2) + "\n", encoding="utf-8")


def _sql_facts(db: sqlite3.Connection) -> set[tuple[str, str, str, str, str]]:
    out: set[tuple[str, str, str, str, str]] = set()
    projections = {"depends_on": ("service_dependencies", "service_id", "resource_id"), "owned_by": ("service_ownerships", "service_id", "team_id"), "provides": ("service_capabilities", "service_id", "capability_id"), "deployed_in": ("service_deployments", "service_id", "environment_id"), "covers": ("integration_test_coverage", "test_id", "service_id"), "covers_capability": ("runbook_capability_coverage", "runbook_id", "capability_id")}
    for predicate, (table, left, right) in projections.items():
        out.update((row[0], row[1], predicate, row[2], row[3]) for row in db.execute(f"SELECT relation_id, {left}, {right}, evidence FROM {table}"))
    return out


def _graph_projection(path: Path) -> tuple[set[tuple[str, str, str]], set[tuple[str, str, str, str, str]]]:
    import real_ladybug as lb
    conn = lb.Connection(lb.Database(str(path)))
    try:
        nodes: set[tuple[str, str, str]] = set()
        rows = conn.execute("MATCH (n:Concept) RETURN n.id, n.kind, n.label")
        while rows.has_next(): nodes.add(tuple(rows.get_next()))
        facts: set[tuple[str, str, str, str, str]] = set()
        rows = conn.execute("MATCH (a:Concept)-[e:LEADSTO]->(b:Concept) RETURN a.id, b.id, e.label, e.evidence, e.relation_id")
        while rows.has_next():
            source, target, predicate, evidence, rid = rows.get_next()
            facts.add((rid or "", source, predicate or "", target, evidence or ""))
        return nodes, facts
    finally:
        conn.close()


def parity_audit(view: dict[str, Any], sql_path: Path, graph_path: Path) -> list[str]:
    """Verify every entity and fact: presence, direction, predicate, evidence."""
    validate_view(view)
    with sqlite3.connect(sql_path) as db:
        sql_entities = set()
        for table, kind in (("resources", "resource"), ("teams", "team"), ("capabilities", "capability"), ("environments", "environment"), ("services", "service"), ("integration_tests", "test"), ("runbooks", "runbook")):
            sql_entities.update((row[0], kind, row[1], row[2]) for row in db.execute(f"SELECT id, name, evidence FROM {table}"))
        sql_facts = _sql_facts(db)
    graph_nodes, graph_facts = _graph_projection(graph_path)
    entity_evidence = {e["id"]: e["evidence"] for e in view["entities"]}
    graph_entities = {(identifier, kind, label, entity_evidence.get(identifier, "")) for identifier, kind, label in graph_nodes}
    canonical_entities = {(e["id"], e["kind"], e["label"], e["evidence"]) for e in view["entities"]}
    canonical_facts = {(f["id"], f["subject"], f["predicate"], f["object"], f["evidence"]) for f in view["facts"]}
    return [name for name, actual, expected in (("sql entities", sql_entities, canonical_entities), ("graph entities", graph_entities, canonical_entities), ("sql facts", sql_facts, canonical_facts), ("graph facts", graph_facts, canonical_facts)) if actual != expected]
