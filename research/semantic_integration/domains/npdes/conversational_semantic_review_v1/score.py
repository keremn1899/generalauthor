"""Qualitative scoring over sealed conversational traces. Proxy interaction, not human usability."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.hidden import PACKETS
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.paths import RUNS

ONTOLOGY_TERMS = (
    "require_interpreted",
    "require_unique",
    "referent(",
    "world.relation",
    "cardinality",
    "n-ary",
    "purpose.require",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": path.read_text(encoding="utf-8")[:4000]}


def conversation_blob(trial_dir: Path) -> str:
    parts = [_read(p) for p in sorted((trial_dir / "conversation").glob("*.md"))] if (trial_dir / "conversation").exists() else []
    parts.append(_read(trial_dir / "host.stdout.txt")[-30000:])
    return "\n".join(parts).lower()


def mp1_scores(trial_dir: Path) -> dict[str, Any]:
    blob = conversation_blob(trial_dir)
    records = {}
    rec_dir = trial_dir / "records"
    if rec_dir.exists():
        for path in rec_dir.glob("*.json"):
            records[path.stem] = _json(path)
    flags = {
        "FAITHFUL_TO_DECISION": any(tok in blob for tok in ("one", "unique", "governing")) and "nodi" in blob,
        "FAITHFUL_TO_EVIDENCE": ("when discharging" in blob or "comment" in blob) and ("c" in blob or "9" in blob or "nodi" in blob),
        "CONSEQUENCE_CLEAR": any(tok in blob for tok in ("compar", "applicab", "monitor", "limit")),
        "UNCERTAINTY_PRESERVED": any(tok in blob for tok in ("don't know", "do not know", "unresolved", "not know", "without")),
        "NON_ONTOLOGY_LANGUAGE": sum(blob.count(t) for t in ONTOLOGY_TERMS) < 8,
        "CORRECTABLE_BY_NORMAL_USER": "a)" not in blob and "option 1" not in blob and "choose one" not in blob,
        "ALTERNATIVES_PLAUSIBLE": any(tok in blob for tok in ("alternat", "another way", "or they could", "might instead")),
        "NO_INVENTED_RATIONALE": "no discharge occurred" not in blob and "means not required" not in blob,
    }
    asked_mechanical = "already determined" in blob or "already established" in blob
    return {
        "n_records": len(records),
        "n_explanations": len(list((trial_dir / "conversation").glob("*.md"))) if (trial_dir / "conversation").exists() else 0,
        "flags": flags,
        "asked_mechanical_as_if_open": asked_mechanical,
        "ontology_term_hits": {t: blob.count(t) for t in ONTOLOGY_TERMS if t in blob},
    }


def packet_recovery(reply: str, packet: dict) -> dict[str, Any]:
    text = (reply or "").lower()
    hits = []
    misses = []
    for dist in packet["distinctions"]:
        keys = [w for w in re.findall(r"[a-z0-9]{4,}", dist.lower()) if w not in {"that", "this", "with", "from", "they", "them", "have", "does", "into", "after"}]
        if sum(1 for k in keys[:6] if k in text) >= 2:
            hits.append(dist)
        else:
            misses.append(dist)
    boxed = bool(re.search(r"\b(i (will )?take|i choose|option [abc]|alternative [abc])\b", text))
    return {
        "n_distinctions": len(packet["distinctions"]),
        "n_recovered": len(hits),
        "recovered": hits,
        "missed": misses,
        "boxed_into_alternatives": boxed,
        "mentions_uncertainty": any(tok in text for tok in ("don't know", "do not know", "uncertain", "not sure")),
    }


def mp2_compare(cells: list[dict]) -> dict[str, Any]:
    by_issue: dict[str, dict] = {}
    for cell in cells:
        by_issue.setdefault(cell["issue_id"], {})[cell["condition"]] = cell
    rows = []
    for issue_id, pair in by_issue.items():
        packet = PACKETS[issue_id]
        open_r = packet_recovery((pair.get("OPEN") or {}).get("proxy_reply") or "", packet)
        near_r = packet_recovery((pair.get("NEAR") or {}).get("proxy_reply") or "", packet)
        rows.append(
            {
                "issue_id": issue_id,
                "open_recovered": open_r["n_recovered"],
                "near_recovered": near_r["n_recovered"],
                "near_minus_open": near_r["n_recovered"] - open_r["n_recovered"],
                "near_boxed": near_r["boxed_into_alternatives"],
                "open": open_r,
                "near": near_r,
            }
        )
    return {"issues": rows}


def classify_generalization(step: dict) -> str:
    interp = step.get("host_interpretation") or {}
    scope = str(interp.get("scope") or "").lower()
    changed = step.get("construction_changed")
    kind = step.get("kind")
    if kind == "UNCERTAINTY":
        return "UNRESOLVED"
    if kind == "AMBIGUOUS_REJECTION" and step.get("clarify"):
        return "UNRESOLVED"
    if not changed and kind == "ACCEPTANCE":
        return "APPROPRIATELY_LOCAL_RULE"
    if scope in {"one_source_value", "one_relation", "one_purpose"}:
        return "APPROPRIATE_REUSABLE_RULE" if "value" not in scope else "APPROPRIATELY_LOCAL_RULE"
    if scope == "one_occurrence":
        return "INSTANCE_MEMORIZATION"
    if scope == "general_world":
        return "OVERGENERALIZATION"
    return "UNRESOLVED"


def mp3_score(trial: dict) -> dict[str, Any]:
    steps = []
    for step in trial.get("steps") or []:
        interp = step.get("host_interpretation") or {}
        steps.append(
            {
                "id": step.get("id"),
                "kind": step.get("kind"),
                "intended_epistemic": step.get("epistemic"),
                "host_epistemic": interp.get("epistemic_kind"),
                "intended_scope": step.get("intended_scope"),
                "host_scope": interp.get("scope"),
                "n_turns": step.get("n_turns"),
                "clarify": step.get("clarify"),
                "construction_changed": step.get("construction_changed"),
                "rerun_ok": (step.get("rerun") or {}).get("ok"),
                "generalization": classify_generalization(step),
            }
        )
    return {"trial": trial.get("trial"), "steps": steps}
