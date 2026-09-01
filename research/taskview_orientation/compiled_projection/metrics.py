"""Frozen reassembly-after-delivery accounting. No model labels."""

from __future__ import annotations

from typing import Any

from research.taskview_orientation.bounded_reliance.metrics import (
    _checkout_retract,
    _phase_reads,
    _relation_breadth,
    sql_relations,
)
from research.taskview_orientation.compiled_projection import (
    CHECKOUT_CONTRACT_PATH,
    MIGRATION_SURFACE_RELATION,
    SUBSUMED_RELATIONS,
)
from research.taskview_orientation.compiled_projection.entitlement import reassembly
from research.taskview_orientation.telemetry import FrozenSpanClassifier, taskview_variant


def _why_relation(arguments: dict[str, Any]) -> str | None:
    why = arguments.get("why")
    if isinstance(why, dict) and why.get("relation"):
        return str(why["relation"])
    return None


def _addressed_relations(event: dict[str, Any]) -> set[str]:
    arguments = event.get("tool_arguments") or {}
    operation = event.get("taskview_operation")
    variant = taskview_variant(event)
    if operation == "query_sql":
        return sql_relations(arguments.get("sql"))
    if variant == "describe_relation" and arguments.get("relation"):
        return {str(arguments["relation"])}
    if variant == "describe_why":
        relation = _why_relation(arguments)
        return {relation} if relation else set()
    return set()


def reassembly_after_delivery(events: list[dict[str, Any]]) -> dict[str, Any]:
    spec = reassembly()
    subsumed = set(spec["subsumed_relations"])
    support = set(spec["repository_support_files"])
    reassessment_from = int(spec["reassessment_relations_from_phase"])
    by_phase: dict[str, dict[str, Any]] = {}
    for phase in range(1, 6):
        required_local = set(spec["required_local_files"][str(phase)])
        reassessment = (
            set(spec["reassessment_relations"]) if phase >= reassessment_from else set()
        )
        calls = 0
        nbytes = 0
        relations: set[str] = set()
        targeted = 0
        sql_count = 0
        files: set[str] = set()
        projection_reread = 0
        for event in events:
            if int(event.get("phase") or 0) != phase:
                continue
            etype = event.get("event_type")
            arguments = event.get("tool_arguments") or {}
            visible = int(event.get("model_visible_output_bytes") or 0)
            if etype == "TASKVIEW_TOOL":
                variant = taskview_variant(event)
                operation = event.get("taskview_operation")
                addressed = _addressed_relations(event)
                if variant == "describe_relation" and MIGRATION_SURFACE_RELATION in addressed:
                    projection_reread += 1
                    continue
                counted = (addressed & subsumed) - reassessment
                if variant == "describe_catalog" or counted:
                    calls += 1
                    nbytes += visible
                    relations.update(counted)
                    if variant == "describe_catalog":
                        relations.add("catalog")
                if variant in {"describe_relation", "describe_why"} and counted:
                    targeted += 1
                if operation == "query_sql" and counted:
                    sql_count += 1
            elif etype == "SOURCE_READ":
                path = str(event.get("source_path") or arguments.get("path") or "")
                if path in required_local:
                    continue
                if path in support:
                    calls += 1
                    nbytes += visible
                    files.add(path)
            elif etype == "SOURCE_SEARCH":
                scope = str(event.get("search_scope") or arguments.get("scope") or ".")
                if scope in {".", ""}:
                    calls += 1
                    nbytes += visible
                    files.add("<repository-root-search>")
        by_phase[str(phase)] = {
            "reassembly_calls": calls,
            "reassembly_bytes": nbytes,
            "distinct_subsumed_relations_reopened": sorted(relations - {"catalog"}),
            "targeted_describe_calls_on_subsumed_relations": targeted,
            "SQL_calls_on_subsumed_relations": sql_count,
            "repository_support_files_reopened_for_already_compiled_coarse_state": sorted(files),
            "projection_reread_calls": projection_reread,
        }
    return {
        "version": spec["version"],
        "t_delivered": 0,
        "subsumed_relations": list(SUBSUMED_RELATIONS),
        "phases": by_phase,
        "reassembly_calls": sum(item["reassembly_calls"] for item in by_phase.values()),
        "reassembly_bytes": sum(item["reassembly_bytes"] for item in by_phase.values()),
        "distinct_subsumed_relations_reopened": sorted(
            {
                name
                for item in by_phase.values()
                for name in item["distinct_subsumed_relations_reopened"]
            }
        ),
        "targeted_describe_calls_on_subsumed_relations": sum(
            item["targeted_describe_calls_on_subsumed_relations"] for item in by_phase.values()
        ),
        "SQL_calls_on_subsumed_relations": sum(
            item["SQL_calls_on_subsumed_relations"] for item in by_phase.values()
        ),
        "repository_support_files_reopened_for_already_compiled_coarse_state": sorted(
            {
                name
                for item in by_phase.values()
                for name in item["repository_support_files_reopened_for_already_compiled_coarse_state"]
            }
        ),
        "projection_reread_calls": sum(
            item["projection_reread_calls"] for item in by_phase.values()
        ),
    }


