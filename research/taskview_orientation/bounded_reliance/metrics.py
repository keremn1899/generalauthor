"""Reconstruction-after-entitlement and mechanism outcomes. Frozen rules only."""

from __future__ import annotations

import re
from typing import Any

from research.taskview_orientation.bounded_reliance import (
    CHECKOUT_CONTRACT_PATH,
    CHECKOUT_VERIFIED_BY,
    TASKVIEW_CONDITIONS,
)
from research.taskview_orientation.bounded_reliance.entitlement import phase_spec
from research.taskview_orientation.telemetry import FrozenSpanClassifier, taskview_variant


_SQL_RELATION = re.compile(
    r"(?i)\b(?:FROM|JOIN)\s+[\"']?([A-Za-z_][A-Za-z0-9_]*)"
)


def sql_relations(sql: str | None) -> set[str]:
    if not sql:
        return set()
    return set(_SQL_RELATION.findall(str(sql)))


def _why_relation(arguments: dict[str, Any]) -> str | None:
    why = arguments.get("why")
    if isinstance(why, dict):
        relation = why.get("relation")
        return str(relation) if relation else None
    return None


def _is_checkout_verified_why(arguments: dict[str, Any]) -> bool:
    why = arguments.get("why")
    if not isinstance(why, dict):
        return False
    if why.get("relation") != CHECKOUT_VERIFIED_BY["relation"]:
        return False
    values = why.get("tuple") or {}
    expected = CHECKOUT_VERIFIED_BY["tuple"]
    return values.get("service") == expected["service"] and values.get("test") == expected["test"]


def _checkout_retract(event: dict[str, Any]) -> bool:
    if event.get("taskview_operation") != "assertion":
        return False
    arguments = event.get("tool_arguments") or {}
    if str(arguments.get("action") or "").upper() != "RETRACT":
        return False
    if arguments.get("relation") != "verified_by":
        return False
    values = arguments.get("values") or {}
    expected = CHECKOUT_VERIFIED_BY["tuple"]
    service = values.get("service") or values.get("service_id")
    test = values.get("test") or values.get("test_id")
    return service == expected["service"] and test == expected["test"]


