from __future__ import annotations

from research.semantic_integration.domains.diligence.pass_localization.agent import MODEL
from research.semantic_integration.domains.diligence.pass_localization.freeze import (
    build_manifest,
)
from research.semantic_integration.domains.diligence.pass_localization.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.pass_localization.prompts import (
    FORBIDDEN_PROMPT_TOKENS,
    PASS_ORDER,
    PROMPTS,
)
from research.semantic_integration.domains.diligence.pass_localization.workspaces import (
    seed_ordinary_workspace,
)


def test_model_is_composer():
    assert MODEL == "composer-2.5"
    assert "fast" not in MODEL


def test_prompts_have_all_passes_and_no_oracle_tokens():
    assert PASS_ORDER == ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8")
    for key, text in PROMPTS.items():
        for token in FORBIDDEN_PROMPT_TOKENS:
            assert token not in text, (key, token)
        if key not in {"d_world_only"}:
            assert "open_ar_assignment_restriction" not in text


def test_ordinary_workspace_omits_hidden_and_d():
    live = new_live_workspace()
    try:
        seed_ordinary_workspace(live)
        assert not list(live.rglob("purpose_d.md"))
        assert not list(live.rglob("purpose_a.json"))
        assert not list(live.rglob("identity_dispositions.json"))
        assert (live / "purposes" / "visible_a.md").exists()
        assert (live / "KERNEL.md").exists()
        payload = preflight_isolation(live)
        assert payload["ok"] is True
    finally:
        remove_live_workspace(live)


def test_certified_world_gold_derive_matches_hidden_expected(tmp_path):
    from research.semantic_integration.domains.diligence.evaluator import (
        score_purpose_a,
        score_purpose_b,
        score_purpose_c,
    )
    from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
        build_certified_world,
    )
    from research.semantic_integration.domains.diligence.pass_localization.gold_derive import (
        derive_certified,
    )
    from research.semantic_integration.domains.diligence.evaluator import load_json
    from pathlib import Path

    hidden = Path(
        "research/semantic_integration/domains/diligence/hidden/expected"
    )
    world = tmp_path / "world.sqlite"
    build_certified_world(world)
    out = derive_certified(world)
    assert score_purpose_a(out["a"], load_json(hidden / "purpose_a.json"))["pass"]
    assert score_purpose_b(out["b"], load_json(hidden / "purpose_b.json"))["pass"]
    assert score_purpose_c(out["c"], load_json(hidden / "purpose_c.json"))["pass"]


def test_manifest_builder_is_composer_five_trials():
    manifest = build_manifest()
    assert manifest["model"] == "composer-2.5"
    assert manifest["n_trials"] == 5
    assert manifest["repairs_during_campaign"] is False
    assert "p0" in manifest["prompt_fingerprints"]
