"""Deterministic negative tests for H1–H3. No LLM."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from taskview import Grounding, GroundingKind, RelationMode, Role, RoleType, TaskView

from research.semantic_integration.domains.diligence.constructor_v3_1_1.admit import admit_workspace
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.abi_completeness import (
    check_abi,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.negative_closure import (
    parse_gate_result,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.provenance import (
    validate_provenance,
)


def test_unbound_required_identity_is_unsatisfied() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "01_vocabulary.json"
        path.write_text(
            json.dumps(
                {
                    "relations": [
                        {
                            "name": "contract_record",
                            "roles": [
                                {"name": "contract_id", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                            ],
                        }
                    ]
                }
            )
        )
        payload = check_abi(path, require_materializable=False)
        assert payload["fields"]["counterparty_text"]["status"] == "SATISFIED"
        assert payload["fields"]["active"]["status"] == "UNSATISFIED"
        assert "active" in payload["unsatisfied"]
        assert payload["ok"] is False


def test_ungrounded_world_assertion_fails_provenance() -> None:
    with tempfile.TemporaryDirectory() as raw:
        world = Path(raw) / "world.sqlite"
        tv = TaskView(str(world), view_id="diligence-world")
        tv.declare_relation(
            "identity_judgment",
            [Role("left", RoleType.TEXT), Role("right", RoleType.TEXT), Role("disposition", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.assert_tuple(
            "identity_judgment",
            {"left": "a", "right": "b", "disposition": "UNRESOLVED"},
        )
        payload = validate_provenance(world)
        assert payload["ok"] is False
        assert payload["ungrounded_count"] == 1


def test_grounded_world_assertion_passes_provenance() -> None:
    with tempfile.TemporaryDirectory() as raw:
        world = Path(raw) / "world.sqlite"
        tv = TaskView(str(world), view_id="diligence-world")
        tv.declare_relation(
            "identity_judgment",
            [Role("left", RoleType.TEXT), Role("right", RoleType.TEXT), Role("disposition", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.assert_tuple(
            "identity_judgment",
            {"left": "a", "right": "b", "disposition": "UNRESOLVED"},
            grounding=[Grounding(GroundingKind.SOURCE, "sources/notes.md", "paragraph 1")],
        )
        payload = validate_provenance(world)
        assert payload["ok"] is True
        assert payload["ungrounded_count"] == 0


def test_distinct_not_established_downgrades() -> None:
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        (workspace / "04_packets").mkdir()
        packet = {
            "obligation_id": "obl-1",
            "selected_observations": [
                {"source_path": "sources/registry.csv", "location": "row 1", "excerpt": "LLC vs Inc"}
            ],
        }
        (workspace / "04_packets" / "obl-1.json").write_text(json.dumps(packet) + "\n")
        (workspace / "05_dispositions.json").write_text(
            json.dumps(
                [
                    {
                        "obligation_id": "obl-1",
                        "relation": "identity_judgment",
                        "values": {"left": "billing:X Inc.", "right": "registry:1"},
                        "disposition": "DISTINCT",
                        "supporting_evidence": [{"source_path": "sources/registry.csv", "location": "row 1"}],
                        "support_claim": "Inc vs LLC",
                    },
                    {
                        "obligation_id": "obl-2",
                        "relation": "identity_judgment",
                        "values": {"left": "crm:A", "right": "billing:A"},
                        "disposition": "SAME_ENTITY",
                        "supporting_evidence": [{"source_path": "sources/notes.md", "location": "p1"}],
                        "support_claim": "same legal entity",
                    },
                ]
            )
        )
        (workspace / "04_packets" / "obl-2.json").write_text(
            json.dumps({"obligation_id": "obl-2", "selected_observations": [{"source_path": "sources/notes.md", "location": "p1", "excerpt": "same legal entity"}]})
        )

        def gate(**kwargs):
            left = kwargs["candidate"]["left"]
            if left.startswith("billing:"):
                return {"result": "NOT_ESTABLISHED", "reason": "attribute mismatch"}
            return {"result": "SUPPORTED_DISTINCT", "reason": "unused"}

        audit = admit_workspace(workspace, gate=gate)
        rows = json.loads((workspace / "05_dispositions.json").read_text())
        by_id = {row["obligation_id"]: row for row in rows}
        assert by_id["obl-1"]["disposition"] == "UNRESOLVED"
        assert by_id["obl-2"]["disposition"] == "SAME_ENTITY"
        distinct_audit = [row for row in audit if row["packet"] == "obl-1"][0]
        assert distinct_audit["final_disposition"] == "UNRESOLVED"


def test_supported_distinct_retained() -> None:
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        (workspace / "04_packets").mkdir()
        (workspace / "04_packets" / "obl-d.json").write_text(
            json.dumps(
                {
                    "obligation_id": "obl-d",
                    "selected_observations": [
                        {"source_path": "sources/notes.md", "location": "p1", "excerpt": "is a different company"}
                    ],
                }
            )
        )
        (workspace / "05_dispositions.json").write_text(
            json.dumps(
                [
                    {
                        "obligation_id": "obl-d",
                        "relation": "identity_judgment",
                        "values": {"left": "crm:HEL-441", "right": "registry:11847299"},
                        "disposition": "DISTINCT",
                        "supporting_evidence": [{"source_path": "sources/notes.md", "location": "p1"}],
                        "support_claim": "explicit distinct company",
                    }
                ]
            )
        )

        def gate(**kwargs):
            return {"result": "SUPPORTED_DISTINCT", "reason": "explicit exclusion"}

        admit_workspace(workspace, gate=gate)
        rows = json.loads((workspace / "05_dispositions.json").read_text())
        assert rows[0]["disposition"] == "DISTINCT"


def test_unbound_abi_does_not_exact_project() -> None:
    from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.projector import (
        write_workspace_outputs,
    )

    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        (workspace / "01_vocabulary.json").write_text(
            json.dumps(
                {
                    "relations": [
                        {
                            "name": "contract_record",
                            "roles": [
                                {"name": "contract_id", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                            ],
                        }
                    ]
                }
            )
        )
        payload = write_workspace_outputs(workspace)
        assert payload["a"]["abi_status"] == "INCOMPLETE_PURPOSE"
        assert payload["a"]["invoices"] == []
        assert "active" in payload["a"]["unsatisfied"]
        assert json.loads((workspace / "08_outputs" / "a.json").read_text())["abi_status"] == "INCOMPLETE_PURPOSE"


def test_parse_gate_fail_closed() -> None:
    assert parse_gate_result("")["result"] == "NOT_ESTABLISHED"
    assert parse_gate_result('{"result": "SUPPORTED_DISTINCT", "reason": "ok"}')["result"] == "SUPPORTED_DISTINCT"


if __name__ == "__main__":
    test_unbound_required_identity_is_unsatisfied()
    test_ungrounded_world_assertion_fails_provenance()
    test_grounded_world_assertion_passes_provenance()
    test_distinct_not_established_downgrades()
    test_supported_distinct_retained()
    test_unbound_abi_does_not_exact_project()
    test_parse_gate_fail_closed()
    print("ok")
