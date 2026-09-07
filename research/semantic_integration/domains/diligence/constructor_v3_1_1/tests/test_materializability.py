"""Deterministic regression tests for negative controls N1–N4.

N1 — no binding: required field exists, no semantic_identity / field_source binding
     Expected: UNSATISFIED, reason = NO_BINDING.
N2 — declared but not materializable: required field has semantic_identity but World contains no valid route to materialize it
     Expected: UNSATISFIED, reason = NOT_MATERIALIZABLE.
N3 — declared and materializable:
     Expected: SATISFIED and normalizer actually emits the required consumer relation/field.
N4 — ambiguous realization: two incompatible mappings could satisfy the same required semantic field without disambiguation
     Expected: AMBIGUOUS. Do not choose one by name similarity.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from taskview import Grounding, GroundingKind, RelationMode, Role, RoleType, TaskView

from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.abi_completeness import (
    check_abi,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.normalizer import (
    normalize_world,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.projector import (
    write_workspace_outputs,
)


def test_n1_no_binding() -> None:
    """N1 — no binding: required field exists, no semantic_identity / field_source binding."""
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
                                # counterparty_text role is completely missing
                            ],
                        }
                    ]
                }
            )
        )
        payload = check_abi(path)
        assert payload["fields"]["counterparty_text"]["status"] == "UNSATISFIED"
        assert payload["fields"]["counterparty_text"]["reason"] == "NO_BINDING"
        assert "counterparty_text" in payload["unsatisfied"]
        assert payload["ok"] is False


def test_n2_declared_but_not_materializable() -> None:
    """N2 — declared but not materializable:
    required field has semantic_identity, but World contains no valid route to materialize it.
    """
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        vocab_path = workspace / "01_vocabulary.json"
        world_path = workspace / "06_world" / "world.sqlite"
        world_path.parent.mkdir(parents=True)

        vocab_path.write_text(
            json.dumps(
                {
                    "relations": [
                        {
                            "name": "contract_record",
                            "roles": [
                                {"name": "contract_id", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                            ],
                        },
                        {
                            "name": "contract_lifecycle",
                            "roles": [
                                {"name": "contract", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "active", "type": "BOOLEAN", "semantic_identity": "active"},
                            ],
                        },
                    ]
                }
            )
        )

        tv = TaskView(str(world_path), view_id="diligence-world")
        tv.declare_relation(
            "contract_record",
            [Role("contract_id", RoleType.TEXT), Role("party", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.declare_relation(
            "contract_lifecycle",
            [Role("contract", RoleType.TEXT), Role("active", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.assert_tuple(
            "contract_record",
            {"contract_id": "contract:1", "party": "Acme Corp"},
            grounding=[Grounding(GroundingKind.SOURCE, "sources/contracts.md", "p1")],
        )
        # contract_lifecycle has 0 tuples asserted, matching frozen v3.1 T3 failure mode

        payload = check_abi(vocab_path, world_path=world_path)
        assert payload["fields"]["active"]["status"] == "UNSATISFIED"
        assert payload["fields"]["active"]["reason"] == "NOT_MATERIALIZABLE"
        assert "active" in payload["unsatisfied"]
        assert payload["fields"]["counterparty_text"]["status"] == "SATISFIED"
        assert payload["fields"]["counterparty_text"]["reason"] is None
        assert payload["ok"] is False

        # Verify projector fails to INCOMPLETE_PURPOSE rather than silent downstream drop
        proj_out = write_workspace_outputs(workspace)
        assert proj_out["a"]["abi_status"] == "INCOMPLETE_PURPOSE"
        assert "active" in proj_out["a"]["unsatisfied"]


def test_n3_declared_and_materializable() -> None:
    """N3 — declared and materializable:
    Expected: SATISFIED and normalizer actually emits the required consumer relation/field.
    """
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        vocab_path = workspace / "01_vocabulary.json"
        world_path = workspace / "06_world" / "world.sqlite"
        world_path.parent.mkdir(parents=True)

        vocab_path.write_text(
            json.dumps(
                {
                    "relations": [
                        {
                            "name": "contract_record",
                            "roles": [
                                {"name": "contract_id", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                            ],
                        },
                        {
                            "name": "contract_lifecycle",
                            "roles": [
                                {"name": "contract", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "active", "type": "BOOLEAN", "semantic_identity": "active"},
                            ],
                        },
                    ]
                }
            )
        )

        tv = TaskView(str(world_path), view_id="diligence-world")
        tv.declare_relation(
            "contract_record",
            [Role("contract_id", RoleType.TEXT), Role("party", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.declare_relation(
            "contract_lifecycle",
            [Role("contract", RoleType.TEXT), Role("active", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.assert_tuple(
            "contract_record",
            {"contract_id": "contract:1", "party": "Acme Corp"},
            grounding=[Grounding(GroundingKind.SOURCE, "sources/contracts.md", "p1")],
        )
        tv.assert_tuple(
            "contract_lifecycle",
            {"contract": "contract:1", "active": "1"},
            grounding=[Grounding(GroundingKind.SOURCE, "sources/contracts.md", "p2")],
        )

        payload = check_abi(vocab_path, world_path=world_path)
        assert payload["fields"]["active"]["status"] == "SATISFIED"
        assert payload["fields"]["active"]["reason"] is None
        assert payload["fields"]["counterparty_text"]["status"] == "SATISFIED"
        assert payload["fields"]["counterparty_text"]["reason"] is None

        # Verify normalizer actually emits the canonical relations/fields
        norm = normalize_world(world_path, vocabulary=vocab_path)
        assert "contract_active" in norm["consumer_relations_recovered"]
        assert len(norm["tables"]["contract_active"]) == 1
        assert norm["tables"]["contract_active"][0]["active"] is True
        assert norm["tables"]["contract_active"][0]["contract_id"] == "contract:1"


def test_n4_ambiguous_realization() -> None:
    """N4 — ambiguous realization:
    If two incompatible mappings could satisfy the same required semantic field and the current contract does not disambiguate:
    Expected: AMBIGUOUS. Do not choose one by name similarity.
    """
    with tempfile.TemporaryDirectory() as raw:
        workspace = Path(raw)
        vocab_path = workspace / "01_vocabulary.json"
        world_path = workspace / "06_world" / "world.sqlite"
        world_path.parent.mkdir(parents=True)

        vocab_path.write_text(
            json.dumps(
                {
                    "relations": [
                        {
                            "name": "contract_record",
                            "roles": [
                                {"name": "contract_id", "type": "TEXT", "semantic_identity": "contract_id"},
                                {"name": "primary_party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                                {"name": "secondary_party", "type": "TEXT", "semantic_identity": "counterparty_text"},
                            ],
                        }
                    ]
                }
            )
        )

        tv = TaskView(str(world_path), view_id="diligence-world")
        tv.declare_relation(
            "contract_record",
            [Role("contract_id", RoleType.TEXT), Role("primary_party", RoleType.TEXT), Role("secondary_party", RoleType.TEXT)],
            mode=RelationMode.BASE,
        )
        tv.assert_tuple(
            "contract_record",
            {"contract_id": "contract:1", "primary_party": "Acme", "secondary_party": "Beta"},
            grounding=[Grounding(GroundingKind.SOURCE, "sources/contracts.md", "p1")],
        )

        payload = check_abi(vocab_path, world_path=world_path)
        assert payload["fields"]["counterparty_text"]["status"] == "AMBIGUOUS"
        assert payload["fields"]["counterparty_text"]["reason"] == "AMBIGUOUS"
        assert "counterparty_text" in payload["ambiguous"]
        assert payload["ok"] is False

        # Verify normalizer refuses to arbitrarily choose one by name similarity
        norm = normalize_world(world_path, vocabulary=vocab_path)
        assert len(norm["ambiguous_interface_mappings"]) > 0


if __name__ == "__main__":
    test_n1_no_binding()
    test_n2_declared_but_not_materializable()
    test_n3_declared_and_materializable()
    test_n4_ambiguous_realization()
    print("All negative controls N1-N4 passed successfully.")
