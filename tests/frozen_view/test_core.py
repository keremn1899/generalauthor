from research.relational_materialization.generator import make_world
import json
import shlex
import sqlite3
import sys

import pytest

from mcp_server.retrieve import Retrieve
from mcp_server.surface import Surface
from research.frozen_view.core import (
    CONSTRUCTION_AGENT_AUTHORED,
    assert_agent_authored_admission,
    canonical_from_world,
    compile_graph,
    compile_sql,
    construction_coverage,
    freeze,
    parity_audit,
    smoke_construction_receipt,
)
from research.frozen_view.run import prepare_frozen_case, run_executor
from research.relational_materialization.generator import write_case
from research.relational_materialization.model import Cell, Heterogeneity, Novelty

def test_frozen_view_has_identical_sql_and_graph_semantics(tmp_path):
    view = canonical_from_world(make_world(54).to_json())
    assert freeze(view, tmp_path / "canonical.json")
    compile_sql(view, tmp_path / "view.sqlite")
    compile_graph(view, tmp_path / "view.lbug")
    assert parity_audit(view, tmp_path / "view.sqlite", tmp_path / "view.lbug") == []
    with sqlite3.connect(tmp_path / "view.sqlite") as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"service_dependencies", "service_ownerships", "runbook_capability_coverage"} <= tables
    assert "entities" not in tables
    assert "facts" not in tables

    surface = Surface(tmp_path / "view.lbug")
    try:
        result = Retrieve(surface).expand(
            ["resource:redis-west"],
            edge_types=["leadsto"],
            edge_labels=["depends_on"],
            direction="incoming",
            depth=1,
        )
    finally:
        surface.close()
    edges = result["evidence"]["edge_records"]
    assert edges
    assert {edge["edge_label"] for edge in edges} == {"depends_on"}
    assert all(edge["edge_evidence"] == "world.json" for edge in edges)
    assert all(edge["relation_id"].startswith("rel:") for edge in edges)


def test_smoke_construction_is_not_admitted_as_an_agent_authored_treatment(tmp_path):
    view = canonical_from_world(make_world(54).to_json())
    coverage = construction_coverage(view, [row["id"] for row in view["facts"]], smoke_construction_receipt(view))
    with pytest.raises(ValueError, match="agent-authored"):
        assert_agent_authored_admission(smoke_construction_receipt(view), coverage)


def test_prepared_sql_arm_records_query_text_returned_ids_and_frozen_audit(tmp_path):
    case = write_case(tmp_path / "cases", Cell(Heterogeneity.PRESTRUCTURED, Novelty.TASK_SPECIFIC, 8), 54)
    view = canonical_from_world(make_world(54).to_json())
    receipt = {
        "construction_mode": CONSTRUCTION_AGENT_AUTHORED,
        "treatment_assignment_known": False,
        "source_scope": ["sources/world.json"],
        "construction_program": "test-only deterministic builder",
        "discovered_relation_ids": [row["id"] for row in view["facts"]],
    }
    frozen = tmp_path / "frozen"
    manifest = prepare_frozen_case(case, frozen, view, receipt)
    assert manifest["semantic_parity"] == "passed"
    assert manifest["construction_coverage"]["canonical_oracle_relation_coverage"] == 1.0
    code = """import json, os, sqlite3
from pathlib import Path
db = sqlite3.connect('view.sqlite')
db.execute(\"SELECT service_id FROM service_dependencies WHERE resource_id = ?\", ('resource:redis-west',)).fetchall()
Path(os.environ['RM_RESPONSE_PATH']).write_text(json.dumps({'answers': [], 'artifacts': {'representation_path': 'view.sqlite'}}))
"""
    record = run_executor(case, frozen, "S", tmp_path / "results", command=f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}")
    assert record["canonical_sha256"] == manifest["canonical_sha256"]
    assert record["semantic_parity"] == "passed"
    assert any("service_dependencies" in row.get("query_text", "") for row in record["sql_queries"])
    assert "service:purchase" in {value for row in record["sql_queries"] for value in row.get("returned_ids", [])}
    assert record["raw_source_fallback_count"] == 0


def test_prepared_graph_arm_uses_bounded_graphauthor_surface_and_records_calls(tmp_path):
    case = write_case(tmp_path / "cases", Cell(Heterogeneity.PRESTRUCTURED, Novelty.TASK_SPECIFIC, 8), 54)
    view = canonical_from_world(make_world(54).to_json())
    receipt = {"construction_mode": CONSTRUCTION_AGENT_AUTHORED, "treatment_assignment_known": False,
               "source_scope": ["sources/world.json"], "construction_program": "test-only deterministic builder",
               "discovered_relation_ids": [row["id"] for row in view["facts"]]}
    frozen = tmp_path / "frozen"; prepare_frozen_case(case, frozen, view, receipt)
    code = """import json, os, subprocess, sys
from pathlib import Path
subprocess.run([sys.executable, 'graphauthor_access.py', 'expand', json.dumps({'node_ids':['resource:redis-west'], 'direction':'incoming', 'depth':1})], check=True)
Path(os.environ['RM_RESPONSE_PATH']).write_text(json.dumps({'answers': [], 'artifacts': {'representation_path': 'view.lbug'}}))
"""
    record = run_executor(case, frozen, "G", tmp_path / "results", command=f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}")
    assert record["graph_operations"][0]["operation"] == "expand"
    assert record["graph_operations"][0]["used_relation_ids"]
    assert record["graph_operations"][0]["returned_ids"]
