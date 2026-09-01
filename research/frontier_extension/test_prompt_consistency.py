from research.frontier_extension.prompt_consistency import (
    answer_cardinality_gate,
    fx04_neutral_oracle,
    output_consistency,
)


def fact(subject, predicate, object):
    return {"subject": subject, "predicate": predicate, "object": object}


def test_output_contract_requires_exact_three_way_output_agreement():
    metadata = {"participant_requested_outputs": ["affected"]}
    oracle = {"answers": {"affected": ["service:a"]}, "grader_expected_outputs": {"affected": ["service:a"]}}
    assert all(output_consistency(metadata, oracle).values())
    oracle["grader_expected_outputs"] = {"other": []}
    assert not all(output_consistency(metadata, oracle).values())


def test_output_contract_is_not_changed_by_json_object_key_sorting():
    metadata = {"participant_requested_outputs": ["services", "deployments"]}
    oracle = {"answers": {"deployments": ["deployment:p"], "services": ["service:s"]},
              "grader_expected_outputs": {"deployments": ["deployment:p"], "services": ["service:s"]}}
    assert all(output_consistency(metadata, oracle).values())


def test_cardinality_gate_is_per_named_answer_set_not_aggregate():
    oracle = {"answers": {"affected": [str(i) for i in range(6)], "uncovered": [str(i) for i in range(6)]}}
    assert answer_cardinality_gate(oracle)["passed"]


def test_fx04_neutral_oracle_rejects_only_forbidden_predicate_near_miss():
    facts = [
        fact("module:allow", "depends_on", "package:legacy"),
        fact("module:reject", "depends_on", "package:legacy"),
        fact("service:allow", "implements", "module:allow"),
        fact("service:reject", "implements", "module:reject"),
        fact("service:allow", "deployed_to", "deployment:prod"),
        fact("service:reject", "deployed_to", "deployment:prod"),
        fact("service:reject", "crosses_deprecated", "boundary:deprecated"),
    ]
    assert fx04_neutral_oracle(facts, "package:legacy", "deployment:prod", 2) == ["service:allow"]
