"""Neutral, deterministic evaluator for frozen canonical engineering facts.

The small data language in this module intentionally has no SQL, Cypher, or
Graphauthor syntax.  A query is a dictionary of named relational derivations;
the evaluator is only an oracle and is never exposed to participants.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleResult:
    answers: dict[str, list[str]]
    used_relation_ids: list[str]
    variables: dict[str, list[str]]


def _as_set(value: Any, variables: dict[str, set[str]]) -> set[str]:
    if isinstance(value, str) and value.startswith("$"):
        return set(variables.get(value[1:], set()))
    if isinstance(value, list):
        out: set[str] = set()
        for item in value:
            out |= _as_set(item, variables)
        return out
    return {str(value)} if value is not None else set()


def evaluate(view: dict[str, Any], query: dict[str, Any]) -> OracleResult:
    """Evaluate all named derivations and return exact, sorted answer sets."""
    facts = list(view["facts"])
    kinds = {str(entity["id"]): str(entity["kind"]) for entity in view["entities"]}
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        outgoing[str(fact["subject"])].append(fact)
        incoming[str(fact["object"])].append(fact)
    variables: dict[str, set[str]] = {}
    used: set[str] = set()

    def eligible(fact: dict[str, Any], predicates: set[str]) -> bool:
        return not predicates or str(fact["predicate"]) in predicates

    def traverse(seeds: set[str], predicates: set[str], direction: str, depth: int,
                 endpoint_kind: str | None = None) -> set[str]:
        frontier, seen, result = set(seeds), set(seeds), set()
        for _ in range(depth):
            next_nodes: set[str] = set()
            for node in frontier:
                rows = ([] if direction == "incoming" else outgoing[node]) + ([] if direction == "outgoing" else incoming[node])
                for fact in rows:
                    if not eligible(fact, predicates):
                        continue
                    target = str(fact["object"] if fact["subject"] == node else fact["subject"])
                    used.add(str(fact["id"]))
                    if target not in seen:
                        seen.add(target); next_nodes.add(target)
                    if endpoint_kind is None or kinds.get(target) == endpoint_kind:
                        result.add(target)
            frontier = next_nodes
            if not frontier:
                break
        return result

    def sequence(seeds: set[str], predicates: list[str], direction: str) -> set[str]:
        current = set(seeds)
        for predicate in predicates:
            current = traverse(current, {predicate}, direction, 1)
        return current

    def path_exists(sources: set[str], targets: set[str], predicates: set[str], direction: str,
                    max_depth: int) -> set[str]:
        found: set[str] = set()
        for source in sources:
            queue: deque[tuple[str, int]] = deque([(source, 0)])
            seen = {source}
            while queue:
                node, depth = queue.popleft()
                if node in targets and node != source:
                    found.add(node); break
                if depth == max_depth:
                    continue
                rows = ([] if direction == "incoming" else outgoing[node]) + ([] if direction == "outgoing" else incoming[node])
                for fact in rows:
                    if not eligible(fact, predicates):
                        continue
                    other = str(fact["object"] if fact["subject"] == node else fact["subject"])
                    used.add(str(fact["id"]))
                    if other not in seen:
                        seen.add(other); queue.append((other, depth + 1))
        return found

    for name, expr in query.get("derive", {}).items():
        op = str(expr["op"])
        if op == "resolve":
            variables[name] = _as_set(expr["references"], variables)
        elif op in {"traverse", "reverse_reachable"}:
            direction = "incoming" if op == "reverse_reachable" else str(expr.get("direction", "outgoing"))
            variables[name] = traverse(_as_set(expr["from"], variables), set(expr.get("predicates", [])), direction,
                                       int(expr.get("max_depth", 1)), expr.get("endpoint_kind"))
        elif op == "sequence":
            variables[name] = sequence(_as_set(expr["from"], variables), list(expr["predicates"]), str(expr.get("direction", "outgoing")))
        elif op == "union":
            variables[name] = _as_set(expr["inputs"], variables)
        elif op == "intersection":
            inputs = [_as_set(item, variables) for item in expr["inputs"]]
            variables[name] = set.intersection(*inputs) if inputs else set()
        elif op == "difference":
            variables[name] = _as_set(expr["left"], variables) - _as_set(expr["right"], variables)
        elif op == "path_targets":
            variables[name] = path_exists(_as_set(expr["from"], variables), _as_set(expr["to"], variables),
                                          set(expr.get("predicates", [])), str(expr.get("direction", "outgoing")),
                                          int(expr.get("max_depth", 4)))
        else:
            raise ValueError(f"unknown neutral operation: {op}")
    answers = {str(name): sorted(variables.get(str(name), set())) for name in query.get("answers", [])}
    return OracleResult(answers=answers, used_relation_ids=sorted(used),
                        variables={key: sorted(value) for key, value in variables.items()})
