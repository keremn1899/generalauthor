"""Evaluator-only taxonomy; never copy this module into participant workspaces."""
from __future__ import annotations

OPERATION_TAXONOMY = {
    "op-01": "inverse_lookup", "op-02": "fan_out", "op-03": "fan_out",
    "op-04": "inverse_lookup", "op-05": "join_set_difference",
    "op-06": "join_intersection", "op-07": "bounded_path",
    "op-08": "join_set_intersection",
}


def taxonomy_for_oracle(oracle: dict) -> list[dict[str, str]]:
    return [{"operation_id": row["id"], "dominant_relational_shape": OPERATION_TAXONOMY[row["id"]]} for row in oracle["operations"]]
