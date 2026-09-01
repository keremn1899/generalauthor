from __future__ import annotations

import json
from pathlib import Path

from research.relational_materialization.generator import make_world, operations, write_case
from research.relational_materialization.model import Arm, Cell, Heterogeneity, Novelty
from research.relational_materialization.runner import (
    _assert_prompt_isolation,
    _cursor_usage,
    _verify_arm,
    participant_prompt,
    reference_command,
    run_case,
    score_response,
)


def test_paired_renderings_preserve_oracle_answers(tmp_path: Path):
    world = make_world(7)
    assert operations(world, Novelty.STANDARD, 1)[0].answer_ids == operations(world, Novelty.STANDARD, 8)[0].answer_ids
    h0 = write_case(tmp_path, Cell(Heterogeneity.PRESTRUCTURED, Novelty.TASK_SPECIFIC, 1), 7)
    h2 = write_case(tmp_path, Cell(Heterogeneity.MIXED, Novelty.TASK_SPECIFIC, 1), 7)
    first = json.loads((h0 / "evaluator" / "oracle.json").read_text())["operations"][0]["answer_ids"]
    second = json.loads((h2 / "evaluator" / "oracle.json").read_text())["operations"][0]["answer_ids"]
    assert first == second
    visible_workload = json.loads((h0 / "agent" / "workload.json").read_text())
    assert all("answer_ids" not in operation for operation in visible_workload["operations"])


def test_r8_is_a_coherent_non_duplicate_prefix_workload():
    ops = operations(make_world(7), Novelty.TASK_SPECIFIC, 8)
    assert [op.id for op in operations(make_world(7), Novelty.TASK_SPECIFIC, 4)] == [op.id for op in ops[:4]]
    assert len({op.relation for op in ops}) == 8
    assert len({op.prompt for op in ops}) == 8


def test_relation_store_path_is_normalized_against_run_root(tmp_path: Path):
    workspace = tmp_path / "run" / "workspace"
    workspace.mkdir(parents=True)
    store = workspace / "relation_store.sqlite"
    import sqlite3
    with sqlite3.connect(store) as connection:
        connection.execute("CREATE TABLE entities (id TEXT)")
        connection.execute("CREATE TABLE relations (source TEXT)")
    assert not _verify_arm(Arm.RELATION_STORE, workspace, workspace.parent, {
        "artifacts": {"representation_path": "workspace/relation_store.sqlite"}
    })
    assert not _verify_arm(Arm.RELATION_STORE, workspace, workspace.parent, {
        "artifacts": {"representation_path": str(store)}
    })


def test_generic_relation_store_rejects_declared_graphauthor_use(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    assert "forbidden_graphauthor_artifact" in _verify_arm(Arm.RELATION_STORE, workspace, tmp_path, {
        "artifacts": {"graphauthor_workbook": ".graphauthor"}
    })


def test_a_and_b_prompts_have_no_treatment_disclosure(tmp_path: Path):
    forbidden = ("graphauthor", ".graphauthor", "graph.lbug", "workbook", "build.py")
    for arm in (Arm.ORDINARY, Arm.RELATION_STORE):
        prompt = participant_prompt(arm, tmp_path / "response.json")
        _assert_prompt_isolation(arm, prompt)
        assert not any(term in prompt.lower() for term in forbidden)
    assert "Graphauthor" in participant_prompt(Arm.GRAPHAUTHOR_FORCED, tmp_path / "response.json")
    assert "optional" in participant_prompt(Arm.GRAPHAUTHOR_OPTIONAL, tmp_path / "response.json").lower()


def test_actual_workspace_graphauthor_artifact_invalidates_a_or_b(tmp_path: Path):
    workspace = tmp_path / "workspace"
    (workspace / ".graphauthor" / "out").mkdir(parents=True)
    (workspace / ".graphauthor" / "out" / "encoding.json").write_text("{}")
    symptoms = _verify_arm(Arm.ORDINARY, workspace, tmp_path, {"artifacts": {}})
    assert "forbidden_graphauthor_artifact" in symptoms


def test_repair_attempt_preserves_original_and_uses_saved_prompt(tmp_path: Path):
    case = write_case(tmp_path / "cases", Cell(Heterogeneity.PRESTRUCTURED, Novelty.TASK_SPECIFIC, 1), 3)
    first = run_case(case, Arm.ORDINARY, reference_command(), tmp_path / "results", timeout=20)
    original_prompt = tmp_path / "results" / case.name / "A" / "participant_prompt.txt"
    repair = run_case(
        case, Arm.ORDINARY, reference_command(), tmp_path / "results", timeout=20,
        attempt_id="attempt-2", prompt_path_override=original_prompt,
    )
    assert first["attempt_id"] == "attempt-1"
    assert repair["attempt_id"] == "attempt-2"
    assert (tmp_path / "results" / case.name / "A" / "record.json").is_file()
    assert (tmp_path / "results" / case.name / "A" / "attempt-2" / "record.json").is_file()


def test_scoring_penalises_missing_and_extra_answers():
    oracle = {"operations": [{"id": "op-01", "answer_ids": ["a", "b"]}]}
    score = score_response(oracle, {"answers": [{"operation_id": "op-01", "answer_ids": ["a", "x"]}]})
    assert score.answer_precision == score.answer_recall == 0.5
    assert score.workload_success == 0.0


def test_cursor_stream_usage_is_retained():
    stdout = '{"type":"result","usage":{"inputTokens":12,"outputTokens":3}}\n'
    assert _cursor_usage(stdout) == {"inputTokens": 12, "outputTokens": 3}


def test_reference_smoke_satisfies_all_arm_contracts(tmp_path: Path):
    case = write_case(tmp_path / "cases", Cell(Heterogeneity.MIXED, Novelty.TASK_SPECIFIC, 1), 3)
    command = reference_command()
    for arm in Arm:
        record = run_case(case, arm, command, tmp_path / "results", timeout=20)
        assert record["returncode"] == 0
        assert record["workload_success"] == 1.0
        assert not record["symptoms"]
