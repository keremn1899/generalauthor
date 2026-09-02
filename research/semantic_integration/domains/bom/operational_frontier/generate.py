"""Oracle-free operational frontier from C1 plus a declared purpose.

Inputs are a compiled TaskView and the frozen purpose contract only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from taskview import TaskView


GENERATION_RULE_VERSION = "viable-replacement-candidate-context-v1"

PURPOSE = {
    "id": "viable_replacement",
    "revision": 1,
    "statement": (
        "Determine viable replacement options for the represented BOM "
        "replacement cases."
    ),
    "required_relation": "acceptable_replacement",
    "rule": (
        "Each mechanically compiled candidate_replacement(new_part, old_part) "
        "together with each deployment_environment of a BOM item whose required "
        "part_type matches both parts demands acceptable_replacement(new_part, "
        "old_part, context) before a viable-replacement answer is established."
    ),
}


def demanded_cases(view: TaskView) -> list[dict[str, str]]:
    """Replacement candidate/context pairs required by the frozen purpose."""

    rows = view.query(
        """
        SELECT DISTINCT
            cr.new_part_id AS new_part,
            cr.old_part_id AS old_part,
            de.environment_id AS context
        FROM candidate_replacement AS cr
        JOIN part_type AS new_type ON new_type.part_id = cr.new_part_id
        JOIN part_type AS old_type
          ON old_type.part_id = cr.old_part_id
         AND old_type.part_type = new_type.part_type
        JOIN requires_type AS required
          ON required.part_type = new_type.part_type
        JOIN deployment_environment AS de
          ON de.bom_item_id = required.bom_item_id
        ORDER BY new_part, old_part, context
        """
    )
    return [
        {
            "new_part": row["new_part"],
            "old_part": row["old_part"],
            "context": row["context"],
        }
        for row in rows
    ]


def established_acceptable_replacement(view: TaskView) -> set[tuple[str, str, str]]:
    return {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in view.query(
            """
            SELECT new_part_id, old_part_id, context_id
            FROM acceptable_replacement
            """
        )
    }


def generate_obligations(
    view: TaskView,
    purpose: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Emit semantic demand that current compiled state does not establish.

    Inputs are a compiled TaskView and the frozen purpose.  This function has
    no evaluation-oracle parameter.
    """

    contract = purpose or PURPOSE
    established = established_acceptable_replacement(view)
    obligations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for case in demanded_cases(view):
        key = (case["new_part"], case["old_part"], case["context"])
        if key in seen:
            continue
        seen.add(key)
        if key in established:
            continue
        obligations.append(
            {
                "relation": contract["required_relation"],
                "values": {
                    "new_part": case["new_part"],
                    "old_part": case["old_part"],
                    "context": case["context"],
                },
                "demanded_by": {
                    "kind": "purpose",
                    "name": contract["id"],
                    "revision": contract["revision"],
                },
            }
        )
    return obligations


def operational_frontier_document(
    view: TaskView,
    purpose: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = purpose or PURPOSE
    cases = demanded_cases(view)
    obligations = generate_obligations(view, purpose=contract)
    pairs = view.query(
        "SELECT new_part_id, old_part_id FROM candidate_replacement"
    )
    return {
        "purpose": {
            "id": contract["id"],
            "revision": contract["revision"],
            "statement": contract["statement"],
        },
        "generation_rule_version": GENERATION_RULE_VERSION,
        "generation_rule": contract["rule"],
        "c1_world_revision": view.revision,
        "candidate_replacement_pairs": len(pairs),
        "candidate_case_count": len(cases),
        "obligation_count": len(obligations),
        "obligations": obligations,
        "provider_inference_calls": 0,
        "inputs": ["compiled_c1_taskview", "purpose_contract"],
    }


def fingerprint(document: dict[str, Any]) -> str:
    body = {key: value for key, value in document.items() if key != "fingerprint"}
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def freeze_operational_frontier(view: TaskView, path: Path) -> dict[str, Any]:
    document = operational_frontier_document(view)
    digest = fingerprint(document)
    document = {**document, "fingerprint": digest}
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    path.with_name(path.name + ".sha256").write_text(digest + "\n", encoding="utf-8")
    return document
