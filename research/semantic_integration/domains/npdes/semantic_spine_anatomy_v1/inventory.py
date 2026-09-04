"""Extract program anatomy and normalized semantic inventories from sealed artifacts."""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.paths import PFPS_RUNS

CATS = [
    "SOURCE_IO",
    "SOURCE_PROFILING_OR_EXPLORATION",
    "PHYSICAL_NORMALIZATION",
    "GENERAL_HELPER_OR_CONTROL_FLOW",
    "REFERENT_DECLARATION",
    "RELATION_DECLARATION",
    "GROUNDING_OR_MAPPING",
    "MECHANICAL_DERIVATION",
    "PURPOSE_REQUIREMENT_SCHEMA",
    "PURPOSE_REQUIREMENT_INSTANTIATION",
    "UNRESOLVED_OR_HOLE_EMISSION",
    "REPORTING_DEBUGGING_OR_SERIALIZATION",
    "OTHER",
]

SEMANTIC_CATS = {
    "REFERENT_DECLARATION",
    "RELATION_DECLARATION",
    "GROUNDING_OR_MAPPING",
    "MECHANICAL_DERIVATION",
    "PURPOSE_REQUIREMENT_SCHEMA",
    "UNRESOLVED_OR_HOLE_EMISSION",
}
MECHANICAL_CATS = {
    "SOURCE_IO",
    "SOURCE_PROFILING_OR_EXPLORATION",
    "PHYSICAL_NORMALIZATION",
    "GENERAL_HELPER_OR_CONTROL_FLOW",
}
REQ_CATS = {"PURPOSE_REQUIREMENT_SCHEMA", "PURPOSE_REQUIREMENT_INSTANTIATION"}
HOLE_CATS = {"UNRESOLVED_OR_HOLE_EMISSION"}

REFERENT_NORM = {
    "measurement": "Measurement",
    "dmr_report": "Measurement",
    "dmr_measurement": "Measurement",
    "limit_value": "LimitValue",
    "limit": "Limit",
    "permit_limit_row": "LimitRow",
    "document": "Document",
    "source_document": "Document",
    "facility": "Facility",
    "permit": "Permit",
    "discharge_point": "Outfall",
    "feature": "Outfall",
    "parameter": "Parameter",
    "monitoring_period": "MonitoringPeriod",
    "monitoring_event": "MonitoringEvent",
    "monitoring_requirement": "MonitoringRequirement",
    "limit_set": "LimitSet",
    "limit_set_schedule": "LimitSchedule",
    "limit_schedule": "LimitSchedule",
}

REL_RULES = [
    ("DocumentInventory", lambda n: "document" in n or "inventory" in n or n.endswith("_catalog") and "document" in n),
    ("Fy2025Scope", lambda n: "fy2025" in n or "fy25" in n or "in_fy" in n),
    ("NumericComparison", lambda n: "numeric" in n and ("compar" in n or "candidate" in n)),
    ("ReportOnlyOrNonNumeric", lambda n: "non_numeric" in n or "without_numeric" in n),
    ("MissingEvidence", lambda n: "no_result" in n or "no_numeric" in n or "missing_result" in n),
    ("CandidateCorrespondence", lambda n: any(tok in n for tok in ("candidate", "evaluation", "schedule_match", "measurement_limit", "limit_active", "permit_match", "permit_link"))),
    ("EffectiveInterval", lambda n: "interval" in n or "effective" in n),
    ("SeasonalMonth", lambda n: "season" in n),
    ("MonitoringObligation", lambda n: "oblig" in n or "monitoring_requirement" in n),
    ("MeasurementBase", lambda n: "measurement" in n and "candidate" not in n and "fy" not in n),
    ("LimitBase", lambda n: "limit" in n and "candidate" not in n and "document" not in n),
    ("CommentPayload", lambda n: "comment" in n),
    ("CodePayload", lambda n: any(tok in n for tok in ("nodi", "qualifier", "optional_monitoring", "freq"))),
]


def _rel_norm(name: str) -> str:
    n = name.lower()
    for label, pred in REL_RULES:
        if pred(n):
            return label
    return "OtherRelation"


