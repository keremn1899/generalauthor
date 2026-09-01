from research.abstraction_frontier.oracle import evaluate


def _view():
    entities = [{"id": x, "kind": x.split(":")[0]} for x in ["module:a", "module:b", "module:c", "test:t"]]
    facts = [
        {"id": "r1", "subject": "module:a", "predicate": "depends_on", "object": "module:b"},
        {"id": "r2", "subject": "module:b", "predicate": "depends_on", "object": "module:c"},
        {"id": "r3", "subject": "test:t", "predicate": "verifies", "object": "module:b"},
    ]
    return {"entities": entities, "facts": facts}


def test_neutral_oracle_operations():
    result = evaluate(_view(), {"derive": {
        "a": {"op": "resolve", "references": "module:a"},
        "downstream": {"op": "traverse", "from": "$a", "predicates": ["depends_on"], "max_depth": 2},
        "tests": {"op": "reverse_reachable", "from": "module:b", "predicates": ["verifies"], "max_depth": 1},
        "seq": {"op": "sequence", "from": "$a", "predicates": ["depends_on", "depends_on"]},
        "both": {"op": "intersection", "inputs": ["$downstream", "$seq"]},
        "remaining": {"op": "difference", "left": "$downstream", "right": "$seq"},
        "merged": {"op": "union", "inputs": ["$tests", "$remaining"]},
        "paths": {"op": "path_targets", "from": "$a", "to": ["module:c"], "predicates": ["depends_on"], "max_depth": 2},
    }, "answers": ["both", "merged", "paths"]})
    assert result.answers == {"both": ["module:c"], "merged": ["module:b", "test:t"], "paths": ["module:c"]}
