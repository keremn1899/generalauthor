"""Evaluator-only scoring for untouched NPDES Constructor v3.1.1. Not visible to constructor workspaces."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.purpose_abi import (
    check_purpose_abi,
)
from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.score import (
    agent_record,
    load_json,
    snapshot,
    walk_strings,
    world_stats,
)

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
EVAL = NPDES / "fixture" / "evaluator_only"
TRIALS = ROOT / "trials"
REPORTS = ROOT / "reports"
MANIFESTS = NPDES / "fixture" / "manifests"

GOLD_S_NEEDLES = {
    "S-FARM-TDS-STAGE": ["tds", "net increase", "*10", "*11", "24992", "staged", "three year", "3 year"],
    "S-FARM-CN-SCHEDULE": ["cyanide", "compliance schedule", "12 month"],
    "S-FARM-TRC-CONDITIONAL": ["trc", "residual chlorine", "chlorine is used", "uv disinfection"],
    "S-FARM-REPORT-ONLY": ["report-only", "report only", "report rather", "n/a"],
    "S-AZTEC-WHEN-DISCHARGING": ["when discharging", "when-discharging", "intermittent"],
    "S-AZTEC-REPORT-ONLY": ["cyanide", "tds", "report"],
    "S-AZTEC-WET-SEASONAL": ["wet", "spring", "irrigation", "once per permit", "ceriodaphnia", "pimephales"],
    "S-AZTEC-DELTA-BHC": ["delta-bhc", "delta bhc", "special study", "source water intake"],
    "S-GCC-EVENT-DISCHARGE": ["storm", "event", "once-through", "artesian", "when discharging"],
    "S-GCC-REPORT-ONLY": ["dissolved copper", "dissolved cadmium", "hardness", "report", "50 mg"],
    "S-GCC-WET-FIRST-DISCHARGE": ["first discharge", "once/5", "wet"],
    "S-SOURCE-AUTHORITY": ["fact sheet", "statement of basis", "operative", "rationale", "authority"],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def as_list(payload: Any, *keys: str) -> list:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return []
    return []


def key_tuple(row: dict[str, Any]) -> tuple[str, str, str, str] | None:
    permit = (
        row.get("permit_number")
        or row.get("facility_permit_number")
        or row.get("permit")
        or row.get("permit_nbr")
        or row.get("npdes")
        or row.get("facility")
    )
    if isinstance(permit, str) and ":" in permit and permit.split(":")[-1].startswith("NM"):
        permit = permit.split(":")[-1]
    outfall = (
        row.get("feature_number")
        or row.get("discharge_point")
        or row.get("outfall")
        or row.get("perm_feature_nbr")
        or row.get("feature")
    )
    if isinstance(outfall, str) and ":" in outfall and not outfall.replace(":", "").isalnum():
        # referent ids like discharge_point:NM0000116:3600545262 — prefer numeric feature if present
        pass
    parameter = (
        row.get("parameter_code")
        or row.get("parameter")
        or row.get("parameter_desc")
    )
    if isinstance(parameter, str) and parameter.startswith("parameter:"):
        parameter = parameter.split(":", 1)[1]
    period = (
        row.get("period_end_date")
        or row.get("monitoring_period_end")
        or row.get("monitoring_period")
        or row.get("period")
        or row.get("monitoring_period_end_date")
    )
    if isinstance(period, str) and "monitoring_period:" in period:
        period = period.rsplit(":", 1)[-1]
    if not permit or parameter is None or period is None:
        return None
    period_s = str(period).replace("/", "-")[:10]
    outfall_s = str(outfall or "").strip()
    if ":" in outfall_s and outfall_s.split(":")[0] in {"discharge_point", "feature"}:
        outfall_s = outfall_s.split(":")[-1]
        if len(outfall_s) > 6:
            outfall_s = row.get("feature_number") or outfall_s
    param_s = str(parameter).strip()
    permit_s = str(permit).strip()
    if permit_s.startswith("facility:"):
        permit_s = permit_s.split(":", 1)[1]
    return (permit_s, str(outfall_s).strip(), param_s, period_s)


def truthy_exceedance(row: dict[str, Any]) -> bool | None:
    for key in (
        "exceedance_outcome",
        "exceeds_limit",
        "exceeds",
        "exceedance",
        "mechanical_exceedance",
        "exceeded",
        "is_exceedance",
        "comparison_outcome",
    ):
        if key not in row:
            continue
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"", "null", "none", "n/a", "na", "unresolved"}:
            continue
        if text in {"true", "yes", "exceedance", "exceeded", "1", "violation", "exceeds", "exceeds_limit"}:
            return True
        if text in {
            "false",
            "no",
            "0",
            "within_limit",
            "within",
            "compliant",
            "not_exceeded",
            "does_not_exceed",
            "comparison_not_applicable",
            "no_numeric_comparison",
        }:
            return False
        if "does_not" in text or "not_exceed" in text or "within" in text:
            return False
        if "exceed" in text:
            return True
        return False
    applicable = row.get("numeric_comparison_applicable")
    if applicable is False or str(applicable).lower() in {"false", "no"}:
        return False
    return None


def report_only_flag(row: dict[str, Any]) -> bool | None:
    for key in ("report_only", "comparison_class", "numeric_comparison_applicable", "limit_class"):
        if key not in row:
            continue
        value = row.get(key)
        text = str(value).strip().lower()
        if key == "numeric_comparison_applicable":
            if value is False or text in {"false", "no"}:
                return True
            if value is True or text in {"true", "yes"}:
                return False
        if "report" in text or text in {"no_numeric_comparison", "not_enforceable"}:
            return True
    return None


def c_state(row: dict[str, Any]) -> str:
    blob = " ".join(
        str(row.get(k) or "")
        for k in (
            "established_missing_evidence_state",
            "missing_evidence_state",
            "state",
            "classification",
            "nodi_code",
            "rationale",
            "blocking_state",
        )
    ).lower()
    if "no_discharge" in blob or "no-discharge" in blob or "nodi_code=c" in blob or blob.strip() == "c":
        return "ESTABLISHED_NO_DISCHARGE"
    if "not_required" in blob or "not required" in blob or "nodi" in blob and "9" in blob:
        return "ESTABLISHED_MONITORING_NOT_REQUIRED"
    if "observation" in blob or "present" in blob:
        return "OBSERVATION_PRESENT"
    if "missing" in blob and "required" in blob:
        return "REQUIRED_MONITORING_MISSING"
    if "unresolved" in blob:
        return "UNRESOLVED"
    return "OTHER"


def score_frontier(trial: int) -> dict[str, Any]:
    gold_s = load_json(EVAL / "gold_s.json") or {}
    clauses = gold_s.get("clauses") or []
    obligations = as_list(load_json(snapshot(trial, "p3") / "03_obligations.json"), "obligations", "items")
    blob = walk_strings(obligations).lower()
    hits = []
    misses = []
    for clause in clauses:
        cid = clause.get("id")
        needles = GOLD_S_NEEDLES.get(cid, [])
        found = any(n in blob for n in needles if len(n) >= 6)
        if not found:
            concept = str(clause.get("concept_governed") or "").lower()
            words = [w for w in concept.replace("/", " ").replace("-", " ").split() if len(w) > 4]
            found = bool(words) and all(k in blob for k in words[:2])
        record = {"id": cid, "concept": clause.get("concept_governed"), "found": found}
        (hits if found else misses).append(record)
    rels = Counter()
    for item in obligations:
        if isinstance(item, dict):
            rels[str(item.get("relation") or item.get("relation_name") or "unknown")] += 1
    return {
        "n_obligations": len(obligations),
        "required_clauses": len(clauses),
        "hits": hits,
        "misses": misses,
        "recall": (len(hits) / len(clauses)) if clauses else None,
        "obligation_relations": dict(rels),
        "duplicate_ids": sum(1 for n in Counter(i.get("obligation_id") for i in obligations if isinstance(i, dict)).values() if n > 1),
    }


def vocab_summary(trial: int) -> dict[str, Any]:
    vocab = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or {}
    relations = as_list(vocab, "relations")
    by_admission: dict[str, list[str]] = defaultdict(list)
    by_class: dict[str, list[str]] = defaultdict(list)
    invented = []
    for row in relations:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "")
        admission = str(row.get("admission") or "").upper()
        cls = str(row.get("construction_class") or "").upper()
        by_admission[admission].append(name)
        by_class[cls].append(name)
        invented.append(
            {
                "name": name,
                "admission": admission,
                "construction_class": cls,
                "meaning": row.get("meaning"),
                "classification": classify_relation(name, str(row.get("meaning") or "")),
            }
        )
    return {
        "n_relations": len(relations),
        "by_admission": {k: v for k, v in by_admission.items()},
        "by_class": {k: v for k, v in by_class.items()},
        "relations": invented,
        "limitations": vocab.get("limitations") if isinstance(vocab, dict) else None,
    }


def classify_relation(name: str, meaning: str) -> str:
    text = f"{name} {meaning}".lower()
    structural = (
        "identity",
        "referent",
        "grounding",
        "candidate",
        "in_scope",
        "derivation",
        "join",
        "scope",
    )
    domain = (
        "dmr",
        "permit",
        "outfall",
        "npdes",
        "nodi",
        "effluent",
        "limit",
        "monitoring",
        "discharge",
        "wet",
        "exceed",
    )
    if any(tok in text for tok in domain):
        return "DOMAIN_SPECIFIC"
    if any(tok in text for tok in structural):
        return "CROSS_DOMAIN_STRUCTURAL_ANALOGUE"
    return "CROSS_DOMAIN_STRUCTURAL_ANALOGUE"


def world_detail(trial: int) -> dict[str, Any]:
    p6 = snapshot(trial, "p6")
    p8 = snapshot(trial, "p8")
    world = p8 / "06_world" / "world.sqlite"
    if not world.exists():
        world = p6 / "06_world" / "world.sqlite"
    stats = world_stats(world)
    tables: dict[str, int] = {}
    columns: dict[str, list[str]] = {}
    if world.exists():
        conn = sqlite3.connect(str(world))
        try:
            names = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            for name in names:
                try:
                    n = conn.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
                    info = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
                except sqlite3.Error:
                    continue
                tables[name] = n
                columns[name] = [c[1] for c in info]
        finally:
            conn.close()
    mech = load_json(snapshot(trial, "p2") / "02_mechanical_report.json") or {}
    admission = load_json(p6 / "06_admission.json") or {}
    provenance = load_json(p8 / "06_provenance.json") or load_json(p6 / "06_provenance.json") or {}
    origins = world.parent / (world.name + ".origins.json")
    return {
        "world_path": str(world),
        "hash": sha256_file(world) if world.exists() else None,
        "stats": stats,
        "tables": tables,
        "columns": {k: v for k, v in columns.items() if not k.startswith("_tv_")},
        "mechanical_report": {
            "referents": mech.get("referents"),
            "base_tuples": mech.get("base_tuples"),
            "candidate_tuples": mech.get("candidate_tuples"),
            "notes": mech.get("notes"),
            "compile_stats": mech.get("compile_stats"),
            "relations": mech.get("relations"),
        },
        "admission_persisted": [
            {
                "relation": r.get("relation"),
                "admission": r.get("admission"),
                "construction_class": r.get("construction_class"),
                "persisted_count": r.get("persisted_count"),
            }
            for r in as_list(admission, "admissions")
            if isinstance(r, dict)
        ],
        "admission_limitations": admission.get("limitations") if isinstance(admission, dict) else None,
        "provenance": {
            "ok": provenance.get("ok"),
            "ungrounded_count": provenance.get("ungrounded_count"),
            "reason": provenance.get("reason"),
        },
        "origins_sidecar_present": origins.exists(),
    }


def p5_summary(trial: int) -> dict[str, Any]:
    dispositions = as_list(load_json(snapshot(trial, "p5") / "05_dispositions.json"), "dispositions")
    audit = as_list(load_json(snapshot(trial, "p5") / "05_adjudication_audit.json"), "items", "audits")
    disp = Counter(str(r.get("disposition") or "").upper() for r in dispositions if isinstance(r, dict))
    final = Counter(str(r.get("final_disposition") or "").upper() for r in audit if isinstance(r, dict))
    neg = Counter(str(r.get("negative_closure") or "none") for r in audit if isinstance(r, dict))
    return {
        "n_dispositions": len(dispositions),
        "dispositions": dict(disp),
        "n_audit": len(audit),
        "final_dispositions": dict(final),
        "negative_closure": dict(neg),
    }


def score_purpose_a(trial: int) -> dict[str, Any]:
    gold = load_json(EVAL / "gold_m.json") or {}
    gold_rows = [r for r in gold.get("rows") or [] if isinstance(r, dict)]
    gold_by_key = {}
    for row in gold_rows:
        gold_by_key[key_tuple(row)] = row
    payload = load_json(snapshot(trial, "p8") / "08_outputs" / "a.json") or {}
    rows = as_list(payload, "rows")
    unresolved = as_list(payload, "unresolved")
    compared = 0
    exact = 0
    report_only_as_exceedance = 0
    miss_exceedance = 0
    false_exceedance = 0
    covered_scoreable = 0
    examples: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = key_tuple(row)
        gold_row = gold_by_key.get(key)
        if not gold_row:
            continue
        if gold_row.get("scoreable"):
            covered_scoreable += 1
        pred = truthy_exceedance(row)
        gold_ex = gold_row.get("mechanical_exceedance")
        pred_report = report_only_flag(row)
        if gold_row.get("report_only") and pred is True:
            report_only_as_exceedance += 1
            if len(examples) < 12:
                examples.append({"kind": "report_only_as_exceedance", "key": key, "row": {k: row.get(k) for k in list(row)[:8]}})
        if gold_row.get("scoreable") and gold_row.get("oracle_conflict"):
            continue
        if gold_row.get("scoreable") and gold_ex is not None and pred is not None:
            compared += 1
            if bool(pred) == bool(gold_ex):
                exact += 1
            elif pred and not gold_ex:
                false_exceedance += 1
            elif gold_ex and not pred:
                miss_exceedance += 1
    n_scoreable = sum(1 for r in gold_rows if r.get("scoreable") and not r.get("oracle_conflict"))
    return {
        "n_rows": len(rows),
        "n_unresolved": len(unresolved),
        "scoreable_covered": covered_scoreable,
        "n_scoreable": n_scoreable,
        "compared": compared,
        "exact": exact,
        "exact_rate": (exact / compared) if compared else None,
        "false_exceedance": false_exceedance,
        "miss_exceedance": miss_exceedance,
        "report_only_as_exceedance": report_only_as_exceedance,
        "examples": examples,
        "has_incomplete_purpose": "INCOMPLETE_PURPOSE" in json.dumps(payload)[:2000],
    }


def score_purpose_c(trial: int) -> dict[str, Any]:
    gold = load_json(EVAL / "gold_e.json") or {}
    gold_rows = [r for r in gold.get("rows") or [] if isinstance(r, dict)]
    gold_by_key = {key_tuple(r): r for r in gold_rows}
    payload = load_json(snapshot(trial, "p8") / "08_outputs" / "c.json") or {}
    rows = as_list(payload, "rows")
    unresolved = as_list(payload, "unresolved")
    matched = 0
    exact = 0
    missing_as_violation = 0
    nodi_c_as_violation = 0
    nodi_c_established = 0
    nodi_9_established = 0
    unresolved_keys = {key_tuple(r) for r in unresolved if isinstance(r, dict)}
    for row in rows + unresolved:
        if not isinstance(row, dict):
            continue
        key = key_tuple(row)
        gold_row = gold_by_key.get(key)
        in_unresolved = key in unresolved_keys or row in unresolved
        state = "UNRESOLVED" if in_unresolved else c_state(row)
        if gold_row:
            matched += 1
            gold_state = gold_row.get("state")
            if state == gold_state:
                exact += 1
            if gold_state == "ESTABLISHED_NO_DISCHARGE" and state == "ESTABLISHED_NO_DISCHARGE":
                nodi_c_established += 1
            if gold_state == "ESTABLISHED_MONITORING_NOT_REQUIRED" and state == "ESTABLISHED_MONITORING_NOT_REQUIRED":
                nodi_9_established += 1
            if gold_state in {"ESTABLISHED_NO_DISCHARGE", "ESTABLISHED_MONITORING_NOT_REQUIRED"} and state == "REQUIRED_MONITORING_MISSING":
                missing_as_violation += 1
            if gold_row.get("nodi_code") == "C" and state == "REQUIRED_MONITORING_MISSING":
                nodi_c_as_violation += 1
        if not gold_row and state == "REQUIRED_MONITORING_MISSING" and not in_unresolved:
            missing_as_violation += 1
    return {
        "n_rows": len(rows),
        "n_unresolved": len(unresolved),
        "matched_keys": matched,
        "exact_state": exact,
        "nodi_c_established": nodi_c_established,
        "nodi_9_established": nodi_9_established,
        "missing_as_violation": missing_as_violation,
        "nodi_c_as_violation": nodi_c_as_violation,
        "gold_by_state": gold.get("by_state"),
    }


def score_purpose_b(trial: int) -> dict[str, Any]:
    payload = load_json(snapshot(trial, "p8") / "08_outputs" / "b.json") or {}
    rows = as_list(payload, "rows")
    unresolved = as_list(payload, "unresolved")
    blob = walk_strings(payload).lower()
    concepts = {
        "when_discharging": any(t in blob for t in ("when discharging", "when-discharging", "intermittent", "nodi")),
        "report_only": "report" in blob,
        "seasonal_or_wet": any(t in blob for t in ("wet", "season", "spring", "irrigation")),
        "special_study": any(t in blob for t in ("study", "delta", "bhc", "schedule")),
        "conditional": any(t in blob for t in ("conditional", "event", "chlorine", "first discharge")),
        "staged_time": any(t in blob for t in ("stage", "effective", "tds", "fy2025")),
    }
    return {
        "n_rows": len(rows),
        "n_unresolved": len(unresolved),
        "concept_mentions": concepts,
        "n_concepts_present": sum(1 for v in concepts.values() if v),
    }


def abi_summary(trial: int) -> dict[str, Any]:
    p8 = snapshot(trial, "p8")
    recorded = load_json(p8 / "08_abi_completeness.json") or {}
    live_world = p8 / "06_world" / "world.sqlite"
    # Re-check SATISFIED => bound table nonempty using recorded fields.
    violations = []
    for field, info in (recorded.get("fields") or {}).items():
        if not isinstance(info, dict):
            continue
        if info.get("status") != "SATISFIED":
            continue
        locs = info.get("locations") or []
        tables = {loc.split(".", 1)[0] for loc in locs if "." in loc}
        nonempty = False
        if live_world.exists() and tables:
            conn = sqlite3.connect(str(live_world))
            try:
                for table in tables:
                    try:
                        n = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
                    except sqlite3.Error:
                        n = 0
                    if n:
                        nonempty = True
                        break
            finally:
                conn.close()
        if tables and not nonempty:
            violations.append({"field": field, "locations": locs})
    return {
        "ok": recorded.get("ok"),
        "n_required": len(recorded.get("required_semantic_fields") or []),
        "n_satisfied": len(recorded.get("satisfied") or []),
        "n_unsatisfied": len(recorded.get("unsatisfied") or []),
        "n_ambiguous": len(recorded.get("ambiguous") or []),
        "unsatisfied": recorded.get("unsatisfied"),
        "ambiguous": recorded.get("ambiguous"),
        "unsatisfied_reasons": recorded.get("unsatisfied_reasons"),
        "invariant_violations": violations,
        "incomplete_purpose_marked": False,
    }


def isolation_summary(trial: int) -> dict[str, Any]:
    leaks = []
    timeouts = []
    models = []
    reported = []
    rcs = []
    p8_paths = []
    for pass_id in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"):
        rec = agent_record(trial, pass_id)
        leaks.extend(rec.get("isolation_leaks") or [])
        if rec.get("timed_out"):
            timeouts.append(pass_id)
        models.append(rec.get("model"))
        reported.append(rec.get("reported_model"))
        rcs.append(rec.get("returncode"))
        if pass_id == "p8":
            p8_paths = ((rec.get("tools") or {}).get("mentioned_paths") or [])
    source_reread = [p for p in p8_paths if "sources/" in str(p) or str(p).endswith(".pdf") or "dmr_measurements" in str(p)]
    return {
        "leaks": leaks,
        "timeouts": timeouts,
        "models": sorted(set(x for x in models if x)),
        "reported_models": sorted(set(x for x in reported if x)),
        "all_returncode_zero": all(c == 0 for c in rcs if c is not None) and len(rcs) == 9,
        "p8_source_path_mentions": source_reread,
    }


def source_authority(trial: int) -> dict[str, Any]:
    parts = []
    for pass_id in ("p1", "p3", "p5", "p6"):
        snap = snapshot(trial, pass_id)
        for name in ("01_vocabulary.json", "03_obligations.json", "05_dispositions.json", "06_admission.json"):
            path = snap / name
            if path.exists():
                parts.append(path.read_text(errors="replace")[:2_000_000])
    blob = "\n".join(parts).lower()
    return {
        "mentions_fact_sheet": "fact sheet" in blob or "fact_sheet" in blob,
        "mentions_statement_of_basis": "statement of basis" in blob or "statement_of_basis" in blob,
        "mentions_operative_or_authority": any(t in blob for t in ("operative", "authority", "supporting rationale", "not an independent")),
        "mentions_permit_part": "part i" in blob or "permit part" in blob,
    }


def programming_over_world(trial: int) -> dict[str, Any]:
    """Three SQL analyses over World only. No CSV/PDF."""
    world = snapshot(trial, "p8") / "06_world" / "world.sqlite"
    vocab = load_json(snapshot(trial, "p1") / "01_vocabulary.json") or {}
    relations = as_list(vocab, "relations")
    bindings: dict[str, list[tuple[str, str]]] = defaultdict(list)
    table_by_name = {}
    for row in relations:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "")
        table_by_name[name] = row
        for role in row.get("roles") or []:
            if isinstance(role, dict) and role.get("semantic_identity"):
                bindings[str(role["semantic_identity"])].append((name, str(role.get("name") or "")))
    if not world.exists():
        return {"ok": False, "reason": "missing_world"}
    conn = sqlite3.connect(str(world))
    conn.row_factory = sqlite3.Row
    user_tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_tv_%'"
        )
    ]

    def cols(table: str) -> set[str]:
        try:
            return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        except sqlite3.Error:
            return set()

    def pick_table(*names: str) -> str | None:
        for name in names:
            if name in user_tables:
                return name
        return None

    measure = pick_table(
        "reported_dmr_measurement",
        "dmr_measurement_assertion",
        "dmr_measurement_extract_row",
        "reported_measurement_stated",
        "dmr_measurement",
    )
    if measure is None:
        for table in user_tables:
            c = cols(table)
            if any(x in c for x in ("dmr_value_nbr", "reported_value", "value_nbr")) and any(
                x in c for x in ("permit_nbr", "facility", "npdes")
            ):
                measure = table
                break
    limit = pick_table(
        "permit_limit_schedule_row",
        "permit_limit_assertion",
        "permit_limit_extract_row",
        "permit_limit_value_stated",
        "permit_limit",
    )
    if limit is None:
        for table in user_tables:
            c = cols(table)
            if any(x in c for x in ("limit_value_nbr", "limit_value_nmbr", "limit_value")):
                limit = table
                break

    recovered_semantics = []
    analyses: dict[str, Any] = {}
    nodi = None
    val = None

    # Analysis 1: numeric exceedance where both values exist.
    if measure and limit:
        mc, lc = cols(measure), cols(limit)
        m_val = next((c for c in ("dmr_value_nbr", "reported_value", "value_nbr", "value") if c in mc), None)
        l_val = next((c for c in ("limit_value_nbr", "limit_value_nmbr", "limit_value", "numeric_limit") if c in lc), None)
        m_permit = next((c for c in ("permit_nbr", "facility", "npdes") if c in mc), None)
        l_permit = next((c for c in ("permit_nbr", "facility", "npdes") if c in lc), None)
        m_feat = next((c for c in ("perm_feature_nbr", "discharge_point", "outfall") if c in mc), None)
        l_feat = next((c for c in ("perm_feature_nbr", "discharge_point", "outfall") if c in lc), None)
        m_par = next((c for c in ("parameter_code", "parameter") if c in mc), None)
        l_par = next((c for c in ("parameter_code", "parameter") if c in lc), None)
        m_per = next((c for c in ("monitoring_period_end", "monitoring_period") if c in mc), None)
        if all([m_val, l_val, m_permit, l_permit, m_par, l_par]):
            join = f'm."{m_permit}" = l."{l_permit}" AND m."{m_par}" = l."{l_par}"'
            if m_feat and l_feat:
                join += f' AND m."{m_feat}" = l."{l_feat}"'
            optional = next((c for c in ("optional_monitoring_flag", "optional_monitoring") if c in lc), None)
            opt_clause = f' AND (l."{optional}" IS NULL OR l."{optional}" NOT IN (\'Y\', \'y\', \'1\', 1))' if optional else ""
            sql = (
                f'SELECT m."{m_permit}" permit, '
                + (f'm."{m_feat}" outfall, ' if m_feat else "'?' outfall, ")
                + f'm."{m_par}" parameter, '
                + (f'm."{m_per}" period, ' if m_per else "NULL period, ")
                + f'm."{m_val}" reported, l."{l_val}" limit_value '
                f'FROM "{measure}" m JOIN "{limit}" l ON {join} '
                f'WHERE m."{m_val}" IS NOT NULL AND l."{l_val}" IS NOT NULL '
                f'AND CAST(m."{m_val}" AS REAL) > -1e30 AND CAST(l."{l_val}" AS REAL) > -1e30 '
                f'AND CAST(m."{m_val}" AS REAL) > CAST(l."{l_val}" AS REAL)'
                f"{opt_clause}"
            )
            try:
                rows = [dict(r) for r in conn.execute(sql).fetchall()]
            except sqlite3.Error as exc:
                rows = []
                recovered_semantics.append(f"analysis_1_sql_error:{exc}")
            analyses["exceedance"] = {
                "sql_ok": True,
                "n": len(rows),
                "sample": rows[:8],
                "tables": {"measurement": measure, "limit": limit},
            }
        else:
            analyses["exceedance"] = {"sql_ok": False, "reason": "missing_join_columns", "measure_cols": sorted(mc), "limit_cols": sorted(lc)}
            recovered_semantics.append("need_column_map_for_numeric_limit_join")
    else:
        analyses["exceedance"] = {"sql_ok": False, "reason": "missing_measurement_or_limit_table", "tables": user_tables}
        recovered_semantics.append("no_measurement_or_limit_table")

    # Analysis 2: NODI / missing-evidence states from stored codes.
    if measure:
        mc = cols(measure)
        nodi = next((c for c in ("nodi_code", "NODI_CODE", "no_data_indicator") if c in mc), None)
        val = next((c for c in ("dmr_value_nbr", "value", "reported_value") if c in mc), None)
        if nodi:
            sql = f'SELECT "{nodi}" nodi, count(*) n FROM "{measure}" GROUP BY 1'
            by = {str(r["nodi"]): r["n"] for r in conn.execute(sql)}
            # Programmer maps C/9 using EPA code knowledge if World stores only the code.
            if any(k in {"C", "9", "c"} for k in by):
                recovered_semantics.append("NODI_CODE_STORED_WITHOUT_CANONICAL_STATE_RELATION")
            analyses["evidence_state"] = {"sql_ok": True, "nodi_counts": by, "has_value_column": bool(val)}
        else:
            analyses["evidence_state"] = {"sql_ok": False, "reason": "no_nodi_column", "cols": sorted(mc)}
            recovered_semantics.append("nodi_not_in_world_schema")
    else:
        analyses["evidence_state"] = {"sql_ok": False, "reason": "no_measurement_table"}

    # Analysis 3: follow-up = numeric exceedance union missing numeric without NODI C/9.
    follow = {"sql_ok": False}
    if measure and analyses.get("exceedance", {}).get("sql_ok") and nodi and val:
        mc = cols(measure)
        permit = next((c for c in ("permit_nbr", "facility") if c in mc), None)
        feat = next((c for c in ("perm_feature_nbr", "discharge_point") if c in mc), None)
        par = next((c for c in ("parameter_code", "parameter") if c in mc), None)
        period = next((c for c in ("monitoring_period_end", "monitoring_period") if c in mc), None)
        if permit and par:
            sql = (
                f'SELECT "{permit}" permit, '
                + (f'"{feat}" outfall, ' if feat else "'?' outfall, ")
                + f'"{par}" parameter, '
                + (f'"{period}" period, ' if period else "NULL period, ")
                + f'"{nodi}" nodi, "{val}" reported '
                f'FROM "{measure}" '
                f'WHERE ("{val}" IS NULL OR CAST("{val}" AS REAL) <= -1e30) '
                f'AND IFNULL("{nodi}", "") NOT IN (\'C\', \'9\', \'c\')'
            )
            try:
                missing = [dict(r) for r in conn.execute(sql).fetchall()]
                follow = {
                    "sql_ok": True,
                    "n_exceedance": analyses["exceedance"]["n"],
                    "n_missing_without_c_or_9": len(missing),
                    "sample_missing": missing[:8],
                    "note": "Follow-up is the union of numeric exceedance and missing values that are not NODI C/9. Report-only exclusion requires a World flag; OPTIONAL_MONITORING_FLAG used when present.",
                }
            except sqlite3.Error as exc:
                follow = {"sql_ok": False, "reason": str(exc)}
    analyses["follow_up"] = follow
    conn.close()
    n_ok = sum(1 for k in ("exceedance", "evidence_state", "follow_up") if analyses.get(k, {}).get("sql_ok"))
    return {
        "ok": n_ok == 3,
        "n_analyses_ok": n_ok,
        "user_tables": user_tables,
        "bindings_sample": {k: v[:4] for k, v in list(bindings.items())[:12]},
        "analyses": analyses,
        "programmer_recovered_source_semantics": recovered_semantics,
    }


def fractions(world: dict[str, Any], vocab: dict[str, Any]) -> dict[str, Any]:
    origin = (world.get("stats") or {}).get("by_origin") or {}
    asserted = int(origin.get("ASSERTED") or origin.get("asserted") or 0)
    derived = int(origin.get("DERIVED") or origin.get("derived") or 0)
    total = int((world.get("stats") or {}).get("assertions") or 0) or (asserted + derived)
    persisted = world.get("admission_persisted") or []
    mech = sum(int(r.get("persisted_count") or 0) for r in persisted if str(r.get("construction_class") or "").upper() == "MECHANICAL")
    sem = sum(int(r.get("persisted_count") or 0) for r in persisted if str(r.get("construction_class") or "").upper() == "SEMANTIC")
    der = sum(int(r.get("persisted_count") or 0) for r in persisted if str(r.get("construction_class") or "").upper() == "DERIVED")
    base = mech + sem
    return {
        "assertions_total": total,
        "origin_asserted": asserted,
        "origin_derived": derived,
        "persisted_mechanical": mech,
        "persisted_semantic": sem,
        "persisted_derived": der,
        "mechanical_fraction_of_persisted_base": (mech / base) if base else None,
        "semantic_fraction_of_persisted_base": (sem / base) if base else None,
        "mechanical_fraction_of_all_persisted": (mech / (mech + sem + der)) if (mech + sem + der) else None,
    }


def score_trial(trial: int) -> dict[str, Any]:
    vocab = vocab_summary(trial)
    world = world_detail(trial)
    return {
        "trial": trial,
        "isolation": isolation_summary(trial),
        "vocabulary": vocab,
        "world": world,
        "fractions": fractions(world, vocab),
        "frontier": score_frontier(trial),
        "p5": p5_summary(trial),
        "abi": abi_summary(trial),
        "source_authority": source_authority(trial),
        "purpose_a": score_purpose_a(trial),
        "purpose_b": score_purpose_b(trial),
        "purpose_c": score_purpose_c(trial),
        "programming": programming_over_world(trial),
    }


def freeze_worlds() -> dict[str, Any]:
    trials = {}
    for i in range(1, 6):
        p6 = snapshot(i, "p6") / "06_world" / "world.sqlite"
        p8 = snapshot(i, "p8") / "06_world" / "world.sqlite"
        vocab = snapshot(i, "p1") / "01_vocabulary.json"
        trials[f"T{i}"] = {
            "world_p6": sha256_file(p6) if p6.exists() else None,
            "world_p8": sha256_file(p8) if p8.exists() else None,
            "p6_eq_p8": sha256_file(p6) == sha256_file(p8) if p6.exists() and p8.exists() else None,
            "vocabulary": sha256_file(vocab) if vocab.exists() else None,
            "bytes_p8": p8.stat().st_size if p8.exists() else None,
        }
    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "note": "World freeze after A/B/C construction, before Purpose D is revealed to any consumer workspace.",
        "trials": trials,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "world_freeze.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    freeze = freeze_worlds()
    trials = {f"T{i}": score_trial(i) for i in range(1, 6)}
    payload = {
        "experiment_id": "npdes-constructor-v3-1-1-untouched",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model": "composer-2.5",
        "world_freeze": freeze,
        "trials": trials,
        "manifest": load_json(MANIFESTS / "manifest.json"),
    }
    dest = REPORTS / "evaluation.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"wrote": str(dest), "freeze": freeze["trials"]}, indent=2))
    return payload


if __name__ == "__main__":
    main()
