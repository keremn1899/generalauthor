"""The schema-only path for newly materialized task graphs."""

from __future__ import annotations

from mcp_server.surface import Surface
from tests.workbook_graph_fixture import narrative_fixture


def _surface_without_authored_contract(tmp_path):
    db_path, _ = narrative_fixture(tmp_path / "task-graph.lbug")
    # No graph_contract_path: the fixture's sidecar uses a non-default name, so
    # this surface sees a newly materialized graph with no graph.md.
    return Surface(db_path)


def test_describe_is_neutral_and_reports_the_executable_schema(tmp_path):
    surface = _surface_without_authored_contract(tmp_path)
    try:
        description = surface.describe()

        assert description["kind"] == "GRAPH_DESCRIPTION"
        assert description["schema_fingerprint"].startswith("gschema_")
        assert description["node_kinds"] == ["character", "event", "faction", "place"]
        assert description["predicates"]["participates_in"] == {
            "carrier": "EXPRESSES",
            "carrier_id": "expresses",
            "direction": "directed",
            "source_kinds": ["character"],
            "target_kinds": ["event"],
        }
        assert description["capabilities"]["ephemeral_program"]["max_steps"] == 12
        # These are orientation/interpretation products, never schema facts.
        assert not {"landmarks", "landmark_preview", "centrality", "posture", "grain"} & set(description)
    finally:
        surface.close()


def test_an_ephemeral_program_compiles_against_generated_schema(tmp_path):
    surface = _surface_without_authored_contract(tmp_path)
    try:
        out = surface.run_ephemeral_traversal(
            {
                "steps": [
                    {"op": "lookup", "references": ["character:ilma"], "assign": "seed"},
                    {
                        "op": "expand",
                        "from": "$seed",
                        "predicates": ["participates_in"],
                        "direction": "outgoing",
                        "depth": 1,
                        "assign": "events",
                    },
                ],
                "collect": "$events",
                "answers": {"events": "$events"},
                "result_mode": "compact",
            },
            evidence="packet",
        )

        assert out["kind"] == "EPHEMERAL_TRAVERSAL"
        assert out["outcome"] == "FOUND"
        assert set(out["answers"]["events"]) == {
            "event:the-summons", "event:the-refusal", "event:the-breaking"
        }
        assert "evidence" not in out
        assert "program" not in out
        assert out["execution_receipt"]["result_mode"] == "compact"
        audit = surface._traversal_audit_packets[out["audit_evidence_ref"]]
        assert audit["evidence_packet"]["node_records"]
    finally:
        surface.close()


def test_compact_answer_sets_do_not_change_full_answer_compatibility(tmp_path):
    surface = _surface_without_authored_contract(tmp_path)
    try:
        base = {
            "steps": [
                {"op": "lookup", "references": ["character:ilma"], "assign": "seed"},
                {
                    "op": "expand", "from": "$seed", "predicates": ["participates_in"],
                    "direction": "outgoing", "depth": 1, "assign": "events",
                },
            ],
            "collect": "$events",
            "answers": ["events"],
        }
        full = surface.run_ephemeral_traversal(base, evidence="packet")

        assert set(full["answer_node_ids"]) == {
            "event:the-summons", "event:the-refusal", "event:the-breaking"
        }
        assert full["evidence"]["node_records"]
    finally:
        surface.close()


def test_named_traversal_can_publish_named_compact_answer_sets(tmp_path):
    db_path, contract_path = narrative_fixture(tmp_path / "named-compact.lbug")
    contract_path.write_text(contract_path.read_text().replace(
        "    answers: [paths]",
        "    answers:\n      connections: $paths\n    result_mode: compact",
    ))
    surface = Surface(db_path, graph_contract_path=contract_path)
    try:
        out = surface.run_traversal(
            "how_are_they_connected",
            {"from_id": "character:ilma", "to_id": "character:torv"},
            evidence="packet",
        )

        assert out["outcome"] == "FOUND"
        assert out["answers"]["connections"]
        assert "evidence" not in out
        assert out["execution_receipt"]["answer_sets"] == {
            "connections": "paths"
        }
    finally:
        surface.close()
