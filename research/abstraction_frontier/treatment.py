"""Frozen experiment-only graph-treatment conformance policy.

This module does not alter Graphauthor's product vocabulary.  It constrains
only the adapter used by the frontier experiment, whose public graph surface
has deliberately excluded search and structural/semantic enrichments.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


TREATMENT_VERSION = "frontier-g-v1-conformance-1"
GRAPH_SURFACE = (
    "describe", "lookup", "expand", "path", "run_ephemeral_traversal",
)
# Recipe operations whose information source is only the frozen canonical
# facts.  `search` and `select_landmarks` are product-valid operations but are
# expressly not valid in this experiment.
ALLOWED_EPHEMERAL_OPS = frozenset({
    "lookup", "traverse", "expand", "shortest_path", "find_paths",
    "walk_sequence", "filter", "sort", "limit", "union", "difference",
    "intersection",
})
EXCLUDED_EPHEMERAL_OPS = frozenset({"search", "select_landmarks"})


class ExcludedEphemeralOperation(ValueError):
    """A program attempts an operation excluded by the frozen treatment."""


def validate_frozen_ephemeral_program(program: dict[str, Any]) -> None:
    """Fail closed before graph construction or program compilation.

    Programs may contain primary `steps` and contingency `then` steps.  Every
    operation is checked; unknown operations are excluded too, rather than
    relying on the product compiler to reject them after surface entry.
    """
    if not isinstance(program, dict):
        return  # The product compiler retains its existing invalid-program error.
    for section in ("steps", "then"):
        steps = program.get(section, [])
        if not isinstance(steps, list):
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            op = str(step.get("op") or "")
            if op not in ALLOWED_EPHEMERAL_OPS:
                reason = "explicitly excluded" if op in EXCLUDED_EPHEMERAL_OPS else "not in the frozen vocabulary"
                raise ExcludedEphemeralOperation(
                    f"EXCLUDED_EPHEMERAL_OPERATION: {section}[{index}].op={op!r} is {reason}"
                )


def treatment_fingerprint() -> str:
    payload = {
        "version": TREATMENT_VERSION,
        "graph_surface": GRAPH_SURFACE,
        "allowed_ephemeral_ops": sorted(ALLOWED_EPHEMERAL_OPS),
        "excluded_ephemeral_ops": sorted(EXCLUDED_EPHEMERAL_OPS),
        "minimal_contract": True,
        "forbidden_information_sources": [
            "lexical_search", "semantic_vector_search", "landmarks",
            "structural_profiles", "compass", "all_node_scan",
            "source_content", "inferred_or_closure_edges", "raw_cypher",
            "named_default_required_traversals",
        ],
    }
    return "fgt_" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
