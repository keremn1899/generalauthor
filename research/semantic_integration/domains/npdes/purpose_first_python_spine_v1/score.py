"""Evaluator-side scoring. Triggerability reused unchanged from Spine Compiler Probe v1."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import FROZEN, RUNS

PRIMARY_CLASSES = {"STRUCTURE_TRIGGERABLE", "SOURCE_METADATA_TRIGGERABLE"}

SEAM_SIGNATURES: dict[str, dict[str, Any]] = {
    "S-FARM-TDS-STAGE": {
        "need_any": ["70295", "total dissolved", "tds"],
        "need_failure": [
            "CARDINALITY_OVERSATISFIED",
            "MULTIPLE_CANDIDATES",
            "CARDINALITY_UNDERSATISFIED",
            "EXPLICIT_UNRESOLVED",
        ],
        "need_structure": ["interval_contains", "begin_date", "end_date", "LIMIT_BEGIN", "parse_date", "2024-12-01"],
    },
    "S-FARM-REPORT-ONLY": {
        "need_any": [
            "non_numeric",
            "without_numeric_limit",
            "limit_value_nmbr",
            "require_numeric",
            "COMPARISON_OPERATOR_REQUIRED",
            "empty limit",
        ],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED", "UNINTERPRETED", "EXPLICIT_UNRESOLVED"],
    },
    "S-AZTEC-WHEN-DISCHARGING": {
        "need_any": ["when discharging", "dmr_comment", "comment"],
        "need_failure": ["UNINTERPRETED", "EXPLICIT_UNRESOLVED", "UNINTERPRETED_REQUIRED_CODE"],
    },
    "S-AZTEC-REPORT-ONLY": {
        "need_any": [
            "non_numeric",
            "without_numeric_limit",
            "limit_value_nmbr",
            "require_numeric",
            "COMPARISON_OPERATOR_REQUIRED",
            "empty limit",
        ],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED", "UNINTERPRETED", "EXPLICIT_UNRESOLVED"],
    },
    "S-GCC-EVENT-DISCHARGE": {
        "need_any": ["storm runoff", "nodi", "NM0000116", "limit_set"],
        "need_failure": ["UNINTERPRETED", "EXPLICIT_UNRESOLVED", "NO_MATERIALIZABLE_PATH", "UNINTERPRETED_REQUIRED_CODE"],
    },
    "S-GCC-REPORT-ONLY": {
        "need_any": [
            "non_numeric",
            "without_numeric_limit",
            "limit_value_nmbr",
            "require_numeric",
            "COMPARISON_OPERATOR_REQUIRED",
            "empty limit",
        ],
        "need_failure": ["COMPARISON_OPERATOR_REQUIRED", "UNINTERPRETED", "EXPLICIT_UNRESOLVED"],
    },
    "S-SOURCE-AUTHORITY": {
        "need_any": ["document_inventory", "document_kind", "fact_sheet", "statement_of_basis", "final_permit"],
        "need_failure": [
            "CARDINALITY_OVERSATISFIED",
            "MULTIPLE_CANDIDATES",
            "EXPLICIT_UNRESOLVED",
            "UNINTERPRETED",
        ],
    },
}

HARDCODE_PATTERNS = [
    re.compile(r"when\s+discharging.{0,80}(conditional|required|not required)", re.I | re.S),
    re.compile(r"if\s+.*when discharging", re.I),
    re.compile(r"nodi.{0,40}==.{0,10}['\"]9['\"].{0,80}(not required|conditional)", re.I | re.S),
    re.compile(r"fact.?sheet.{0,60}subordinate", re.I),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def construction_text(trial_dir: Path) -> str:
    iters = sorted(trial_dir.glob("iter*/construction.py"))
    if not iters:
        return ""
    return iters[-1].read_text(encoding="utf-8", errors="replace")


def blob(trial_dir: Path) -> str:
    parts = [construction_text(trial_dir)]
    for name in ("trial.json", "final_run.json"):
        path = trial_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    last_holes = sorted(trial_dir.glob("iter*/holes.json"))
    if last_holes:
        parts.append(last_holes[-1].read_text(encoding="utf-8")[:400000])
    last_spine = sorted(trial_dir.glob("iter*/spine.json"))
    if last_spine:
        parts.append(last_spine[-1].read_text(encoding="utf-8")[:200000])
    return "\n".join(parts).lower()


def group_failure_kinds(trial: dict) -> set[str]:
    return {str(g.get("failure_kind") or "") for g in trial.get("final", {}).get("hole_groups") or []}


def seam_hit(gold_id: str, trial: dict, text: str) -> bool:
    spec = SEAM_SIGNATURES[gold_id]
    failures = group_failure_kinds(trial)
    if spec["need_failure"] and not any(kind in failures for kind in spec["need_failure"]):
        return False
    if spec["need_any"] and not any(token.lower() in text for token in spec["need_any"]):
        return False
    extra = spec.get("need_structure") or []
    if extra and not any(token.lower() in text for token in extra):
        return False
    return True


def classify_group(group: dict) -> str:
    kind = str(group.get("failure_kind") or "")
    req = str(group.get("requirement") or "").lower()
    if kind in {
        "CARDINALITY_OVERSATISFIED",
        "CARDINALITY_UNDERSATISFIED",
        "MULTIPLE_CANDIDATES",
        "COMPARISON_OPERATOR_REQUIRED",
        "UNINTERPRETED",
        "UNINTERPRETED_REQUIRED_CODE",
        "NO_MATERIALIZABLE_PATH",
        "EXPLICIT_UNRESOLVED",
    }:
        return "PURPOSE_RELEVANT" if req or kind == "NO_MATERIALIZABLE_PATH" else "PLAUSIBLY_RELEVANT"
    return "IRRELEVANT"


def derived_rows(trial: dict) -> int:
    rels = trial.get("final", {}).get("relations") or {}
    n = 0
    for spec in rels.values():
        if isinstance(spec, dict) and spec.get("derived"):
            n += int(spec.get("n_rows") or 0)
    return n


def spine_distinctions(trial: dict, text: str) -> dict[str, bool]:
    if not trial.get("final", {}).get("ok"):
        return {
            "measurement": False,
            "limit": False,
            "parameter_context": False,
            "period_or_interval": False,
            "candidate_correspondence": False,
            "document_inventory": False,
            "opaque_code_or_text": False,
        }
    rows = trial.get("final", {}).get("relation_row_counts") or {}
    names = " ".join(rows.keys()).lower()
    return {
        "measurement": any("measur" in k and n > 0 for k, n in rows.items()),
        "limit": any("limit" in k and "candidate" not in k and n > 0 for k, n in rows.items())
        or ("permit_limits" in text and max(rows.values() or [0]) > 0),
        "parameter_context": "parameter" in text or "parameter" in names,
        "period_or_interval": any(tok in text for tok in ("period", "interval_contains", "begin_date", "parse_date")),
        "candidate_correspondence": derived_rows(trial) > 0
        or any("candidate" in k and n > 0 for k, n in rows.items()),
        "document_inventory": "document_inventory" in text
        and any(n > 0 and ("doc" in k or "inventory" in k or "permit_document" in k) for k, n in rows.items()),
        "opaque_code_or_text": any(tok in text for tok in ("nodi", "comment", "qualifier", "require_interpreted", "unresolved")),
    }


def hardcode_flags(code: str) -> list[str]:
    hits = []
    for pattern in HARDCODE_PATTERNS:
        if pattern.search(code or ""):
            hits.append(pattern.pattern)
    return hits


def first_failure(trial: dict, distinctions: dict[str, bool], exploration: dict) -> str:
    if not trial.get("final", {}).get("ok"):
        errors = " ".join(trial.get("final", {}).get("errors") or [])
        if "construction.py missing" in errors:
            return "deterministic execution"
        if any(tok in errors.lower() for tok in ("syntax", "nameerror", "typeerror", "valueerror", "keyerror")):
            return "deterministic execution"
        return "deterministic execution"
    reads = " ".join(exploration.get("reads") or []).lower()
    if not distinctions.get("candidate_correspondence"):
        if "dmr" not in reads and "permit_limit" not in reads and "csv" not in reads:
            return "source exploration"
        return "physical correspondence"
    if trial.get("final", {}).get("n_hole_groups", 0) == 0:
        return "requirement authoring"
    return "semantic modeling"


def exploration_merge(trial_dir: Path) -> dict[str, Any]:
    reads, shells = [], []
    for agent_path in sorted(trial_dir.glob("iter*/agent.json")):
        payload = load_json(agent_path)
        exp = payload.get("exploration") or {}
        reads.extend(exp.get("reads") or [])
        shells.extend(exp.get("shells") or [])
    return {"reads": reads, "shells": shells}


def score_trial(index: int, freeze: dict) -> dict[str, Any]:
    trial_dir = RUNS / f"T{index}"
    trial = load_json(trial_dir / "trial.json")
    text = blob(trial_dir)
    code = construction_text(trial_dir)
    distinctions = spine_distinctions(trial, text)
    exploration = exploration_merge(trial_dir)
    primary = [s for s in freeze["seams"] if s["class"] in PRIMARY_CLASSES]
    per_seam = {}
    hits = 0
    for seam in freeze["seams"]:
        gid = seam["gold_id"]
        hit = seam_hit(gid, trial, text) if gid in SEAM_SIGNATURES else False
        per_seam[gid] = {"class": seam["class"], "primary": seam["class"] in PRIMARY_CLASSES, "hit": hit}
        if seam["class"] in PRIMARY_CLASSES and hit:
            hits += 1
    groups = trial.get("final", {}).get("hole_groups") or []
    selectivity = []
    for group in groups:
        label = classify_group(group)
        selectivity.append(
            {
                "group_id": group.get("group_id"),
                "failure_kind": group.get("failure_kind"),
                "requirement": group.get("requirement"),
                "n_instances": group.get("n_instances"),
                "label": label,
            }
        )
    counts = Counter(row["label"] for row in selectivity)
    n_groups = len(groups) or 1
    tds = "TRIGGER" if per_seam.get("S-FARM-TDS-STAGE", {}).get("hit") else "MISS"
    if tds == "MISS" and distinctions.get("candidate_correspondence") and distinctions.get("period_or_interval"):
        if "70295" in text or "tds" in text:
            tds = "SPINE_HAS_DATES_NO_HOLE"
    return {
        "trial": f"T{index}",
        "ok": trial.get("final", {}).get("ok"),
        "n_iterations": trial.get("n_iterations"),
        "n_hole_groups": trial.get("final", {}).get("n_hole_groups") or 0,
        "n_hole_instances": trial.get("final", {}).get("n_hole_instances") or 0,
        "e1_primary_hits": hits,
        "e1_primary_n": len(primary),
        "e1_recall": hits / len(primary) if primary else None,
        "per_seam": per_seam,
        "e4_counts": dict(counts),
        "e4_purpose_relevant_rate": counts["PURPOSE_RELEVANT"] / n_groups if groups else None,
        "e4_groups": selectivity,
        "e2_distinctions": distinctions,
        "e2_n_true": sum(1 for v in distinctions.values() if v),
        "tds": tds,
        "when_discharging": bool(per_seam.get("S-AZTEC-WHEN-DISCHARGING", {}).get("hit")),
        "authority": bool(per_seam.get("S-SOURCE-AUTHORITY", {}).get("hit")),
        "hardcode_flags": hardcode_flags(code),
        "first_failure": first_failure(trial, distinctions, exploration),
        "exploration": {
            "n_reads": len(exploration.get("reads") or []),
            "read_basenames": sorted({Path(p).name for p in (exploration.get("reads") or [])})[:40],
            "n_shells": len(exploration.get("shells") or []),
            "shell_sample": (exploration.get("shells") or [])[:12],
        },
        "relation_row_counts": trial.get("final", {}).get("relation_row_counts") or {},
        "requirement_names": trial.get("final", {}).get("requirement_names") or [],
        "construction_n_lines": len(code.splitlines()),
    }


def e5_stability(trial_scores: list[dict]) -> dict[str, Any]:
    keys = list((trial_scores[0].get("e2_distinctions") or {}).keys()) if trial_scores else []
    stable = {}
    for key in keys:
        vals = [bool((t.get("e2_distinctions") or {}).get(key)) for t in trial_scores]
        stable[key] = {"n_true": sum(vals), "stable": len(set(vals)) == 1}
    return {"distinctions": stable}


def choose_label(mean_e1: float, mean_e2: float, n_ok: int, when_hits: int, cand_n: int) -> str:
    if n_ok < 3:
        return "MIXED_PURPOSE_FIRST_PYTHON_RESULT"
    strong_spine = mean_e2 >= 5 and cand_n >= 3
    high_recall = mean_e1 >= 0.7
    if n_ok >= 4 and strong_spine and high_recall:
        return "PURPOSE_FIRST_PYTHON_SPINE_SUPPORTED"
    if n_ok >= 4 and strong_spine and mean_e1 < 0.4:
        return "PHYSICAL_CONFUND_REMOVED_SEMANTIC_AUTHORING_WEAK"
    if cand_n <= 1 and n_ok >= 4:
        return "EXPLORATION_INSUFFICIENT"
    return "MIXED_PURPOSE_FIRST_PYTHON_RESULT"


def score_campaign() -> dict[str, Any]:
    freeze = load_json(FROZEN / "triggerability.json")
    baselines = load_json(FROZEN / "baselines.json")
    trials = [score_trial(i, freeze) for i in range(1, 6) if (RUNS / f"T{i}" / "trial.json").exists()]
    n = len(trials) or 1
    mean_e1 = sum(t["e1_recall"] or 0 for t in trials) / n
    mean_e2 = sum(t["e2_n_true"] for t in trials) / n
    mean_groups = sum(t["n_hole_groups"] for t in trials) / n
    mean_instances = sum(t["n_hole_instances"] for t in trials) / n
    n_ok = sum(1 for t in trials if t.get("ok"))
    cand_n = sum(1 for t in trials if (t.get("e2_distinctions") or {}).get("candidate_correspondence"))
    when_hits = sum(1 for t in trials if t.get("when_discharging"))
    special = {}
    for gid in [
        "S-FARM-TDS-STAGE",
        "S-SOURCE-AUTHORITY",
        "S-AZTEC-WHEN-DISCHARGING",
        "S-FARM-REPORT-ONLY",
        "S-AZTEC-REPORT-ONLY",
        "S-GCC-REPORT-ONLY",
        "S-GCC-EVENT-DISCHARGE",
        "S-FARM-TRC-CONDITIONAL",
        "S-AZTEC-WET-SEASONAL",
        "S-GCC-WET-FIRST-DISCHARGE",
        "S-AZTEC-DELTA-BHC",
        "S-FARM-CN-SCHEDULE",
    ]:
        special[gid] = {
            "hits": sum(1 for t in trials if (t.get("per_seam") or {}).get(gid, {}).get("hit")),
            "n": len(trials),
        }
    return {
        "experiment_id": "npdes-purpose-first-python-spine-v1",
        "n_trials": len(trials),
        "n_ok": n_ok,
        "e1_mean_recall": mean_e1,
        "e2_mean_distinctions": mean_e2,
        "e3_mean_groups": mean_groups,
        "e3_mean_instances": mean_instances,
        "e5": e5_stability(trials),
        "special_traces": special,
        "n_candidate_materialized": cand_n,
        "label": choose_label(mean_e1, mean_e2, n_ok, when_hits, cand_n),
        "baselines": baselines,
        "trials": trials,
    }