REQ_RULES = [
    ("unique_applicable_limit", lambda n: "unique" in n and ("limit" in n or "schedule" in n or "catalog" in n or "applicable" in n)),
    ("materializable_fy2025_measurements", lambda n: "materializable" in n and ("measur" in n or "fy" in n or "reported" in n)),
    ("materializable_candidates", lambda n: "materializable" in n and ("candidate" in n or "pair" in n or "evaluation" in n or "compar" in n)),
    ("materializable_documents", lambda n: "materializable" in n and "document" in n),
    ("materializable_no_result", lambda n: "materializable" in n and ("no_result" in n or "missing" in n or "no_numeric" in n)),
    ("materializable_monitoring", lambda n: "materializable" in n and ("monitor" in n or "oblig" in n)),
    ("interpret_nodi", lambda n: "nodi" in n),
    ("interpret_comment", lambda n: "comment" in n or "discharg" in n or "conditional" in n),
    ("interpret_optional_monitoring", lambda n: "optional" in n),
    ("interpret_qualifier", lambda n: "qualifier" in n),
    ("interpret_frequency", lambda n: "freq" in n),
    ("interpret_limit_type", lambda n: "limit_type" in n or "type_code" in n or "enforceability" in n),
    ("interpret_seasonal_month", lambda n: "season" in n or "month" in n),
    ("interpret_sample_type", lambda n: "sample_type" in n),
    ("interpret_unit", lambda n: "unit" in n),
    ("interpret_value_type", lambda n: "value_type" in n),
    ("interpret_statistical_base", lambda n: "statistical" in n or "stat_base" in n),
    ("numeric_limit", lambda n: "numeric" in n and "limit" in n),
    ("numeric_measurement", lambda n: "numeric" in n and ("measur" in n or "reported" in n or "dmr" in n)),
    ("report_only_gap", lambda n: "without_numeric" in n or "non_numeric" in n or "report_only" in n or "comparability" in n and "nmbr" in n),
    ("document_text_unavailable", lambda n: "document" in n and ("text" in n or "not_available" in n or "not_materialized" in n)),
    ("pass_fail_semantics", lambda n: "pass_fail" in n or "pass-fail" in n),
    ("aggregated_reporting", lambda n: "aggregat" in n or "geometric" in n),
]


def _req_norm(name: str) -> str:
    n = (name or "").lower()
    if n.startswith("seasonal_") and "monitoring" in n:
        return "interpret_seasonal_month"
    if "{month}" in n or n.startswith("seasonal_{"):
        return "interpret_seasonal_month"
    for label, pred in REQ_RULES:
        if pred(n):
            return label
    return "other_requirement"


def construction_path(trial: str) -> Path:
    return PFPS_RUNS / trial / "iter1" / "construction.py"


def spine_path(trial: str) -> Path:
    return PFPS_RUNS / trial / "iter1" / "spine.json"


def holes_path(trial: str) -> Path:
    return PFPS_RUNS / trial / "iter1" / "holes.json"


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_str_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    arg0 = node.args[0]
    direct = _const_str(arg0)
    if direct:
        return direct
    if isinstance(arg0, ast.JoinedStr):
        parts: list[str] = []
        for value in arg0.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
                parts.append("{" + value.value.id + "}")
            else:
                parts.append("{…}")
        return "".join(parts)
    return None


def classify_call(name: str) -> str | None:
    if name in {"rows", "document_inventory", "tables", "fields", "n_rows"}:
        return "SOURCE_IO"
    if name in {"profile", "distinct_values", "key_candidates", "value_overlap", "join_profile", "join"}:
        return "SOURCE_PROFILING_OR_EXPLORATION"
    if name in {"parse_date", "interval_contains", "looks_numeric", "_looks_numeric", "_text"}:
        return "PHYSICAL_NORMALIZATION"
    if name == "referent":
        return "REFERENT_DECLARATION"
    if name == "relation":
        return "RELATION_DECLARATION"
    if name == "map":
        return "GROUNDING_OR_MAPPING"
    if name == "derive":
        return "MECHANICAL_DERIVATION"
    if name in {"require", "require_unique", "require_materializable", "require_interpreted", "require_numeric"}:
        return "PURPOSE_REQUIREMENT_SCHEMA"
    if name == "unresolved":
        return "UNRESOLVED_OR_HOLE_EMISSION"
    if name in {"print", "dumps", "dump", "snapshot"}:
        return "REPORTING_DEBUGGING_OR_SERIALIZATION"
    return None