def reconstruction_after_entitlement(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_phase: dict[str, dict[str, Any]] = {}
    for phase in range(1, 6):
        spec = phase_spec(phase)
        entitling = set(spec.get("entitling_relations") or [])
        ancestors = set(spec.get("ancestor_relations") or [])
        reassessment = set(spec.get("reassessment_relations") or [])
        required_local = set(spec.get("required_local_files") or [])
        repo_reproof = set(spec.get("repository_reproof_files") or [])
        reproof_relations = entitling | ancestors
        t_entitled: int | None = None
        reproof_calls = 0
        reproof_bytes = 0
        reproof_rel: set[str] = set()
        reproof_files: set[str] = set()
        catalog = 0
        targeted = 0
        sql_count = 0
        phase_events = [
            event for event in events if int(event.get("phase") or 0) == phase
        ]
        for event in phase_events:
            if event.get("event_type") != "TASKVIEW_TOOL":
                continue
            operation = event.get("taskview_operation")
            arguments = event.get("tool_arguments") or {}
            if operation == "query_sql":
                sql_count += 1
                relations = sql_relations(arguments.get("sql"))
                if (
                    t_entitled is None
                    and relations & entitling
                    and not event.get("error_type")
                ):
                    t_entitled = int(event["sequence"])
            variant = taskview_variant(event)
            if variant == "describe_catalog":
                catalog += 1
            elif variant in {"describe_relation", "describe_why"}:
                targeted += 1
        for event in phase_events:
            seq = int(event.get("sequence") or 0)
            if t_entitled is None or seq <= t_entitled:
                continue
            etype = event.get("event_type")
            arguments = event.get("tool_arguments") or {}
            nbytes = int(event.get("model_visible_output_bytes") or 0)
            if etype == "TASKVIEW_TOOL":
                operation = event.get("taskview_operation")
                variant = taskview_variant(event)
                addressed: set[str] = set()
                if operation == "query_sql":
                    addressed = sql_relations(arguments.get("sql"))
                elif variant == "describe_relation":
                    if arguments.get("relation"):
                        addressed = {str(arguments["relation"])}
                elif variant == "describe_why":
                    relation = _why_relation(arguments)
                    if relation:
                        addressed = {relation}
                counted = (addressed & reproof_relations) - reassessment
                if variant == "describe_catalog" or counted:
                    reproof_calls += 1
                    reproof_bytes += nbytes
                    reproof_rel.update(counted)
                    if variant == "describe_catalog":
                        reproof_rel.add("catalog")
            elif etype == "SOURCE_READ":
                path = event.get("source_path") or arguments.get("path")
                if path in required_local:
                    continue
                if path in repo_reproof:
                    reproof_calls += 1
                    reproof_bytes += nbytes
                    reproof_files.add(str(path))
            elif etype == "SOURCE_SEARCH":
                scope = str(event.get("search_scope") or arguments.get("scope") or ".")
                if scope in {".", ""}:
                    reproof_calls += 1
                    reproof_bytes += nbytes
                    reproof_files.add("<repository-root-search>")
        by_phase[str(phase)] = {
            "t_entitled_sequence": t_entitled,
            "reproof_calls": reproof_calls,
            "reproof_bytes": reproof_bytes,
            "reproof_distinct_relations": sorted(reproof_rel),
            "reproof_repository_files": sorted(reproof_files),
            "catalog_describe_count": catalog,
            "targeted_describe_count": targeted,
            "sql_query_count": sql_count,
        }
    return {
        "version": "bounded-reliance-entitlement-v1",
        "phases": by_phase,
        "episode_reproof_calls": sum(item["reproof_calls"] for item in by_phase.values()),
        "episode_reproof_bytes": sum(item["reproof_bytes"] for item in by_phase.values()),
    }


def _phase_reads(events: list[dict[str, Any]], phase: int) -> set[str]:
    return {
        str(event.get("source_path") or (event.get("tool_arguments") or {}).get("path"))
        for event in events
        if event.get("event_type") == "SOURCE_READ" and int(event.get("phase") or 0) == phase
    }


def _relation_breadth(events: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for event in events:
        if event.get("event_type") != "TASKVIEW_TOOL":
            continue
        arguments = event.get("tool_arguments") or {}
        variant = taskview_variant(event)
        if event.get("taskview_operation") == "query_sql":
            names.update(sql_relations(arguments.get("sql")))
        elif variant == "describe_relation" and arguments.get("relation"):
            names.add(str(arguments["relation"]))
        elif variant == "describe_why":
            relation = _why_relation(arguments)
            if relation:
                names.add(relation)
    return sorted(names)


def phase4_falsifiers(
    events: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    *,
    condition: str,
) -> dict[str, Any]:
    phase4 = [event for event in events if int(event.get("phase") or 0) == 4]
    answer = next(
        (item["answer"] for item in answers if int(item.get("phase") or 0) == 4),
        {},
    )
    inspected = CHECKOUT_CONTRACT_PATH in _phase_reads(events, 4)
    saw_why = any(
        event.get("event_type") == "TASKVIEW_TOOL"
        and taskview_variant(event) == "describe_why"
        and _is_checkout_verified_why(event.get("tool_arguments") or {})
        for event in phase4
    )
    received_changed = condition in {"T01", "T11"} and saw_why
    invalidated = answer.get("invalidated_verification") or []
    checkout_invalidated = (
        "service:checkout" in invalidated or "test:checkout-contract" in invalidated
        if isinstance(invalidated, list)
        else False
    )
    retracted = any(
        event.get("event_type") == "TASKVIEW_TOOL" and _checkout_retract(event)
        for event in phase4
    )
    first_changed_seq = next(
        (
            int(event["sequence"])
            for event in phase4
            if event.get("event_type") == "TASKVIEW_TOOL"
            and taskview_variant(event) == "describe_why"
            and _is_checkout_verified_why(event.get("tool_arguments") or {})
        ),
        None,
    )
    retract_seq = next(
        (
            int(event["sequence"])
            for event in phase4
            if event.get("event_type") == "TASKVIEW_TOOL" and _checkout_retract(event)
        ),
        None,
    )
    inspected_between = False
    if first_changed_seq is not None and retract_seq is not None:
        inspected_between = any(
            event.get("event_type") == "SOURCE_READ"
            and event.get("source_path") == CHECKOUT_CONTRACT_PATH
            and first_changed_seq < int(event["sequence"]) < retract_seq
            for event in phase4
        )
    unrelated_mutation = any(
        event.get("event_type") == "TASKVIEW_TOOL"
        and event.get("taskview_operation") == "assertion"
        and not _checkout_retract(event)
        and str((event.get("tool_arguments") or {}).get("action") or "").upper()
        in {"ASSERT", "RETRACT"}
        for event in phase4
    )
    treat_old_as_justified_after_changed = received_changed and not checkout_invalidated
    changed_as_automatic_false = (
        received_changed and retracted and not inspected_between
    )
    t10_overtrust = (
        condition == "T10"
        and not inspected
        and not retracted
        and not checkout_invalidated
    )
    return {
        "inspected_changed_checkout_source": inspected,
        "saw_checkout_grounding_why": saw_why,
        "received_changed_grounding": received_changed,
        "checkout_verification_invalidated_in_answer": checkout_invalidated,
        "retracted_checkout_verified_by": retracted,
        "treat_old_verification_as_justified_after_changed": (
            treat_old_as_justified_after_changed
        ),
        "failed_to_inspect_changed_source": not inspected,
        "treat_changed_as_automatic_falsehood": changed_as_automatic_false,
        "unrelated_semantic_mutation": unrelated_mutation,
        "t10_authority_without_freshness": t10_overtrust,
        "safety_mechanism_failed": any(
            [
                treat_old_as_justified_after_changed,
                not inspected,
                changed_as_automatic_false,
                unrelated_mutation,
            ]
        )
        if condition in TASKVIEW_CONDITIONS
        else (not inspected),
    }


def mechanism_outcomes(
    events: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    oracle_scores: list[dict[str, Any]],
    classifier_metrics: dict[str, Any],
    *,
    condition: str,
) -> dict[str, Any]:
    local_rates: dict[str, float | None] = {}
    for phase in range(1, 6):
        required = set(phase_spec(phase).get("required_local_files") or [])
        reads = _phase_reads(events, phase)
        local_rates[str(phase)] = (
            len(required & reads) / len(required) if required else None
        )
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
        "local_source_inspection_rate": local_rates,
        "semantically_adjudicated_local_correctness": [
            {
                "phase": score.get("phase", index + 1),
                "all_fields_correct": score.get("all_fields_correct"),
                "field_scores": score.get("field_scores"),
            }
            for index, score in enumerate(oracle_scores)
        ],
        "currentness_completeness_correctness": {
            "phase3_whole_world_complete": next(
                (
                    item["answer"].get("whole_world_complete")
                    for item in answers
                    if int(item.get("phase") or 0) == 3
                ),
                None,
            ),
            "phase5_completeness_universe": phase5.get("completeness_universe"),
            "phase5_whole_world_complete": phase5.get("whole_world_complete"),
        },
        "phase4_changed_source_inspection": CHECKOUT_CONTRACT_PATH in _phase_reads(events, 4),
        "phase4_falsifiers": phase4_falsifiers(events, answers, condition=condition),
        "assert_retract_behavior": [
            {
                "sequence": event["sequence"],
                "phase": event["phase"],
                "arguments": event.get("tool_arguments"),
            }
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
            and event.get("taskview_operation") == "assertion"
        ],
        "derived_state_rerun_behavior": [
            {
                "sequence": event["sequence"],
                "phase": event["phase"],
                "arguments": event.get("tool_arguments"),
            }
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
            and event.get("taskview_operation") == "rerun"
        ],
        "false_known_absence_claims": false_known_absence,
        "relation_breadth": _relation_breadth(events),
        "targeted_describe_count": sum(
            taskview_variant(event) in {"describe_relation", "describe_why"}
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "catalog_describe_count": sum(
            taskview_variant(event) == "describe_catalog"
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "sql_query_count": sum(
            event.get("taskview_operation") == "query_sql"
            for event in events
            if event.get("event_type") == "TASKVIEW_TOOL"
        ),
        "repository_orientation_bytes": (
            int((classifier_metrics.get("label_bytes") or {}).get("ORIENTATION_SUPPORT") or 0)
            + int((classifier_metrics.get("label_bytes") or {}).get("IRRELEVANT") or 0)
        ),
        "taskview_visible_bytes": classifier_metrics.get("taskview_visible_bytes"),
        "acquisition_inclusive_bytes": classifier_metrics.get("net_orientation_bytes"),
        "O_post": classifier_metrics.get("O_post"),
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
    condition: str,
) -> dict[str, Any]:
    classifier_metrics = classifier.aggregate(events)
    return {
        "reconstruction_after_entitlement": reconstruction_after_entitlement(events),
        "mechanism_outcomes": mechanism_outcomes(
            events,
            answers,
            oracle_scores,
            classifier_metrics,
            condition=condition,
        ),
        "economics_reported_not_primary": {
            "O_post": classifier_metrics.get("O_post"),
            "net_orientation_bytes": classifier_metrics.get("net_orientation_bytes"),
            "total_model_visible_bytes": classifier_metrics.get("total_model_visible_bytes"),
        },
    }
