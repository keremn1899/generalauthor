from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from research.semantic_integration.domains.bom.llm_world_programming.prompts import (
    participant_prompt,
)
from research.semantic_integration.domains.bom.llm_world_programming.scorer import (
    classify_failure,
    load_expected,
    strip_support,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import (
    REPO,
    canary_paths,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
    run_isolated,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.workspaces import (
    build_raw_workspace,
    build_world_workspace,
    copy_frozen_world_fixture,
    forbidden_paths_present,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_API = (
    REPO_ROOT
    / "research/semantic_integration/domains/bom/llm_world_programming_v2/workspace_assets/world/WORLD_API.md"
)


def test_prompts_a_and_b_still_do_not_name_solution_relations():
    for condition in ("raw", "world"):
        for task_id in ("analysis_a", "analysis_b"):
            prompt = participant_prompt(condition, task_id)
            assert "part:X110" not in prompt
            assert "eligible_part" not in prompt
            assert "manufacturer_part_number" not in prompt
            assert "acceptable_replacement" not in prompt


def test_open_world_opens_the_provided_fixture(tmp_path):
    copy_frozen_world_fixture()
    workspace = tmp_path / "world"
    build_world_workspace(workspace)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace)
    completed = subprocess.run(
        [
            "python3",
            "-c",
            "from world_surface import open_world; "
            "world = open_world(); "
            "info = world.describe(); "
            "world.close(); "
            "print(info['view']['view_id']); "
            "print(len(info['relations']))",
        ],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.strip().splitlines()
    assert lines[0]
    assert int(lines[1]) > 0


def test_world_api_still_does_not_name_solution_relations():
    text = WORLD_API.read_text(encoding="utf-8")
    assert "eligible_part" not in text
    assert "acceptable_replacement" not in text


def test_physical_isolation_preflight_hides_repo_and_siblings():
    copy_frozen_world_fixture()
    live = new_live_workspace()
    try:
        build_raw_workspace(live)
        assert forbidden_paths_present(live, "raw") == []
        result = preflight_isolation(live)
        assert result["ok"] is True
        hidden = run_isolated(
            live,
            [
                "python3",
                "-c",
                "from pathlib import Path; "
                f"print(Path({str(canary_paths()[0])!r}).exists()); "
                f"print(Path({str(REPO / 'research')!r}).exists())",
            ],
            timeout=30,
        )
        assert hidden.returncode == 0, hidden.stderr
        lines = hidden.stdout.strip().splitlines()
        assert lines[0] == "False"
        assert lines[1] == "False"
    finally:
        remove_live_workspace(live)


def test_scorer_still_accepts_frozen_expected(tmp_path):
    copy_frozen_world_fixture()
    from research.semantic_integration.domains.bom.llm_world_programming_v2.scorer import (
        score_run,
    )

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
    assert "support" not in strip_support(
        {"task": "replacement_state", "support": [], "cases": []}
    )


def test_new_campaigns_default_to_composer_not_sol(monkeypatch):
    from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
        DEFAULT_MODEL,
        model_is_expensive,
        model_is_non_cursor,
        refuse_expensive_model,
        refuse_non_cursor_model,
        reported_model_is_composer,
        run_agent,
    )

    assert DEFAULT_MODEL == "composer-2.5"
    assert not model_is_expensive(DEFAULT_MODEL)
    assert model_is_expensive("gpt-5.6-sol-high")
    assert not model_is_non_cursor("composer-2.5")
    assert model_is_non_cursor("gpt-5.6-sol-high")
    assert model_is_non_cursor("gpt-5.6-terra-medium")
    assert model_is_non_cursor("claude-sonnet-5-thinking-high")
    assert model_is_non_cursor("gemini-3.7-flash-low")
    assert reported_model_is_composer("Composer 2.5")
    assert not reported_model_is_composer("GPT-5.6 Sol 272K High")
    monkeypatch.delenv("ALLOW_EXPENSIVE_MODEL", raising=False)
    try:
        refuse_expensive_model("gpt-5.6-sol-high", action="freeze")
        raise AssertionError("expected refuse_expensive_model to raise")
    except RuntimeError as exc:
        assert "composer-2.5" in str(exc)
    for forbidden in (
        "gpt-5.6-sol-high",
        "gpt-5.6-terra-medium",
        "claude-opus-5-thinking-high",
        "gemini-3.7-flash-low",
    ):
        try:
            refuse_non_cursor_model(forbidden, action="run")
            raise AssertionError(f"expected refuse_non_cursor_model for {forbidden}")
        except RuntimeError as exc:
            assert "non-Cursor" in str(exc)
    refuse_non_cursor_model("composer-2.5", action="run")
    try:
        run_agent(
            workspace=Path("/tmp"),
            prompt="do not run",
            model="gpt-5.6-sol-high",
        )
        raise AssertionError("expected run_agent to refuse sol")
    except RuntimeError as exc:
        assert "non-Cursor" in str(exc) or "expensive model" in str(exc)


def test_freeze_refuses_to_overwrite_existing_campaign():
    from research.semantic_integration.domains.bom.llm_world_programming_v2.freeze_manifest import (
        freeze,
    )

    try:
        freeze()
        raise AssertionError("expected freeze to refuse overwrite")
    except RuntimeError as exc:
        assert "overwrite" in str(exc)
        assert "bom-llm-world-programming-v3" in str(exc)
