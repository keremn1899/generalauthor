import json
import os
import subprocess
import sys

import pytest

from research.abstraction_frontier.treatment import (
    ExcludedEphemeralOperation,
    treatment_fingerprint,
    validate_frozen_ephemeral_program,
)


@pytest.mark.parametrize("program", [
    {"steps": [{"op": "search", "query": "production", "assign": "hits"}], "collect": "$hits"},
    {"then": [{"op": "select_landmarks", "assign": "landmarks"}], "steps": [{"op": "lookup", "references": ["service:x"], "assign": "seed"}], "collect": "$seed"},
    {"steps": [{"op": "read_cypher", "query": "MATCH (n)", "assign": "raw"}], "collect": "$raw"},
])
def test_excluded_recipe_operations_fail_before_execution(program):
    with pytest.raises(ExcludedEphemeralOperation, match="EXCLUDED_EPHEMERAL_OPERATION"):
        validate_frozen_ephemeral_program(program)


def test_canonical_fact_program_remains_admissible_and_fingerprint_is_stable():
    validate_frozen_ephemeral_program({
        "steps": [
            {"op": "lookup", "references": ["service:x"], "assign": "seed"},
            {"op": "expand", "from": "$seed", "predicates": ["depends_on"], "assign": "deps"},
            {"op": "intersection", "of": "$deps", "with": "$deps", "assign": "answer"},
        ], "collect": "$answer",
    })
    assert treatment_fingerprint() == "fgt_7899e5ed448eedb70605"


def test_experiment_wrapper_rejects_search_before_opening_a_graph(tmp_path):
    """No view.lbug is supplied: a search rejection must happen first."""
    from research.abstraction_frontier.campaign import GRAPH_ACCESS, ROOT

    client = tmp_path / "graphauthor_access.py"
    client.write_text(GRAPH_ACCESS, encoding="utf-8")
    audit = tmp_path / "graph.jsonl"
    process = subprocess.run(
        [sys.executable, str(client), "run_ephemeral_traversal", json.dumps({
            "program": {"steps": [{"op": "search", "query": "anything", "assign": "hits"}], "collect": "$hits"}
        })],
        cwd=tmp_path,
        env=os.environ | {"PYTHONPATH": str(ROOT), "AF_GRAPH_AUDIT": str(audit)},
        text=True, capture_output=True,
    )
    assert process.returncode != 0
    assert "EXCLUDED_EPHEMERAL_OPERATION" in process.stderr
    event = json.loads(audit.read_text(encoding="utf-8"))
    assert event["event"] == "graph_operation_rejected"
    assert event["before_execution"] is True
