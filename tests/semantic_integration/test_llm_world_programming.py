from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.bom.llm_world_programming.prompts import (
    participant_prompt,
)
from research.semantic_integration.domains.bom.llm_world_programming.scorer import (
    classify_failure,
    load_expected,
    schema_valid,
    score_run,
    strip_support,
)
from research.semantic_integration.domains.bom.llm_world_programming.workspaces import (
    build_raw_workspace,
    build_world_workspace,
    forbidden_paths_present,
    freeze_world_fixture,
)


def test_workspaces_are_physically_isolated(tmp_path):
    freeze_world_fixture()
    raw = tmp_path / "raw"
    world = tmp_path / "world"
    build_raw_workspace(raw)
    build_world_workspace(world)
    assert (raw / "sources" / "manufacturer.csv").exists()
    assert not (world / "sources").exists()
    assert not list(world.rglob("manufacturer.csv"))
    assert (world / "world.sqlite").exists()
    assert not (raw / "world.sqlite").exists()
    api = (world / "WORLD_API.md").read_text(encoding="utf-8")
    assert "eligible_part" not in api
    assert "acceptable_replacement" not in api
    assert forbidden_paths_present(raw, "raw") == []
    assert forbidden_paths_present(world, "world") == []
    assert "indoor_panel" not in (raw / "README.md").read_text(encoding="utf-8")
    assert "indoor_panel" not in (world / "README.md").read_text(encoding="utf-8")


def test_prompts_do_not_name_expected_tuples_or_solution_relations():
    for condition in ("raw", "world"):
        for task_id in ("analysis_a", "analysis_b", "analysis_c"):
            prompt = participant_prompt(condition, task_id)
            assert "part:X110" not in prompt
            assert "part:X100" not in prompt
            assert "eligible_part" not in prompt
            assert "manufacturer_part_number" not in prompt
            assert "oracle" not in prompt.lower()


def test_scorer_accepts_expected_payload_and_flags_unknown_as_false(tmp_path):
    freeze_world_fixture()
    expected = load_expected("analysis_a")
    workspace = tmp_path / "trial"
    workspace.mkdir()
    payload = json.dumps(expected)
    (workspace / "analysis.py").write_text(
        "from pathlib import Path\n"
        f"Path('output.json').write_text({payload!r}, encoding='utf-8')\n",
        encoding="utf-8",
    )
    scored = score_run(
        condition="raw",
        task_id="analysis_a",
        trial_dir=workspace,
        clean_root=tmp_path / "clean",
    )
    assert scored["pass"] is True
    mutated = json.loads(json.dumps(expected))
    mutated["cases"][1]["semantic_state"] = "rejected"
    mutated["cases"][1]["epistemic"] = "FALSE"
    assert (
        classify_failure(
            task_id="analysis_a",
            expected=expected,
            actual=mutated,
            executes=True,
            parses=True,
            schema_valid=True,
            exact=False,
        )
        == "UNKNOWN_AS_FALSE"
    )
    assert schema_valid("analysis_a", expected)
    assert "support" not in strip_support(
        {"task": "replacement_state", "support": [], "cases": []}
    )
    assert not (tmp_path / "clean" / "env" / "oracle.json").exists()
