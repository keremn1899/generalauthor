"""Run Semantic Spine Anatomy & Minimality Probe v1. Research-only."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    run_construction,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import seed_workspace
from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.ablate import ablate_source
from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.inventory import (
    construction_path,
    cross_trial,
    holes_path,
    inventory_trial,
    spine_path,
)
from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.paths import (
    ABLATIONS,
    COPIES,
    EXPERIMENT_ID,
    PFPS_RUNS,
    REPORTS,
    RUNS,
    TRIALS,
)
from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.score_local import classify_ablation, score_run

LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-semantic-spine-anatomy-v1"

ABLATION_SPEC: list[dict[str, Any]] = [
    {"trial": "T1", "id": "drop_season_month_flag", "requirement_names": ["season_month_flag_semantics"]},
    {"trial": "T1", "id": "drop_limit_freq", "requirement_names": ["limit_freq_semantics"]},
    {"trial": "T1", "id": "drop_unique_catalog", "requirement_names": ["unique_catalog_variant_per_limit_value"]},
    {"trial": "T1", "id": "drop_unique_schedule", "requirement_names": ["unique_schedule_match_per_measurement"]},
    {"trial": "T1", "id": "drop_nodi", "requirement_names": ["nodi_code_semantics"]},
    {"trial": "T1", "id": "drop_comment_interpret", "requirement_names": ["requirement_comment_semantics"]},
    {"trial": "T1", "id": "drop_when_unresolved", "unresolved_names": ["discharge_condition_not_in_structured_evidence"]},
    {"trial": "T1", "id": "drop_non_numeric_class", "requirement_names": ["non_numeric_limit_classification"]},
    {"trial": "T2", "id": "drop_seasonal", "requirement_names": ["interpret_seasonal_month_flag"]},
    {"trial": "T2", "id": "drop_unique", "requirement_names": ["unique_limit_value_per_numeric_measurement"]},
    {"trial": "T2", "id": "drop_nodi", "requirement_names": ["interpret_nodi_semantics"]},
    {"trial": "T2", "id": "drop_comment", "requirement_names": ["interpret_permit_dmr_comment"]},
    {"trial": "T3", "id": "drop_value_type", "requirement_names": ["value_type_for_limit_selection"]},
    {"trial": "T3", "id": "drop_limit_unit", "requirement_names": ["limit_unit_for_comparison"]},
    {"trial": "T3", "id": "drop_seasonal_loop", "drop_seasonal_loop": True},
    {"trial": "T3", "id": "drop_unique_permit_limit", "requirement_names": ["unique_permit_limit_per_measurement"]},
    {"trial": "T3", "id": "drop_nodi", "requirement_names": ["nodi_code_semantics"]},
    {"trial": "T3", "id": "drop_comment_interpret", "requirement_names": ["permit_comment_for_monitoring_applicability"]},
    {"trial": "T4", "id": "drop_freq", "requirement_names": ["limit_freq_obligation"]},
    {"trial": "T4", "id": "drop_unique", "requirement_names": ["unique_applicable_limit_per_measurement"]},
    {"trial": "T4", "id": "drop_nodi", "requirement_names": ["nodi_code_semantics"]},
    {"trial": "T4", "id": "drop_comment", "requirement_names": ["dmr_comment_obligation"]},
    {"trial": "T5", "id": "drop_aggregated", "unresolved_names": ["aggregated_reporting_requirement"]},
    {"trial": "T5", "id": "drop_pass_fail", "unresolved_names": ["pass_fail_reporting_semantics"]},
    {"trial": "T5", "id": "drop_unique", "requirement_names": ["unique_applicable_limit_per_measurement"]},
    {"trial": "T5", "id": "drop_nodi", "requirement_names": ["nodi_code_semantics"]},
    {"trial": "T5", "id": "drop_comment", "requirement_names": ["permit_limit_comment_text"]},
    {"trial": "T5", "id": "drop_document_unresolved", "unresolved_names": ["permit_document_text_not_available"]},
    {"trial": "T5", "id": "drop_sample_type", "requirement_names": ["limit_sample_type_code"]},
    {"trial": "T5", "id": "drop_freq", "requirement_names": ["monitoring_frequency_code"]},
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def snapshot_copies() -> dict[str, Any]:
    rows = []
    for trial in TRIALS:
        src = construction_path(trial)
        dest = COPIES / trial / "construction.py"
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        dest.write_bytes(data)
        rows.append(
            {
                "trial": trial,
                "source": str(src),
                "copy": str(dest),
                "sha256": sha256_bytes(data),
                "bytes": len(data),
            }
        )
    return {"experiment_id": EXPERIMENT_ID, "copies": rows}


def verify_originals_untouched(snapshot: dict) -> None:
    for row in snapshot["copies"]:
        live = Path(row["source"]).read_bytes()
        if sha256_bytes(live) != row["sha256"]:
            raise RuntimeError(f"sealed original mutated: {row['trial']}")


def execute_program(trial: str, code: str, dest: Path) -> dict[str, Any]:
    LIVE_ROOT.mkdir(parents=True, exist_ok=True)
    live = LIVE_ROOT / dest.name
    if live.exists():
        shutil.rmtree(live)
    seed_workspace(live)
    (live / "construction.py").write_text(code, encoding="utf-8")
    clean = live / "clean_run"
    prepare_clean_run(live, clean)
    public = run_construction(clean)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "construction.py").write_text(code, encoding="utf-8")
    for name in ("spine.json", "holes.json", "run_public.json"):
        src = clean / name
        if src.exists():
            shutil.copy2(src, dest / name)
    dump(dest / "runner.json", public)
    holes = []
    spine: dict[str, Any] = {}
    if (dest / "holes.json").exists():
        holes = json.loads((dest / "holes.json").read_text(encoding="utf-8"))
    if (dest / "spine.json").exists():
        spine = json.loads((dest / "spine.json").read_text(encoding="utf-8"))
    scored = score_run(code, public, holes, spine)
    dump(dest / "score.json", scored)
    shutil.rmtree(live, ignore_errors=True)
    return scored


def run_baselines() -> dict[str, dict]:
    out = {}
    for trial in TRIALS:
        code = (COPIES / trial / "construction.py").read_text(encoding="utf-8")
        scored = execute_program(trial, code, ABLATIONS / trial / "baseline")
        out[trial] = scored
    return out


def run_ablations(baselines: dict[str, dict]) -> list[dict]:
    results = []
    for spec in ABLATION_SPEC:
        trial = spec["trial"]
        original = (COPIES / trial / "construction.py").read_text(encoding="utf-8")
        code, n_removed = ablate_source(
            original,
            requirement_names=spec.get("requirement_names"),
            unresolved_names=spec.get("unresolved_names"),
            drop_seasonal_loop=bool(spec.get("drop_seasonal_loop")),
        )
        dest = ABLATIONS / trial / spec["id"]
        scored = execute_program(trial, code, dest)
        label = classify_ablation(baselines[trial], scored)
        if n_removed == 0:
            label = "COUPLED_OR_INDETERMINATE"
        row = {
            "trial": trial,
            "ablation_id": spec["id"],
            "n_removed_nodes": n_removed,
            "spec": {k: spec[k] for k in spec if k != "trial"},
            "score": scored,
            "label": label,
            "delta_e1": (scored.get("e1_hits") or 0) - (baselines[trial].get("e1_hits") or 0),
            "delta_e2": (scored.get("e2_n_true") or 0) - (baselines[trial].get("e2_n_true") or 0),
            "delta_groups": (scored.get("n_hole_groups") or 0) - (baselines[trial].get("n_hole_groups") or 0),
        }
        dump(dest / "ablation.json", row)
        results.append(row)
        print(f"{trial} {spec['id']}: removed={n_removed} e1={scored.get('e1_hits')} label={label}", flush=True)
    return results


def rescore_saved() -> None:
    """Recompute labels from saved ablation artifacts without rerunning programs."""
    baselines: dict[str, dict] = {}
    for trial in TRIALS:
        dest = ABLATIONS / trial / "baseline"
        code = (dest / "construction.py").read_text(encoding="utf-8")
        public = json.loads((dest / "runner.json").read_text(encoding="utf-8"))
        holes = json.loads((dest / "holes.json").read_text(encoding="utf-8")) if (dest / "holes.json").exists() else []
        spine = json.loads((dest / "spine.json").read_text(encoding="utf-8")) if (dest / "spine.json").exists() else {}
        baselines[trial] = score_run(code, public, holes, spine)
    dump(RUNS / "baselines.json", baselines)
    results = []
    for spec in ABLATION_SPEC:
        dest = ABLATIONS / spec["trial"] / spec["id"]
        code = (dest / "construction.py").read_text(encoding="utf-8")
        public = json.loads((dest / "runner.json").read_text(encoding="utf-8"))
        holes = json.loads((dest / "holes.json").read_text(encoding="utf-8")) if (dest / "holes.json").exists() else []
        spine = json.loads((dest / "spine.json").read_text(encoding="utf-8")) if (dest / "spine.json").exists() else {}
        scored = score_run(code, public, holes, spine)
        n_removed = json.loads((dest / "ablation.json").read_text(encoding="utf-8")).get("n_removed_nodes", 0)
        label = classify_ablation(baselines[spec["trial"]], scored)
        if n_removed == 0:
            label = "COUPLED_OR_INDETERMINATE"
        row = {
            "trial": spec["trial"],
            "ablation_id": spec["id"],
            "n_removed_nodes": n_removed,
            "spec": {k: spec[k] for k in spec if k != "trial"},
            "score": scored,
            "label": label,
            "delta_e1": (scored.get("e1_hits") or 0) - (baselines[spec["trial"]].get("e1_hits") or 0),
            "delta_e2": (scored.get("e2_n_true") or 0) - (baselines[spec["trial"]].get("e2_n_true") or 0),
            "delta_groups": (scored.get("n_hole_groups") or 0) - (baselines[spec["trial"]].get("n_hole_groups") or 0),
        }
        dump(dest / "ablation.json", row)
        results.append(row)
        print(f"{spec['trial']} {spec['id']}: e1={scored.get('e1_hits')} nodi={scored.get('precise', {}).get('nodi_precise')} auth={scored.get('precise', {}).get('authority_precise')} label={label}", flush=True)
    dump(RUNS / "ablations.json", results)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--rescore":
        rescore_saved()
        return
    RUNS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_copies()
    dump(RUNS / "copy_manifest.json", snapshot)
    inventories = [inventory_trial(t) for t in TRIALS]
    dump(RUNS / "inventories.json", inventories)
    dump(RUNS / "intersection.json", cross_trial(inventories))
    print("inventories written", flush=True)
    baselines = run_baselines()
    dump(RUNS / "baselines.json", baselines)
    print("baselines written", flush=True)
    ablations = run_ablations(baselines)
    dump(RUNS / "ablations.json", ablations)
    verify_originals_untouched(snapshot)
    dump(
        RUNS / "campaign.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "n_inventories": len(inventories),
            "n_ablations": len(ablations),
            "originals_untouched": True,
        },
    )
    print("campaign sealed", flush=True)


if __name__ == "__main__":
    main()
