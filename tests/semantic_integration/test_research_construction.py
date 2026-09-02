from __future__ import annotations

import json

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    stream_events,
    usage_from_events,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    reported_model_is_composer,
)
from research.semantic_integration.domains.research.constructor_agent import MODEL
from research.semantic_integration.domains.research.freeze_apparatus import (
    HIDDEN,
    PURPOSES,
    ROOT,
    SOURCES,
    build_manifest,
)
from research.semantic_integration.domains.research.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.research.workspaces import (
    README,
    TASK,
    build_constructor_workspace,
)


def test_hidden_purpose_d_is_not_among_visible_purposes():
    visible = {path.name for path in PURPOSES.glob("visible_*.md")}
    assert visible == {"visible_a.md", "visible_b.md", "visible_c.md"}
    assert (HIDDEN / "purpose_d.md").exists()
    assert (HIDDEN / "expected" / "purpose_d.json").exists()


def test_sources_are_heterogeneous_and_nontrivial():
    names = {path.name for path in SOURCES.rglob("*") if path.is_file()}
    assert "study_registry.csv" in names
    assert "publications.json" in names
    assert "datasets.csv" in names
    assert "methods_notes.md" in names
    assert "CLEAR-HTN-variables.md" in names
    assert "AURORA-variables.md" in names


def test_fixture_contains_required_complexity():
    registry = (SOURCES / "study_registry.csv").read_text(encoding="utf-8")
    publications = json.loads((SOURCES / "publications.json").read_text(encoding="utf-8"))
    datasets = (SOURCES / "datasets.csv").read_text(encoding="utf-8")
    notes = (SOURCES / "methods_notes.md").read_text(encoding="utf-8")
    assert "REG-2021-0412" in registry
    assert "change in systolic pressure at 12 weeks" in registry
    assert any(row["publication_id"] == "PUB-CLEAR-2023" for row in publications)
    assert any("12-week SBP change from baseline" in json.dumps(row) for row in publications)
    assert "NW-PULM-24" in datasets
    assert "has not uniquely bound" in notes
    assert "HbA1c assay file was not transferred" in notes
    assert "Marlin lipid clinic audit" in notes
    assert "PSQI was analysed as secondary" in notes or "PSQI was collected as a secondary" in (
        json.dumps(publications) + notes
    )


def test_constructor_workspace_omits_hidden_and_prior_ontologies():
    live = new_live_workspace()
    try:
        build_constructor_workspace(live)
        assert not list(live.rglob("purpose_d.md"))
        assert not list(live.rglob("purpose_a.json"))
        assert not list(live.rglob("designer_notes.md"))
        kernel = (live / "KERNEL.md").read_text(encoding="utf-8")
        assert "eligible_part" not in kernel
        assert "acceptable_replacement" not in kernel
        assert "identity_judgment" not in kernel
        assert "same_underlying_study" not in kernel
        assert "reanalysis_ready_under_purpose_c" not in kernel
        task = (live / "CONSTRUCTION_TASK.md").read_text(encoding="utf-8")
        assert "traceable_result_with_dataset" not in task
        assert "open_ar_assignment_restriction" not in task
        payload = preflight_isolation(live)
        assert payload["ok"] is True
    finally:
        remove_live_workspace(live)


def test_prompts_are_generic_construction_contract():
    assert "gold ontology" in README
    assert "Do not add a semantic primitive" in TASK
    assert "eligible_part" not in README
    assert "identity_judgment" not in TASK


def test_manifest_builder_hashes_hidden_separately():
    manifest = build_manifest()
    assert manifest["held_out_purpose"] == "D"
    assert manifest["label"] == "PRE_REPAIR_CONSTRUCTOR_BASELINE"
    assert "purpose_d.md" in manifest["hidden_fingerprints"]
    assert "visible_a.md" in manifest["purpose_fingerprints"]
    assert manifest["model"] == "composer-2.5"
    assert MODEL == "composer-2.5"
    assert "fast" not in MODEL
    assert "BOM ontology" in manifest["constructor_must_not_see"]
    assert "diligence ontology" in manifest["constructor_must_not_see"]


def test_d_is_not_concatenation_of_a_and_c():
    expected_a = json.loads((HIDDEN / "expected" / "purpose_a.json").read_text())
    expected_c = json.loads((HIDDEN / "expected" / "purpose_c.json").read_text())
    expected_d = json.loads((HIDDEN / "expected" / "purpose_d.json").read_text())
    a_asserted = {
        row["registry_id"]
        for row in expected_a["studies"]
        if row["correspondence"] == "asserted"
    }
    c_ready = {row["registry_id"] for row in expected_c["studies"] if row["status"] == "ready"}
    d_matches = {row["registry_id"] for row in expected_d["cases"] if row["status"] == "matches"}
    assert "REG-2019-1108" in d_matches
    assert "REG-2019-1108" not in c_ready
    assert "REG-2022-0094" in c_ready
    assert "REG-2022-0094" not in d_matches
    assert d_matches != (a_asserted & c_ready)


def test_frozen_constructor_runs_reported_composer_not_gpt_or_claude():
    for phase in ("abc", "d"):
        transcript = ROOT / "constructor_run" / phase / "transcript.stdout.txt"
        if not transcript.exists():
            continue
        events = stream_events(transcript.read_text(encoding="utf-8"))
        reported = usage_from_events(events)["model"]
        assert reported_model_is_composer(reported)
        agent = json.loads((ROOT / "constructor_run" / phase / "agent.json").read_text())
        assert agent["model"] == "composer-2.5"
        assert agent["reported_model"] == "Composer 2.5"