def mechanism_outcomes(
    events: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    oracle_scores: list[dict[str, Any]],
    classifier_metrics: dict[str, Any],
) -> dict[str, Any]:
    spec = reassembly()
    local_rates: dict[str, float | None] = {}
    for phase in range(1, 6):
        required = set(spec["required_local_files"][str(phase)])
        reads = _phase_reads(events, phase)
        local_rates[str(phase)] = len(required & reads) / len(required) if required else None
    phase5 = next(
        (item["answer"] for item in answers if int(item.get("phase") or 0) == 5),
        {},
    )
    gap_stale_unrestored = any(
        event.get("event_type") == "TASKVIEW_TOOL"
        and event.get("taskview_operation") == "query_sql"
        and "verification_gap" in sql_relations((event.get("tool_arguments") or {}).get("sql"))
        and int(event.get("phase") or 0) == 5
        for event in events
    ) and not any(
        event.get("event_type") == "TASKVIEW_TOOL"
        and event.get("taskview_operation") == "rerun"
        and (event.get("tool_arguments") or {}).get("relation") == "verification_gap"
        for event in events
    )
    false_known_absence = bool(phase5.get("whole_world_complete") is True) or (
        gap_stale_unrestored and phase5.get("current_verification_gap") == []
    )
    return {
        "required_local_source_inspection_rate": local_rates,
        "semantically_adjudicated_local_correctness": [
            {
                "phase": score.get("phase", index + 1),
                "all_fields_correct": score.get("all_fields_correct"),
            }
            for index, score in enumerate(oracle_scores)
        ],
        "phase4_changed_checkout_source_inspected": CHECKOUT_CONTRACT_PATH
        in _phase_reads(events, 4),
        "false_known_absence_claims": false_known_absence,
        "phase5_completeness_universe": phase5.get("completeness_universe"),
        "phase5_whole_world_complete": phase5.get("whole_world_complete"),
        "semantic_assertion_update": [
            {
                "sequence": event["sequence"],
                "phase": event["phase"],
                "arguments": event.get("tool_arguments"),
            }
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
            and event.get("taskview_operation") == "assertion"
        ],
        "verification_gap_rerun_behavior": [
            {
                "sequence": event["sequence"],
                "phase": event["phase"],
                "arguments": event.get("tool_arguments"),
            }
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
            and event.get("taskview_operation") == "rerun"
        ],
        "checkout_verified_by_retracted": any(
            event.get("event_type") == "TASKVIEW_TOOL" and _checkout_retract(event)
            for event in events
            if int(event.get("phase") or 0) == 4
        ),
        "catalog_describe_count": sum(
            taskview_variant(event) == "describe_catalog"
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "targeted_describe_count": sum(
            taskview_variant(event) in {"describe_relation", "describe_why"}
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "sql_query_count": sum(
            event.get("taskview_operation") == "query_sql"
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "unique_taskview_relations_accessed": _relation_breadth(events),
        "unique_repository_files_read": classifier_metrics.get("unique_files_read") or [],
        "broad_repository_searches": classifier_metrics.get("repository_search_calls") or 0,
        "repository_orientation_bytes": (
            int((classifier_metrics.get("label_bytes") or {}).get("ORIENTATION_SUPPORT") or 0)
            + int((classifier_metrics.get("label_bytes") or {}).get("IRRELEVANT") or 0)
        ),
        "taskview_visible_bytes": classifier_metrics.get("taskview_visible_bytes"),
        "acquisition_inclusive_bytes": classifier_metrics.get("net_orientation_bytes"),
        "participant_tool_errors": sum(
            event.get("event_type") == "TOOL_ERROR" for event in events
        ),
    }


def score_episode(
    events: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    oracle_scores: list[dict[str, Any]],
    classifier: FrozenSpanClassifier,
    *,
    initial_delivery_bytes: int,
) -> dict[str, Any]:
    classifier_metrics = classifier.aggregate(events)
    return {
        "reassembly_after_delivery": reassembly_after_delivery(events),
        "mechanism_outcomes": mechanism_outcomes(
            events, answers, oracle_scores, classifier_metrics
        ),
        "initial_delivery_bytes": initial_delivery_bytes,
        "model_visible_input_bytes": classifier_metrics.get("model_visible_input_bytes"),
        "economics_reported_not_primary": {
            "O_post": classifier_metrics.get("O_post"),
            "net_orientation_bytes": classifier_metrics.get("net_orientation_bytes"),
            "total_model_visible_bytes": classifier_metrics.get("total_model_visible_bytes"),
        },
    }
