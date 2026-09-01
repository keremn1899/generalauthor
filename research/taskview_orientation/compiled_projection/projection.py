"""Deterministic migration-surface compiler. No new semantic judgments."""

from __future__ import annotations

from typing import Any

from research.taskview_orientation.compiled_projection import (
    MIGRATION_SURFACE_RELATION,
    SUBSUMED_RELATIONS,
)
from research.taskview_orientation.fixture import semantic_rows
from research.taskview_orientation.surface import ExperimentTaskViewSurface


PREFIXES = ("service:", "adapter:", "test:", "library:", "component:")

# Exclusive disposition order. First matching rule wins.
DISPOSITION_RULES = (
    "DIRECT_CHANGE",
    "PROTECTED",
    "EXCLUDED_BOUNDARY",
    "UNRESOLVED_SCOPE",
)

PARITY_RULES = (
    {
        "compiled_field": "subjects.*.disposition=DIRECT_CHANGE",
        "source_relation_tuple(s)": "requires_change(x)",
        "derivation_rule": "DIRECT_CHANGE(x) <- requires_change(x)",
    },
    {
        "compiled_field": "subjects.*.disposition=PROTECTED",
        "source_relation_tuple(s)": "protected_by(x, a) and not requires_change(x)",
        "derivation_rule": "PROTECTED(x, a) <- protected_by(x, a) AND NOT requires_change(x)",
    },
    {
        "compiled_field": "subjects.*.protected_by",
        "source_relation_tuple(s)": "protected_by(x, a)",
        "derivation_rule": "protected_by field copies protected_by.adapter",
    },
    {
        "compiled_field": "subjects.*.compatible_via",
        "source_relation_tuple(s)": "compatible_via(x, old, new, a)",
        "derivation_rule": "compatible_via field copies the compatible_via tuple for x",
    },
    {
        "compiled_field": "subjects.*.disposition=EXCLUDED_BOUNDARY",
        "source_relation_tuple(s)": "boundary(x) AND excluded(x, basis)",
        "derivation_rule": "EXCLUDED_BOUNDARY(x, basis) <- boundary(x) AND excluded(x, basis) AND NOT requires_change(x) AND NOT protected_by(x, _)",
    },
    {
        "compiled_field": "subjects.*.exclusion_basis",
        "source_relation_tuple(s)": "excluded(x, basis)",
        "derivation_rule": "exclusion_basis copies excluded.basis",
    },
    {
        "compiled_field": "subjects.*.disposition=UNRESOLVED_SCOPE",
        "source_relation_tuple(s)": "unresolved_scope(x)",
        "derivation_rule": "UNRESOLVED_SCOPE(x) <- unresolved_scope(x) AND no higher-priority disposition",
    },
    {
        "compiled_field": "subjects.*.scope=IN_SCOPE",
        "source_relation_tuple(s)": "in_scope(x)",
        "derivation_rule": "scope IN_SCOPE iff in_scope(x); omitted otherwise",
    },
    {
        "compiled_field": "subjects.*.verification=VERIFIED",
        "source_relation_tuple(s)": "verified_by(x, t) AND x not in verification_gap",
        "derivation_rule": "VERIFIED <- current verified_by tuple for x",
    },
    {
        "compiled_field": "subjects.*.verification=GAP",
        "source_relation_tuple(s)": "verification_gap(x)",
        "derivation_rule": "GAP <- x in current verification_gap",
    },
    {
        "compiled_field": "subjects.*.verified_by",
        "source_relation_tuple(s)": "verified_by(x, t)",
        "derivation_rule": "verified_by field copies verified_by.test",
    },
    {
        "compiled_field": "scope_receipt.affected_service",
        "source_relation_tuple(s)": "describe(affected_service).completeness.{status,stale,current,universe}",
        "derivation_rule": "COMPLETE iff receipt status is COMPLETE and not stale; otherwise NOT_COMPLETE",
    },
    {
        "compiled_field": "scope_receipt.whole_world",
        "source_relation_tuple(s)": "absence of any COMPLETE completeness receipt whose universe is whole-world",
        "derivation_rule": "Always NOT_COMPLETE: fixture has no whole-world completeness contract",
    },
)


