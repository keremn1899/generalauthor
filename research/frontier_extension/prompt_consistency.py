"""Substrate-neutral prompt/output and constrained-oracle consistency checks."""
from __future__ import annotations

from collections import deque
from typing import Any


def output_consistency(metadata: dict[str, Any], oracle: dict[str, Any]) -> dict[str, bool]:
    """Check the three output contracts independently of either treatment."""
    requested = metadata.get("participant_requested_outputs", [])
    answers = list(oracle.get("answers", {}))
    grader = list(oracle.get("grader_expected_outputs", {}))
    # JSON objects are unordered contracts.  Candidate artifacts are written
    # with sorted keys, so semantic agreement must not depend on serialization
    # order; duplicate requested names remain invalid.
    requested_names = set(requested)
    answer_names = set(answers)
    grader_names = set(grader)
    return {
        "prompt_oracle": len(requested) == len(requested_names) and requested_names == answer_names,
        "oracle_grader": answer_names == grader_names,
        "prompt_grader": len(requested) == len(requested_names) and requested_names == grader_names,
    }


def answer_cardinality_gate(oracle: dict[str, Any], maximum: int = 6) -> dict[str, Any]:
    """Apply the frozen *per named answer set* cardinality rule."""
    cardinalities = {name: len(values) for name, values in oracle["answers"].items()}
    return {"per_named_output": cardinalities, "maximum": maximum,
            "passed": all(value <= maximum for value in cardinalities.values())}


def fx04_neutral_oracle(facts: list[dict[str, str]], seed: str, production: str, max_depth: int) -> list[str]:
    """Return qualifying services without using a SQL or Graphauthor projection.

    A candidate is eligible when it is reachable through the bounded incoming
    dependency scope, implements a scoped module, is deployed to production,
    and has no ``crosses_deprecated`` relation.  This is deliberately a plain
    fact evaluator so it validates the neutral-oracle condition independently
    of either treatment representation.
    """
    incoming: dict[str, list[str]] = {}
    for fact in facts:
        if fact["predicate"] == "depends_on":
            incoming.setdefault(fact["object"], []).append(fact["subject"])
    queue = deque([(seed, 0)])
    scoped = {seed}
    while queue:
        node, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for child in incoming.get(node, []):
            if child not in scoped:
                scoped.add(child)
                queue.append((child, depth + 1))
    implements = {fact["subject"]: fact["object"] for fact in facts if fact["predicate"] == "implements"}
    production_services = {fact["subject"] for fact in facts if fact["predicate"] == "deployed_to" and fact["object"] == production}
    rejected = {fact["subject"] for fact in facts if fact["predicate"] == "crosses_deprecated"}
    return sorted(service for service, module in implements.items()
                  if module in scoped and service in production_services and service not in rejected)
