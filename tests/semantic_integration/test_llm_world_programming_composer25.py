from __future__ import annotations

import json

from research.semantic_integration.domains.bom.llm_world_programming.prompts import (
    participant_prompt,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    refuse_non_cursor_model,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.agent import (
    MODEL,
    MODEL_FAST_FORBIDDEN,
    refuse_fast_model,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.freeze_manifest import (
    N_TRIALS,
    V3_FINGERPRINT,
    prompt_fingerprints,
    v3_manifest,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.isolation import (
    EXPERIMENT_ID,
    LIVE_ROOT,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.workspaces import (
    ROOT,
    copy_frozen_world_fixture,
)


def test_model_is_composer_not_sol_or_fast():
    assert MODEL == "composer-2.5"
    assert "sol" not in MODEL
    assert MODEL != MODEL_FAST_FORBIDDEN
    try:
        refuse_fast_model("composer-2.5-fast")
        raise AssertionError("expected refuse_fast_model")
    except RuntimeError:
        pass
    try:
        refuse_non_cursor_model("gpt-5.6-terra-medium", action="run")
        raise AssertionError("expected refuse_non_cursor_model")
    except RuntimeError as exc:
        assert "non-Cursor" in str(exc)


def test_protocol_fingerprints_match_frozen_v3():
    predecessor = v3_manifest()
    assert predecessor["fingerprint"] == V3_FINGERPRINT
    assert prompt_fingerprints() == predecessor["prompt_fingerprints"]
    assert N_TRIALS == 5
    assert EXPERIMENT_ID == "bom-llm-world-programming-composer25"
    assert ROOT.name == "llm_world_programming_composer25"
    assert "composer25" in str(LIVE_ROOT)


def test_prompts_still_do_not_name_solution_relations():
    for condition in ("raw", "world"):
        for task_id in ("analysis_a", "analysis_b"):
            prompt = participant_prompt(condition, task_id)
            assert "part:X110" not in prompt
            assert "eligible_part" not in prompt
            assert "acceptable_replacement" not in prompt


def test_copied_world_fixture_matches_v3():
    predecessor = v3_manifest()
    copied = copy_frozen_world_fixture()
    assert copied == predecessor["world_fixture_fingerprint"]


def test_isolation_preflight_hides_repo_and_v3_report():
    copy_frozen_world_fixture()
    live = new_live_workspace()
    try:
        (live / "README.md").write_text("workspace\n", encoding="utf-8")
        payload = preflight_isolation(live)
        assert payload["ok"] is True
        assert payload["failures"] == []
    finally:
        remove_live_workspace(live)