IMPLEMENTATION_LEAK_NEEDLES = (
    "Decoder(",
    "allow_comments",
    "number_mode",
    "canonical_keys",
    "sort_keys",
    "decimal_mode",
    "decimal-string",
    "build_report",
    "signed_body",
    "resolve_consumer",
    "REGISTRY",
    "plugins.",
    "json_codec.py",
    "comments accepted",
    "Decimal",
    "10.50",
    "wildcard",
)


def short_id(value: str) -> str:
    for prefix in PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def _ids(rows: list[dict[str, Any]], *keys: str) -> set[str]:
    out: set[str] = set()
    for row in rows:
        for key in keys:
            if key in row and row[key]:
                out.add(str(row[key]))
    return out


def _index(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row}


def completeness_receipts(surface: ExperimentTaskViewSurface) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    catalog = surface.describe().get("completeness") or []
    if isinstance(catalog, list):
        for receipt in catalog:
            if not isinstance(receipt, dict) or not receipt.get("target"):
                continue
            receipts[str(receipt["target"])] = {
                "status": receipt.get("status"),
                "universe": receipt.get("universe"),
                "state": receipt.get("state"),
                "stale": receipt.get("state") == "STALE",
                "current": receipt.get("state") in {None, "CURRENT"},
            }
    for name in ("affected_service", "verification_gap", "requires_change"):
        payload = surface.describe(relation=name)
        relation = payload.get("relation") or {}
        receipt = relation.get("completeness") or {}
        if not isinstance(receipt, dict) or not receipt:
            continue
        receipts[name] = {
            "status": receipt.get("status"),
            "universe": receipt.get("universe"),
            "state": receipt.get("state"),
            "stale": receipt.get("state") == "STALE",
            "current": receipt.get("state") == "CURRENT",
            "basis": receipt.get("basis"),
        }
    return receipts


def compile_state(surface: ExperimentTaskViewSurface) -> dict[str, Any]:
    """Canonical structured state used by both presentations."""

    rows = semantic_rows(surface.view)
    receipts = completeness_receipts(surface)
    requires = _ids(rows.get("requires_change") or [], "service_id")
    protected = _index(rows.get("protected_by") or [], "service_id")
    compatible = _index(rows.get("compatible_via") or [], "service_id")
    boundary = _ids(rows.get("boundary") or [], "subject_id")
    excluded = _index(rows.get("excluded") or [], "subject_id")
    unresolved = _ids(rows.get("unresolved_scope") or [], "subject_id")
    in_scope = _ids(rows.get("in_scope") or [], "subject_id")
    verified = _index(rows.get("verified_by") or [], "service_id")
    gap = _ids(rows.get("verification_gap") or [], "service_id")
    affected = _ids(rows.get("affected_service") or [], "service_id")

    subjects: dict[str, dict[str, Any]] = {}

    def _subject(identity: str) -> dict[str, Any]:
        item = subjects.setdefault(identity, {"id": identity, "short_id": short_id(identity)})
        return item

    for identity in sorted(requires):
        item = _subject(identity)
        item["disposition"] = "DIRECT_CHANGE"
    for identity, row in sorted(protected.items()):
        item = _subject(identity)
        if "disposition" not in item:
            item["disposition"] = "PROTECTED"
        item["protected_by"] = row["adapter_id"]
    for identity, row in sorted(compatible.items()):
        item = _subject(identity)
        item["compatible_via"] = {
            "old_library": row["old_library_id"],
            "new_library": row["new_library_id"],
            "adapter": row["adapter_id"],
        }
    for identity in sorted(boundary & set(excluded)):
        item = _subject(identity)
        if "disposition" not in item:
            item["disposition"] = "EXCLUDED_BOUNDARY"
        item["exclusion_basis"] = excluded[identity]["basis"]
    for identity in sorted(unresolved):
        item = _subject(identity)
        if "disposition" not in item:
            item["disposition"] = "UNRESOLVED_SCOPE"

    for identity, item in subjects.items():
        if identity in in_scope:
            item["scope"] = "IN_SCOPE"
        if identity in gap:
            item["verification"] = "GAP"
        elif identity in verified:
            item["verification"] = "VERIFIED"
            item["verified_by"] = verified[identity]["test_id"]

    affected_receipt = receipts.get("affected_service") or {}
    affected_complete = (
        affected_receipt.get("status") == "COMPLETE" and not affected_receipt.get("stale")
    )
    return {
        "relation": MIGRATION_SURFACE_RELATION,
        "subjects": [subjects[key] for key in sorted(subjects, key=_subject_sort)],
        "scope_receipt": {
            "affected_service": "COMPLETE" if affected_complete else "NOT_COMPLETE",
            "affected_service_universe": affected_receipt.get("universe"),
            "whole_world": "NOT_COMPLETE",
        },
        "atomic_rows": {name: list(rows.get(name) or []) for name in SUBSUMED_RELATIONS},
        "completeness_receipts": receipts,
        "affected_service_ids": sorted(affected),
    }


