"""Acceptance gate for the frozen Graphauthor one-off programming v1 surface.

These are apparatus checks, not experiment cases.  They exercise the actual
no-graph.md path that the frozen-view graph treatment will use.
"""

from __future__ import annotations

from mcp_server.graph_contract import load_graph_contract
from mcp_server.surface import Surface
from tests.workbook_graph_fixture import narrative_fixture


def _scratch_surface(tmp_path) -> Surface:
    db_path, _ = narrative_fixture(tmp_path / "scratch-task-graph.lbug")
    # The fixture's contract is intentionally not called graph.md.  With no
    # explicit path, this is the minimal-contract path used by the experiment.
    return Surface(db_path)


def _event_sets_program(*, result_mode: str = "compact") -> dict:
    return {
        "name": "compare_participation",
        "steps": [
            {"op": "lookup", "references": ["character:ilma"], "assign": "ilma"},
            {"op": "lookup", "references": ["character:torv"], "assign": "torv"},
            {
                "op": "expand", "from": "$ilma", "predicates": ["participates_in"],
                "direction": "outgoing", "depth": 1, "assign": "ilma_events",
            },
            {
                "op": "expand", "from": "$torv", "predicates": ["participates_in"],
                "direction": "outgoing", "depth": 1, "assign": "torv_events",
            },
            {
                "op": "difference", "of": "$ilma_events", "minus": "$torv_events",
                "assign": "only_ilma",
            },
            {
                "op": "intersection", "of": "$ilma_events", "with": "$torv_events",
                "assign": "shared_events",
            },
        ],
        "collect": "$only_ilma + $shared_events",
        "answers": {
            "only_ilma": "$only_ilma",
            "shared_events": "$shared_events",
        },
        "result_mode": result_mode,
    }


def test_describe_is_representation_only_and_sufficient_to_program(tmp_path):
    surface = _scratch_surface(tmp_path)
    try:
        description = surface.describe()

        assert set(description) == {
            "contract_version", "graph_version", "trace_id", "kind", "outcome",
            "source", "schema_version", "schema_fingerprint", "node_kinds",
            "predicates", "capabilities",
        }
        assert description["predicates"]["participates_in"]["carrier"] == "EXPRESSES"
        assert description["predicates"]["participates_in"]["direction"] == "directed"
        assert "find_paths" in description["capabilities"]["ephemeral_program"]["ops"]
        assert description["capabilities"]["ephemeral_program"]["result_modes"] == [
            "full", "compact"
        ]
    finally:
        surface.close()


def test_no_graph_md_derives_contract_and_supports_predicate_path(tmp_path):
    surface = _scratch_surface(tmp_path)
    try:
        out = surface.run_ephemeral_traversal(
            {
                "name": "predicate_path_from_scratch_schema",
                "steps": [
                    {"op": "lookup", "references": ["character:ilma"], "assign": "source"},
                    {"op": "lookup", "references": ["place:the-terrace"], "assign": "target"},
                    {
                        "op": "find_paths", "from": "$source", "to": "$target",
                        "predicates": ["participates_in", "occurs_at"],
                        "direction": "outgoing", "max_hops": 2, "assign": "paths",
                    },
                ],
                "collect": "$paths",
                "answers": {"paths": "$paths"},
                "result_mode": "compact",
            },
            evidence="packet",
        )

        assert out["outcome"] == "FOUND"
        assert "place:the-terrace" in out["answers"]["paths"]
        assert out["execution_receipt"]["operations"][-1]["result_count"] == 3
        assert out["execution_receipt"]["format_fingerprint"].startswith("gschema_")
    finally:
        surface.close()


def test_authored_contract_precedes_generated_minimal_contract(tmp_path):
    db_path, contract_path = narrative_fixture(tmp_path / "authored-contract.lbug")
    authored = load_graph_contract(contract_path)
    surface = Surface(db_path, graph_contract_path=contract_path)
    try:
        out = surface.run_ephemeral_traversal(
            _event_sets_program(), evidence="packet"
        )

        assert out["outcome"] == "FOUND"
        assert out["execution_receipt"]["format_fingerprint"] == authored.fingerprint
        assert not out["execution_receipt"]["format_fingerprint"].startswith("gschema_")
    finally:
        surface.close()


def test_set_algebra_reuses_intermediate_variables_and_compact_hides_them(tmp_path):
    surface = _scratch_surface(tmp_path)
    try:
        out = surface.run_ephemeral_traversal(
            _event_sets_program(), evidence="packet"
        )

        assert out["outcome"] == "FOUND"
        assert out["answers"] == {
            "only_ilma": ["event:the-refusal"],
            "shared_events": ["event:the-breaking", "event:the-summons"],
        }
        assert [op["assign_to"] for op in out["execution_receipt"]["operations"]] == [
            "ilma", "torv", "ilma_events", "torv_events", "only_ilma", "shared_events",
        ]
        assert "evidence" not in out
        assert "program" not in out
        assert "membership" not in out
    finally:
        surface.close()


def test_compact_audit_reference_retains_complete_packet_and_full_is_compatible(tmp_path):
    surface = _scratch_surface(tmp_path)
    try:
        compact = surface.run_ephemeral_traversal(
            _event_sets_program(), evidence="packet"
        )
        audit = surface._traversal_audit_packets[compact["audit_evidence_ref"]]

        assert audit["execution_receipt"]["audit_evidence_ref"] == compact["audit_evidence_ref"]
        assert audit["execution_receipt"]["packet_node_count"] == len(
            audit["evidence_packet"]["node_records"]
        )
        assert {row["id"] for row in audit["evidence_packet"]["node_records"]} >= {
            "character:ilma", "character:torv", "event:the-refusal",
        }

        full = surface.run_ephemeral_traversal(
            _event_sets_program(result_mode="full"), evidence="packet"
        )
        assert full["outcome"] == "FOUND"
        assert full["answer_node_ids"] == [
            "event:the-refusal", "event:the-breaking", "event:the-summons",
        ]
        assert full["evidence"]["node_records"]
    finally:
        surface.close()


def test_legacy_answer_list_remains_supported(tmp_path):
    surface = _scratch_surface(tmp_path)
    try:
        program = _event_sets_program(result_mode="full")
        program["answers"] = ["only_ilma"]
        out = surface.run_ephemeral_traversal(program, evidence="packet")

        assert out["outcome"] == "FOUND"
        assert out["answer_node_ids"] == ["event:the-refusal"]
        assert out["execution_receipt"]["answer_sets"] == {
            "only_ilma": "only_ilma"
        }
    finally:
        surface.close()