def classify_lines(code: str) -> dict[str, Any]:
    tree = ast.parse(code)
    n_lines = code.count("\n") + (0 if code.endswith("\n") or not code else 1)
    assigned = ["OTHER"] * (n_lines + 2)

    def paint(node: ast.AST, cat: str) -> None:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        if start is None:
            return
        for i in range(start, (end or start) + 1):
            if 0 <= i < len(assigned):
                assigned[i] = cat

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_") or node.name in {"looks_numeric"}:
                paint(node, "GENERAL_HELPER_OR_CONTROL_FLOW")
        if isinstance(node, ast.Call):
            cat = classify_call(_call_name(node))
            if cat:
                paint(node, cat)
        if isinstance(node, ast.For):
            # loops that contain unresolved/require over source rows are instantiation
            inner = {classify_call(_call_name(n)) for n in ast.walk(node) if isinstance(n, ast.Call)}
            if "UNRESOLVED_OR_HOLE_EMISSION" in inner and inner <= {
                "UNRESOLVED_OR_HOLE_EMISSION",
                "PHYSICAL_NORMALIZATION",
                "GENERAL_HELPER_OR_CONTROL_FLOW",
                None,
            }:
                paint(node, "PURPOSE_REQUIREMENT_INSTANTIATION")

    lines = code.splitlines()
    counts: Counter[str] = Counter()
    nonempty = 0
    for i, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        nonempty += 1
        if line.strip().startswith("#"):
            counts["OTHER"] += 1
            continue
        cat = assigned[i] if i < len(assigned) else "OTHER"
        counts[cat] += 1
    return {
        "physical_loc": len(lines),
        "nonblank_loc": nonempty,
        "by_category": {c: counts.get(c, 0) for c in CATS},
        "semantic_loc": sum(counts[c] for c in SEMANTIC_CATS),
        "mechanical_runtime_support_loc": sum(counts[c] for c in MECHANICAL_CATS),
        "requirement_loc": sum(counts[c] for c in REQ_CATS),
        "hole_instance_loc": sum(counts[c] for c in HOLE_CATS),
    }


def extract_calls(code: str) -> dict[str, Any]:
    tree = ast.parse(code)
    req_sites: list[dict[str, Any]] = []
    rels: list[str] = []
    refs: list[str] = []
    call_counts: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        call_counts[name] += 1
        arg0 = _call_str_arg(node)
        if name == "relation" and arg0:
            rels.append(arg0)
        if name == "referent" and arg0:
            refs.append(arg0)
        if name in {"require", "require_unique", "require_materializable", "require_interpreted", "require_numeric", "unresolved"} and arg0:
            field = None
            for kw in node.keywords:
                if kw.arg == "field":
                    field = _const_str(kw.value)
            req_sites.append({"kind": name, "name": arg0, "field": field, "lineno": node.lineno})
    return {
        "call_counts": dict(call_counts),
        "relation_names": rels,
        "referent_kinds": sorted(set(refs)),
        "requirement_sites": req_sites,
        "n_requirement_call_sites": len(req_sites),
        "n_unique_requirement_names": len({r["name"] for r in req_sites}),
    }


def grain_from_holes(holes: list[dict], req_sites: list[dict]) -> dict[str, Any]:
    schemas = sorted({s["name"] for s in req_sites})
    obligations: set[tuple] = set()
    for hole in holes:
        req = hole.get("requirement")
        kind = hole.get("failure_kind")
        observed = hole.get("observed")
        value = None
        if isinstance(observed, dict):
            value = observed.get("value") or observed.get("field")
        elif isinstance(observed, str):
            value = observed[:120]
        if kind == "UNINTERPRETED":
            obligations.add(("interpret", req, str(value)))
        elif kind in {"CARDINALITY_OVERSATISFIED", "MULTIPLE_CANDIDATES", "CARDINALITY_UNDERSATISFIED"}:
            obligations.add(("cardinality", req, kind))
        elif kind == "NO_MATERIALIZABLE_PATH":
            obligations.add(("materializable", req, kind))
        elif kind == "COMPARISON_OPERATOR_REQUIRED":
            obligations.add(("numeric", req, kind))
        elif kind == "EXPLICIT_UNRESOLVED":
            obligations.add(("unresolved", req, str(value)[:80] if value else req))
        else:
            obligations.add(("other", req, kind))
    return {
        "requirement_schemas": len(schemas),
        "schema_names": schemas,
        "candidate_semantic_obligations": len(obligations),
        "hole_occurrences": len(holes),
        "obligation_sample": sorted(list(obligations), key=lambda x: (str(x[0]), str(x[1])))[:40],
    }


def classify_duplication(spine_reqs: list[dict], sites: list[dict], holes: list[dict]) -> dict[str, Any]:
    name_counts = Counter(r.get("name") for r in spine_reqs)
    site_names = Counter(s["name"] for s in sites)
    categories = {"A_PURE_CODE_DUPLICATION": 0, "B_INSTANCE_EXPANSION": 0, "C_MISSING_PARAMETERIZATION": 0, "D_FALSE_DUPLICATION": 0, "E_UNCERTAIN": 0}
    details = []
    for name, n_emitted in name_counts.items():
        n_sites = site_names.get(name, 0)
        n_holes = sum(1 for h in holes if h.get("requirement") == name)
        if n_sites <= 1 and n_emitted <= 1:
            cat = "B_INSTANCE_EXPANSION" if n_holes > 1 else "E_UNCERTAIN"
            if n_holes <= 1:
                cat = "E_UNCERTAIN"
                # single schema, single emission — not duplication
                continue
        if n_sites > 1 and n_emitted == n_sites:
            cat = "A_PURE_CODE_DUPLICATION"
        elif n_sites == 1 and n_emitted > 1:
            # one authored call, many World requirement rows → loop instantiation of unresolved
            cat = "C_MISSING_PARAMETERIZATION" if name_counts[name] > 10 else "B_INSTANCE_EXPANSION"
        elif n_sites == 1 and n_holes > 1:
            cat = "B_INSTANCE_EXPANSION"
        else:
            cat = "E_UNCERTAIN"
        categories[cat] += n_emitted
        details.append({"name": name, "sites": n_sites, "emitted": n_emitted, "holes": n_holes, "category": cat})
    # holes from require_interpreted: one schema, many values → B
    return {"counts_by_category": categories, "per_name": details}