def _subject_sort(identity: str) -> tuple[int, str]:
    rank = {
        "service:checkout": 0,
        "service:reporting": 1,
        "service:partner-gateway": 2,
        "service:external-worker": 3,
    }
    return (rank.get(identity, 50), identity)


def render_compiled(state: dict[str, Any]) -> str:
    lines = [MIGRATION_SURFACE_RELATION, ""]
    for subject in state["subjects"]:
        lines.append(subject["short_id"])
        lines.append(f"  disposition: {subject['disposition']}")
        if subject.get("scope"):
            lines.append(f"  scope: {subject['scope']}")
        if subject.get("protected_by"):
            lines.append(f"  protected_by: {short_id(subject['protected_by'])}")
        if subject.get("compatible_via"):
            via = subject["compatible_via"]
            lines.append(
                "  compatible_via: "
                f"{short_id(via['old_library'])} -> {short_id(via['new_library'])} "
                f"via {short_id(via['adapter'])}"
            )
        if subject.get("exclusion_basis"):
            lines.append(f"  exclusion_basis: {subject['exclusion_basis']}")
        if subject.get("verification"):
            lines.append(f"  verification: {subject['verification']}")
        if subject.get("verified_by"):
            lines.append(f"  verified_by: {short_id(subject['verified_by'])}")
        lines.append("")
    receipt = state["scope_receipt"]
    lines.append("scope_receipt")
    lines.append(f"  affected_service: {receipt['affected_service']}")
    lines.append(f"  whole_world: {receipt['whole_world']}")
    return "\n".join(lines).rstrip() + "\n"


def render_atomic(state: dict[str, Any]) -> str:
    lines = ["atomic_task_state", ""]
    for name in SUBSUMED_RELATIONS:
        lines.append(f"{name}:")
        rows = state["atomic_rows"][name]
        if not rows:
            lines.append("  (none)")
            continue
        for row in rows:
            rendered = " ".join(f"{key}={row[key]}" for key in row)
            lines.append(f"  {rendered}")
        lines.append("")
    lines.append("completeness:")
    receipts = state["completeness_receipts"]
    affected = receipts.get("affected_service") or {}
    lines.append(
        "  affected_service: "
        f"status={affected.get('status')} universe={affected.get('universe')} "
        f"stale={affected.get('stale')} current={affected.get('current')}"
    )
    lines.append("  whole_world: NOT_COMPLETE")
    return "\n".join(lines).rstrip() + "\n"


def presentation_for(condition: str, surface: ExperimentTaskViewSurface) -> str:
    state = compile_state(surface)
    if condition == "COMPILED":
        return render_compiled(state)
    if condition == "ATOMIC":
        return render_atomic(state)
    raise ValueError(f"unknown condition {condition}")


