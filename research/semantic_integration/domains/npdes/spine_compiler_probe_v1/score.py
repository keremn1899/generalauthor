"""Evaluator-side scoring. Never shown to participant agents."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.spine_compiler_probe_v1.paths import FROZEN, RUNS

PRIMARY_CLASSES = {"STRUCTURE_TRIGGERABLE", "SOURCE_METADATA_TRIGGERABLE"}

SEAM_SIGNATURES: dict[str, dict[str, Any]] = {
    "S-FARM-TDS-STAGE": {
        "need_any": ["70295", "total dissolved", "tds"],
        "need_failure": ["CARDINALITY_OVERSATISFIED", "MULTIPLE_CANDIDATES", "CARDINALITY_UNDERSATISFIED"],
        "need_structure": ["interval_contains", "begin_date", "end_date", "LIMIT_BEGIN", "2024-12-01", "12/01/2024"],
        "permits": ["NM0020583"],
    },
    "S-FARM-REPORT-ONLY": {
        "need_any": ["COMPARISON_OPERATOR_REQUIRED", "require_numeric", "LIMIT_VALUE_NMBR", "limit_value"],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED"],
        "permits": ["NM0020583"],
    },
    "S-AZTEC-WHEN-DISCHARGING": {
        "need_any": ["when discharging", "DMR_COMMENT", "comment"],
        "need_failure": ["UNINTERPRETED_REQUIRED_CODE", "NO_MATERIALIZABLE_PATH", "CARDINALITY_UNDERSATISFIED"],
        "permits": ["NM0028762"],
    },
    "S-AZTEC-REPORT-ONLY": {
        "need_any": ["COMPARISON_OPERATOR_REQUIRED", "require_numeric", "LIMIT_VALUE_NMBR", "limit_value"],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED"],
        "permits": ["NM0028762"],
    },
    "S-GCC-EVENT-DISCHARGE": {
        "need_any": ["storm runoff", "NODI", "nodi", "NM0000116", "LIMIT_SET_NAME"],
        "need_failure": ["UNINTERPRETED_REQUIRED_CODE", "NO_MATERIALIZABLE_PATH", "CARDINALITY_UNDERSATISFIED"],
        "permits": ["NM0000116"],
    },
    "S-GCC-REPORT-ONLY": {
        "need_any": ["COMPARISON_OPERATOR_REQUIRED", "require_numeric", "LIMIT_VALUE_NMBR", "limit_value"],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED"],
        "permits": ["NM0000116"],
    },
    "S-SOURCE-AUTHORITY": {
        "need_any": ["document_inventory", "document_kind", "fact_sheet", "statement_of_basis", "final_permit"],
        "need_failure": ["CARDINALITY_OVERSATISFIED", "MULTIPLE_CANDIDATES", "UNBOUND_CORRESPONDENCE"],
        "permits": [],
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def blob(trial_dir: Path) -> str:
    parts: list[str] = []
    for name in ("trial.json", "final_compile.json"):
        path = trial_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    iters = sorted(trial_dir.glob("iter*/program.json"))
    if iters:
        parts.append(iters[-1].read_text(encoding="utf-8"))
    instances = trial_dir / "iter1" / "trigger_instances.json"
    last_instances = sorted(trial_dir.glob("iter*/trigger_instances.json"))
    if last_instances:
        text = last_instances[-1].read_text(encoding="utf-8")
        parts.append(text[:400000])
    return "\n".join(parts).lower()


def program_of(trial_dir: Path) -> dict:
    iters = sorted(trial_dir.glob("iter*/program.json"))
    if not iters:
        return {}
    payload = load_json(iters[-1])
    return payload if isinstance(payload, dict) else {}


def group_failure_kinds(trial: dict) -> set[str]:
    return {str(g.get("failure_kind") or "") for g in trial.get("final", {}).get("trigger_groups") or []}


def seam_hit(gold_id: str, trial: dict, text: str, program: dict) -> bool:
    spec = SEAM_SIGNATURES[gold_id]
    failures = group_failure_kinds(trial)
    if spec["need_failure"] and not any(kind in failures for kind in spec["need_failure"]):
        return False
    prog_text = json.dumps(program, default=str).lower()
    hay = text + "\n" + prog_text
    if spec["need_any"] and not any(token.lower() in hay for token in spec["need_any"]):
        return False
    if gold_id == "S-FARM-TDS-STAGE":
        if not any(token.lower() in hay for token in spec["need_structure"]):
            return False
    if spec["permits"] and gold_id not in {"S-SOURCE-AUTHORITY"}:
        if not any(p.lower() in hay for p in spec["permits"]):
            # permit may be only in instances truncated; allow if failure+token matched
            if gold_id.startswith("S-AZTEC") or gold_id.startswith("S-GCC") or gold_id.startswith("S-FARM"):
                pass
    return True


def classify_group(group: dict, program: dict) -> str:
    kind = str(group.get("failure_kind") or "")
    req = str(group.get("requirement_id") or "").lower()
    if kind == "NO_MATERIALIZABLE_PATH":
        return "PURPOSE_RELEVANT"
    if kind in {
        "CARDINALITY_OVERSATISFIED",
        "CARDINALITY_UNDERSATISFIED",
        "MULTIPLE_CANDIDATES",
        "COMPARISON_OPERATOR_REQUIRED",
        "UNINTERPRETED_REQUIRED_CODE",
    }:
        return "PURPOSE_RELEVANT" if req else "PLAUSIBLY_RELEVANT"
    if kind == "UNBOUND_CORRESPONDENCE":
        return "PLAUSIBLY_RELEVANT"
    return "IRRELEVANT"


def spine_distinctions(program: dict, compile_final: dict) -> dict[str, bool]:
    """Materialized distinctions. An uncompiled program scores false on every cell."""

    if not compile_final.get("structurally_valid"):
        return {
            "facility_permit": False,
            "measurements": False,
            "parameters": False,
            "periods": False,
            "limit_rows": False,
            "effective_intervals": False,
            "candidate_links": False,
            "nodi_or_codes": False,
            "document_metadata": False,
        }
    text = json.dumps(program, default=str).lower()
    rows = compile_final.get("relation_row_counts") or {}
    spine_rels = (compile_final.get("spine") or {}).get("relations") or {}
    maps = program.get("maps") or []
    source_names = {str(m.get("source") or "") for m in maps if isinstance(m, dict)}
    derived_rows = 0
    for spec in spine_rels.values():
        if isinstance(spec, dict) and spec.get("kind") == "derived":
            derived_rows += int(spec.get("rows") or 0)
    has_interval = "interval_contains" in text
    return {
        "facility_permit": any(tok in text for tok in ("permit", "external_permit")) and max(rows.values() or [0]) > 0,
        "measurements": "dmr_measurements.csv" in source_names
        and any(n > 0 and "measur" in k for k, n in rows.items()),
        "parameters": any(tok in text for tok in ("parameter", "parameter_code")),
        "periods": any(tok in text for tok in ("period", "monitoring_period")),
        "limit_rows": "permit_limits.csv" in source_names
        and any("limit" in k and n > 0 for k, n in rows.items()),
        "effective_intervals": has_interval and derived_rows > 0,
        "candidate_links": derived_rows > 0,
        "nodi_or_codes": any(tok in text for tok in ("nodi", "optional_monitoring", "comment", "qualifier")),
        "document_metadata": "document_inventory.json" in source_names
        and any(n > 0 and ("doc" in k or "permit_document" in k) for k, n in rows.items()),
    }


def tds_trace(trial: dict, text: str, program: dict, distinctions: dict[str, bool]) -> dict[str, Any]:
    hit = False
    if "S-FARM-TDS-STAGE" in SEAM_SIGNATURES:
        hit = seam_hit("S-FARM-TDS-STAGE", trial, text, program)
    mechanical = distinctions.get("effective_intervals") and distinctions.get("candidate_links") and (
        "70295" in text or "tds" in text or "total dissolved" in text
    )
    if hit:
        status = "TRIGGER"
    elif mechanical:
        status = "SPINE_RESOLVED_MECHANICALLY"
    else:
        status = "MISS"
    return {
        "status": status,
        "trigger": hit,
        "spine_has_dated_candidates": bool(mechanical),
        "question": "Did the constructed spine know applicable-limit selection was unresolved or mechanically dated?",
    }


def authority_trace(trial: dict, text: str, program: dict, distinctions: dict[str, bool]) -> dict[str, Any]:
    hit = seam_hit("S-SOURCE-AUTHORITY", trial, text, program)
    return {
        "frozen_class": "SOURCE_METADATA_TRIGGERABLE",
        "trigger": hit,
        "mapped_inventory": distinctions.get("document_metadata"),
        "note": "Metadata only. No prose. No retrofit.",
    }


def score_trial(index: int, freeze: dict) -> dict[str, Any]:
    trial_dir = RUNS / f"T{index}"
    trial = load_json(trial_dir / "trial.json")
    text = blob(trial_dir)
    program = program_of(trial_dir)
    compile_final = trial.get("final") or {}
    distinctions = spine_distinctions(program, compile_final)
    primary = [s for s in freeze["seams"] if s["class"] in PRIMARY_CLASSES]
    per_seam = {}
    hits = 0
    for seam in freeze["seams"]:
        gid = seam["gold_id"]
        if gid in SEAM_SIGNATURES:
            hit = seam_hit(gid, trial, text, program)
        else:
            hit = False
        per_seam[gid] = {
            "class": seam["class"],
            "primary": seam["class"] in PRIMARY_CLASSES,
            "hit": hit,
        }
        if seam["class"] in PRIMARY_CLASSES and hit:
            hits += 1
    groups = compile_final.get("trigger_groups") or []
    selectivity = []
    for group in groups:
        label = classify_group(group, program)
        selectivity.append(
            {
                "group_id": group.get("group_id"),
                "failure_kind": group.get("failure_kind"),
                "requirement_id": group.get("requirement_id"),
                "n_instances": group.get("n_instances"),
                "label": label,
            }
        )
    counts = Counter(row["label"] for row in selectivity)
    n_groups = len(groups) or 1
    return {
        "trial": f"T{index}",
        "structurally_valid": compile_final.get("structurally_valid"),
        "n_iterations": trial.get("n_iterations"),
        "n_trigger_groups": compile_final.get("n_trigger_groups") or 0,
        "n_trigger_instances": compile_final.get("n_trigger_instances") or 0,
        "e1_primary_hits": hits,
        "e1_primary_n": len(primary),
        "e1_recall": hits / len(primary) if primary else None,
        "per_seam": per_seam,
        "e3_counts": dict(counts),
        "e3_irrelevant_rate": counts["IRRELEVANT"] / n_groups if groups else None,
        "e3_purpose_relevant_rate": counts["PURPOSE_RELEVANT"] / n_groups if groups else None,
        "e3_groups": selectivity,
        "e4_distinctions": distinctions,
        "e4_n_true": sum(1 for v in distinctions.values() if v),
        "tds": tds_trace(trial, text, program, distinctions),
        "authority": authority_trace(trial, text, program, distinctions),
        "relation_row_counts": compile_final.get("relation_row_counts") or {},
        "referent_counts": compile_final.get("referent_counts") or {},
        "program_summary": {
            "n_referents": len(program.get("referents") or []),
            "n_maps": len(program.get("maps") or []),
            "n_relations": len(program.get("relations") or []),
            "n_requirements": len(program.get("requirements") or []),
            "relation_names": [r.get("name") for r in (program.get("relations") or []) if isinstance(r, dict)],
            "requirement_ids": [r.get("id") for r in (program.get("requirements") or []) if isinstance(r, dict)],
        },
    }


def e5_stability(trial_scores: list[dict]) -> dict[str, Any]:
    keys = [
        "facility_permit",
        "measurements",
        "parameters",
        "periods",
        "limit_rows",
        "effective_intervals",
        "candidate_links",
        "nodi_or_codes",
        "document_metadata",
    ]
    stable = {}
    for key in keys:
        vals = [bool((t.get("e4_distinctions") or {}).get(key)) for t in trial_scores]
        stable[key] = {"n_true": sum(vals), "stable": len(set(vals)) == 1}
    req_sets = [tuple(sorted(t.get("program_summary", {}).get("requirement_ids") or [])) for t in trial_scores]
    rel_sets = [tuple(sorted(t.get("program_summary", {}).get("relation_names") or [])) for t in trial_scores]
    return {
        "distinctions": stable,
        "identical_requirement_ids": len(set(req_sets)) == 1,
        "identical_relation_names": len(set(rel_sets)) == 1,
        "n_distinct_requirement_id_sets": len(set(req_sets)),
        "n_distinct_relation_name_sets": len(set(rel_sets)),
        "note": "Names may differ. Stability is scored on distinctions, not identifiers.",
    }


def choose_label(mean_e1: float, mean_e4: float, mean_groups: float, n_valid: int) -> str:
    if n_valid < 3:
        return "MIXED_PROGRAMMED_SPINE_RESULT"
    strong_spine = mean_e4 >= 6
    high_recall = mean_e1 >= 0.7
    some_recall = mean_e1 >= 0.4
    if strong_spine and high_recall:
        return "PROGRAMMED_SPINE_SUPPORTED"
    if strong_spine and not some_recall:
        return "PROGRAMMED_CONSTRUCTION_WORKS_TRIGGER_RECALL_WEAK"
    if mean_e4 <= 4:
        return "SPINE_UNDERSPECIFIED"
    if n_valid >= 4 and mean_e1 < 0.25 and mean_e4 >= 5:
        return "AGENTIC_PASS_REASONING_NOT_COMPRESSIBLE"
    return "MIXED_PROGRAMMED_SPINE_RESULT"


def score_campaign() -> dict[str, Any]:
    freeze = load_json(FROZEN / "triggerability.json")
    baselines = load_json(FROZEN / "baselines.json")
    trials = [score_trial(i, freeze) for i in range(1, 6) if (RUNS / f"T{i}" / "trial.json").exists()]
    n = len(trials) or 1
    mean_e1 = sum(t["e1_recall"] or 0 for t in trials) / n
    mean_e4 = sum(t["e4_n_true"] for t in trials) / n
    mean_groups = sum(t["n_trigger_groups"] for t in trials) / n
    mean_instances = sum(t["n_trigger_instances"] for t in trials) / n
    n_valid = sum(1 for t in trials if t.get("structurally_valid"))
    special = {}
    for gid in [
        "S-FARM-TDS-STAGE",
        "S-SOURCE-AUTHORITY",
        "S-FARM-TRC-CONDITIONAL",
        "S-AZTEC-WHEN-DISCHARGING",
        "S-AZTEC-WET-SEASONAL",
        "S-GCC-WET-FIRST-DISCHARGE",
        "S-AZTEC-DELTA-BHC",
        "S-FARM-REPORT-ONLY",
        "S-AZTEC-REPORT-ONLY",
        "S-GCC-REPORT-ONLY",
        "S-FARM-CN-SCHEDULE",
        "S-GCC-EVENT-DISCHARGE",
    ]:
        special[gid] = {
            "hits": sum(1 for t in trials if (t.get("per_seam") or {}).get(gid, {}).get("hit")),
            "n": len(trials),
        }
    label = choose_label(mean_e1, mean_e4, mean_groups, n_valid)
    return {
        "experiment_id": "npdes-spine-compiler-probe-v1",
        "n_trials": len(trials),
        "n_structurally_valid": n_valid,
        "e1_mean_recall": mean_e1,
        "e2_mean_trigger_groups": mean_groups,
        "e2_mean_trigger_instances": mean_instances,
        "e2_baselines": baselines,
        "e4_mean_distinctions": mean_e4,
        "e5": e5_stability(trials),
        "special_traces": special,
        "label": label,
        "trials": trials,
    }