def inventory_trial(trial: str) -> dict[str, Any]:
    code = construction_path(trial).read_text(encoding="utf-8")
    spine = json.loads(spine_path(trial).read_text(encoding="utf-8"))
    holes = json.loads(holes_path(trial).read_text(encoding="utf-8"))
    loc = classify_lines(code)
    calls = extract_calls(code)
    refs = []
    for kind in calls["referent_kinds"]:
        refs.append({"original": kind, "normalized": REFERENT_NORM.get(kind, kind)})
    rels = []
    for name, spec in (spine.get("relations") or {}).items():
        rels.append(
            {
                "original": name,
                "normalized": _rel_norm(name),
                "derived": spec.get("derived"),
                "mode": spec.get("mode"),
                "n_rows": spec.get("n_rows"),
                "roles": [r.get("name") for r in (spec.get("roles") or [])],
            }
        )
    req_schema = []
    for site in calls["requirement_sites"]:
        req_schema.append(
            {
                "original": site["name"],
                "normalized": _req_norm(site["name"]),
                "kind": site["kind"],
                "field": site.get("field"),
            }
        )
    grain = grain_from_holes(holes, calls["requirement_sites"])
    dup = classify_duplication(spine.get("requirements") or [], calls["requirement_sites"], holes)
    factorized_req = sorted({r["normalized"] for r in req_schema})
    factorized_rel = sorted({r["normalized"] for r in rels})
    factorized_ref = sorted({r["normalized"] for r in refs})
    return {
        "trial": trial,
        "loc": loc,
        "calls": {k: calls[k] for k in ("call_counts", "n_requirement_call_sites", "n_unique_requirement_names")},
        "referents": refs,
        "relations": rels,
        "requirement_schemas": req_schema,
        "n_spine_requirement_rows": len(spine.get("requirements") or []),
        "n_relations": len(rels),
        "n_referent_kinds": len(refs),
        "n_requirement_schemas": calls["n_unique_requirement_names"],
        "grain": grain,
        "duplication": dup,
        "n_hole_groups": spine.get("n_hole_groups"),
        "n_hole_instances": spine.get("n_hole_instances"),
        "relation_row_counts": spine.get("relation_row_counts") or {},
        "referent_kinds_runtime": spine.get("referent_kinds") or {},
        "factorized": {
            "requirement_schemas": sorted({r["normalized"] for r in req_schema}),
            "relation_schemas": sorted({r["normalized"] for r in rels}),
            "referent_schemas": sorted({r["normalized"] for r in refs}),
            "n_requirement_schemas": len({r["normalized"] for r in req_schema}),
            "n_relation_schemas": len({r["normalized"] for r in rels}),
            "n_referent_schemas": len({r["normalized"] for r in refs}),
            "grounded_requirement_instances": len(spine.get("requirements") or []),
            "grounded_hole_occurrences": len(holes),
        },
    }


def cross_trial(inventories: list[dict]) -> dict[str, Any]:
    def freq(getter) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for inv in inventories:
            counts.update(set(getter(inv)))
        return dict(counts)

    ref_f = freq(lambda i: [r["normalized"] for r in i["referents"]])
    rel_f = freq(lambda i: [r["normalized"] for r in i["relations"]])
    req_f = freq(lambda i: [r["normalized"] for r in i["requirement_schemas"]])

    def buckets(freq_map: dict[str, int]) -> dict[str, list[str]]:
        out = {f"{n}/5": [] for n in range(1, 6)}
        for key, n in sorted(freq_map.items(), key=lambda kv: (-kv[1], kv[0])):
            out[f"{n}/5"].append(key)
        return out

    return {
        "referents": buckets(ref_f),
        "relations": buckets(rel_f),
        "requirements": buckets(req_f),
        "raw": {"referents": ref_f, "relations": rel_f, "requirements": req_f},
    }