def compiled_payload(surface: ExperimentTaskViewSurface) -> dict[str, Any]:
    state = compile_state(surface)
    return {
        "relation": MIGRATION_SURFACE_RELATION,
        "presentation": "compiled_decision_projection",
        "text": render_compiled(state),
        "state": {
            "subjects": state["subjects"],
            "scope_receipt": state["scope_receipt"],
        },
    }


def atomic_payload(surface: ExperimentTaskViewSurface) -> dict[str, Any]:
    state = compile_state(surface)
    return {
        "relation": MIGRATION_SURFACE_RELATION,
        "presentation": "atomic_relations",
        "text": render_atomic(state),
        "state": {
            "atomic_rows": state["atomic_rows"],
            "completeness_receipts": {
                name: receipt
                for name, receipt in state["completeness_receipts"].items()
                if name in {"affected_service", "verification_gap", "requires_change"}
            },
            "scope_receipt": state["scope_receipt"],
        },
    }


def parity_artifact(surface: ExperimentTaskViewSurface) -> dict[str, Any]:
    state = compile_state(surface)
    rows = state["atomic_rows"]
    subjects = {item["id"]: item for item in state["subjects"]}
    return {
        "version": "compiled-projection-parity-v1",
        "subsumed_relations": list(SUBSUMED_RELATIONS),
        "rules": list(PARITY_RULES),
        "compiled_fields": [
            {
                "subject": item["id"],
                "compiled_field": field,
                "value": item.get(field),
                "source_relation_tuple(s)": _sources_for(item, field, rows),
            }
            for item in state["subjects"]
            for field in (
                "disposition",
                "scope",
                "protected_by",
                "compatible_via",
                "exclusion_basis",
                "verification",
                "verified_by",
            )
            if field in item
        ]
        + [
            {
                "compiled_field": "scope_receipt.affected_service",
                "value": state["scope_receipt"]["affected_service"],
                "source_relation_tuple(s)": [
                    "affected_service completeness receipt",
                    *[f"affected_service(service_id={sid})" for sid in state["affected_service_ids"]],
                ],
                "derivation_rule": "COMPLETE iff current COMPLETE receipt over production_service",
            },
            {
                "compiled_field": "scope_receipt.whole_world",
                "value": "NOT_COMPLETE",
                "source_relation_tuple(s)": ["no whole-world completeness receipt exists"],
                "derivation_rule": "NOT_COMPLETE from absence of a whole-world COMPLETE contract",
            },
        ],
        "subjects_present": sorted(subjects),
        "compiled_text": render_compiled(state),
        "atomic_text": render_atomic(state),
    }


def _sources_for(item: dict[str, Any], field: str, rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    identity = item["id"]
    if field == "disposition":
        disp = item["disposition"]
        if disp == "DIRECT_CHANGE":
            return [f"requires_change(service_id={identity})"]
        if disp == "PROTECTED":
            return [f"protected_by(service_id={identity})"]
        if disp == "EXCLUDED_BOUNDARY":
            return [
                f"boundary(subject_id={identity})",
                f"excluded(subject_id={identity})",
            ]
        if disp == "UNRESOLVED_SCOPE":
            return [f"unresolved_scope(subject_id={identity})"]
    if field == "scope":
        return [f"in_scope(subject_id={identity})"]
    if field == "protected_by":
        return [f"protected_by(service_id={identity}, adapter_id={item['protected_by']})"]
    if field == "compatible_via":
        via = item["compatible_via"]
        return [
            "compatible_via("
            f"service_id={identity}, old_library_id={via['old_library']}, "
            f"new_library_id={via['new_library']}, adapter_id={via['adapter']})"
        ]
    if field == "exclusion_basis":
        return [f"excluded(subject_id={identity}, basis={item['exclusion_basis']})"]
    if field == "verification":
        if item["verification"] == "GAP":
            return [f"verification_gap(service_id={identity})"]
        return [f"verified_by(service_id={identity})"]
    if field == "verified_by":
        return [f"verified_by(service_id={identity}, test_id={item['verified_by']})"]
    return []


def leaks_implementation_answers(text: str) -> list[str]:
    return [needle for needle in IMPLEMENTATION_LEAK_NEEDLES if needle in text]
