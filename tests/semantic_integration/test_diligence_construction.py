from __future__ import annotations

import json

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    stream_events,
    usage_from_events,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    reported_model_is_composer,
)
from research.semantic_integration.domains.diligence.constructor_agent import MODEL
from research.semantic_integration.domains.diligence.freeze_apparatus import (
    HIDDEN,
    PURPOSES,
    ROOT,
    SOURCES,
    build_manifest,
)
from research.semantic_integration.domains.diligence.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.workspaces import (
    build_constructor_workspace,
)


def test_hidden_purpose_d_is_not_among_visible_purposes():
    visible = {path.name for path in PURPOSES.glob("visible_*.md")}
    assert visible == {"visible_a.md", "visible_b.md", "visible_c.md"}
    assert (HIDDEN / "purpose_d.md").exists()
    assert (HIDDEN / "expected" / "purpose_d.json").exists()


def test_sources_are_heterogeneous_and_nontrivial():
    names = {path.name for path in SOURCES.rglob("*") if path.is_file()}
    assert "crm.csv" in names
    assert "invoices.json" in names
    assert "company_registry.csv" in names
    assert "commercial_notes.md" in names
    assert "MSA-HELION-2019.md" in names


def test_constructor_workspace_omits_hidden_and_d():
    live = new_live_workspace()
    try:
        build_constructor_workspace(live)
        assert not list(live.rglob("purpose_d.md"))
        assert not list(live.rglob("purpose_a.json"))
        kernel = (live / "KERNEL.md").read_text(encoding="utf-8")
        assert "eligible_part" not in kernel
        assert "acceptable_replacement" not in kernel
        assert "open_ar_assignment_restriction" not in (live / "CONSTRUCTION_TASK.md").read_text(
            encoding="utf-8"
        )
        payload = preflight_isolation(live)
        assert payload["ok"] is True
    finally:
        remove_live_workspace(live)


def test_manifest_builder_hashes_hidden_separately():
    manifest = build_manifest()
    assert manifest["held_out_purpose"] == "D"
    assert "purpose_d.md" in manifest["hidden_fingerprints"]
    assert "visible_a.md" in manifest["purpose_fingerprints"]
    assert manifest["model"] == "composer-2.5"
    assert MODEL == "composer-2.5"
    assert "fast" not in MODEL


def test_frozen_constructor_runs_reported_composer_not_gpt_or_claude():
    for phase in ("abc", "d"):
        transcript = ROOT / "constructor_run" / phase / "transcript.stdout.txt"
        events = stream_events(transcript.read_text(encoding="utf-8"))
        reported = usage_from_events(events)["model"]
        assert reported_model_is_composer(reported)
        agent = json.loads((ROOT / "constructor_run" / phase / "agent.json").read_text())
        assert agent["model"] == "composer-2.5"
        assert agent["reported_model"] == "Composer 2.5"
