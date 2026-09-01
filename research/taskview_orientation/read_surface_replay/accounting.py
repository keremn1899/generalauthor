"""Replay-level accounting, admission gates, and mechanical greed diagnostics."""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from research.taskview_orientation.read_surface_replay.candidates import (
    CATEGORIES,
    ChargedItem,
    replay_episode,
)
from research.taskview_orientation.read_surface_replay.epistemic import evaluate_safety
from research.taskview_orientation.read_surface_replay.ledger import CampaignLedger, EpisodeLedger
from research.taskview_orientation.read_surface_replay.serialize import serializer_hash


PRIMARY_CANDIDATES = ("A", "B", "C", "D", "E", "F")
SENSITIVITY_CANDIDATES = ("E1", "Eall")
LEVELS = (
    "trajectory_preserving",
    "mechanical_dedup_floor",
    "row_floor",
)


def _sum_categories(items: list[ChargedItem], *, phase_min: int | None = None) -> dict[str, int]:
    out = {name: 0 for name in CATEGORIES}
    for item in items:
        if phase_min is not None and item.phase < phase_min and item.kind not in {
            "stable_contract",
            "tool_schema",
        }:
            continue
        if phase_min is not None and item.kind in {"stable_contract", "tool_schema"}:
            continue
        for name, value in item.categories.items():
            out[name] = out.get(name, 0) + int(value)
    return out


def _result_bytes(items: list[ChargedItem], *, include_init: bool) -> int:
    total = 0
    for item in items:
        if item.kind == "tool_schema":
            if include_init:
                total += item.total
            continue
        if item.kind == "stable_contract":
            if include_init:
                total += item.total
            continue
        total += item.total
    return total


def _post_phase1_bytes(items: list[ChargedItem]) -> int:
    return sum(item.total for item in items if item.phase >= 2)


def summarize_episode(
    episode: EpisodeLedger,
    candidate: str,
    level: str,
    items: list[ChargedItem],
) -> dict[str, Any]:
    budget = episode.raw_o_post - episode.repository_o_post
    cats = _sum_categories(items)
    post = _post_phase1_bytes(items)
    acq = _result_bytes(items, include_init=True)
    all_phase_results = _result_bytes(items, include_init=False)
    return {
        "candidate": candidate,
        "level": level,
        "replicate": episode.replicate,
        "episode_id": episode.episode_id,
        "stable_contract_bytes": cats["stable_contract"],
        "tool_schema_bytes": cats["tool_schema"],
        "semantic_context_bytes": cats["semantic_context"],
        "dynamic_row_bytes": cats["dynamic_row"],
        "epistemic_bytes": cats["epistemic"],
        "grounding_bytes": cats["grounding"],
        "maintenance_bytes": cats["maintenance"],
        "error_bytes": cats["error"],
        "envelope_bytes": cats.get("envelope", 0),
        "total_taskview_read_bytes": all_phase_results,
        "post_phase_1_taskview_bytes": post,
        "acquisition_inclusive_taskview_bytes": acq,
        "TASKVIEW_repository_O_post": episode.repository_o_post,
        "RAW_matched_O_post": episode.raw_o_post,
        "repository_orientation_savings": budget,
        "net_orientation_delta_post": post - budget,
        "net_orientation_delta_acq": acq - budget,
        "historical_taskview_visible_bytes": episode.historical_taskview_visible_bytes,
        "historical_taskview_post_bytes": episode.historical_taskview_post_bytes,
        "sql_escape_count": sum(item.sql_escape for item in items),
        "not_modified_count": sum(item.not_modified for item in items),
        "omitted_count": sum(item.omitted for item in items),
    }


def admit(summaries: list[dict[str, Any]], safety: bool, *, floor: bool) -> str:
    preserving = [item for item in summaries if item["level"] == "trajectory_preserving"]
    floors = [item for item in summaries if item["level"] == "mechanical_dedup_floor"]
    if not safety:
        return "REJECT"
    preserving.sort(key=lambda item: item["replicate"])
    floors.sort(key=lambda item: item["replicate"])
    acq = [item["net_orientation_delta_acq"] for item in preserving]
    floor_acq = [item["net_orientation_delta_acq"] for item in floors]
    vs_a = None
    if not safety:
        return "REJECT"
    median_acq = statistics.median(acq)
    wins = sum(delta < 0 for delta in acq)
    floor_median = statistics.median(floor_acq)
    floor_wins = sum(delta < 0 for delta in floor_acq)
    worse_than_a = 0
    if vs_a is not None:
        worse_than_a = vs_a
    if median_acq < 0 and wins >= 3:
        return "ADMIT"
    if floor_median < 0 and floor_wins >= 3:
        return "CONDITIONAL"
    if floor_median >= 0:
        return "DEPRIORITIZE"
    return "DEPRIORITIZE"


def greed_metrics(episode: EpisodeLedger) -> dict[str, Any]:
    by_phase: dict[int, list] = defaultdict(list)
    for access in episode.accesses:
        if access.operation == "query_sql" and not access.is_error:
            by_phase[access.phase].append(access)
    relation_breadth = {}
    reread_rates = {}
    accesses_total = 0
    first_keys: dict[int, set[str]] = {}
    rows_retrieved = 0
    unique_rows: set[tuple] = set()
    full_scan = 0
    filtered = 0
    order_limit = 0
    sql_count = 0
    for phase, accesses in by_phase.items():
        rels = [access.sql.relation for access in accesses if access.sql]
        relation_breadth[str(phase)] = len(set(rels))
        accesses_total += len(accesses)
        keys = []
        for access in accesses:
            sql_count += 1
            key = f"{access.sql.relation}|{access.relevant_revision_token}" if access.sql else ""
            keys.append(key)
            rows_retrieved += len(access.returned_rows)
            for tup in access.canonical_tuples:
                unique_rows.add((access.sql.relation, access.relation_revisions.get(access.sql.relation), tup))
            if access.sql and access.sql.shape == "PLAIN":
                full_scan += 1
            if access.sql and access.sql.shape == "FILTER":
                filtered += 1
            if access.sql and access.sql.shape == "ORDER/LIMIT":
                order_limit += 1
        repeats = 0
        seen: set[str] = set()
        for key in keys:
            if key in seen:
                repeats += 1
            seen.add(key)
        reread_rates[str(phase)] = (repeats / len(keys)) if keys else 0.0
        first_keys[phase] = set(keys)
    later = 0
    later_eligible = 0
    seen_episode: set[str] = set()
    for phase in sorted(by_phase):
        for access in by_phase[phase]:
            key = f"{access.sql.relation}|{access.relevant_revision_token}"
            if phase > 1:
                later_eligible += 1
                if key in seen_episode:
                    later += 1
            seen_episode.add(key)
    exact_repeats = 0
    exact_queries = 0
    seen_exact: set[str] = set()
    for access in episode.accesses:
        if access.operation != "query_sql" or access.is_error or access.sql is None:
            continue
        exact_queries += 1
        key = access.sql.query_key() + "|" + access.relevant_revision_token
        if key in seen_exact:
            exact_repeats += 1
        seen_exact.add(key)
    describes = [access for access in episode.accesses if access.operation == "describe"]
    catalog = sum(access.describe_kind == "catalog" for access in describes)
    catalogs_after_first = max(0, catalog - 1)
    unique_n = len(unique_rows) or 1
    return {
        "relation_breadth_per_phase": relation_breadth,
        "state_query_count": sql_count,
        "relation_access_count": accesses_total,
        "phase_reread_rate": reread_rates,
        "episode_refresh_rate": (later / later_eligible) if later_eligible else 0.0,
        "exact_query_reread_rate": (exact_repeats / exact_queries) if exact_queries else 0.0,
        "rows_retrieved": rows_retrieved,
        "unique_delivered_rows": len(unique_rows),
        "row_reread_amplification": rows_retrieved / unique_n,
        "full_scan_rate": (full_scan / sql_count) if sql_count else 0.0,
        "filter_rate": (filtered / sql_count) if sql_count else 0.0,
        "limit_order_rate": (order_limit / sql_count) if sql_count else 0.0,
        "catalog_describe_count": catalog,
        "epistemic_refresh_count": catalogs_after_first
        + sum(access.describe_kind == "relation" for access in describes),
        "contract_amplification_numerator_catalogs": catalog,
    }


def savings_sources(
    by_candidate: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, dict[str, float]]:
    """Disjoint-ish attribution versus A trajectory-preserving acquisition totals.

    Overlapping mechanisms are not summed.  Each row is a pairwise contrast.
    """

    def median_acq(candidate: str, level: str = "trajectory_preserving") -> float:
        return statistics.median(
            item["acquisition_inclusive_taskview_bytes"]
            for item in by_candidate[candidate][level]
        )

    a = median_acq("A")
    return {
        "contract_lifetime_B_minus_A": {
            "kind": "pairwise",
            "bytes": median_acq("B") - a,
            "note": "stable contract once vs repeated catalog describe; SQL held fixed",
        },
        "request_language_C_minus_B": {
            "kind": "pairwise",
            "bytes": median_acq("C") - median_acq("B"),
            "note": "simple access vs SQL with identical row serializer",
        },
        "auto_context_D_minus_A": {
            "kind": "pairwise",
            "bytes": median_acq("D") - a,
            "note": "first-use cards replace catalog; SQL retained",
        },
        "bundling_E_minus_B": {
            "kind": "pairwise",
            "bytes": median_acq("E") - median_acq("B"),
            "note": "oracle phase-union bundle vs per-call SQL under the same contract",
        },
        "selector_E1_minus_E": {
            "kind": "pairwise",
            "bytes": median_acq("E1") - median_acq("E"),
            "note": "one extra relation in the oracle bundle",
        },
        "selector_Eall_minus_E": {
            "kind": "pairwise",
            "bytes": median_acq("Eall") - median_acq("E"),
            "note": "all-relations bundle vs observed-union oracle bundle",
        },
        "conditional_F_minus_A": {
            "kind": "pairwise",
            "bytes": median_acq("F") - a,
            "note": "not_modified on unchanged query+revision; describes retained",
        },
        "state_dedup_A_floor_minus_A": {
            "kind": "pairwise",
            "bytes": median_acq("A", "mechanical_dedup_floor") - a,
            "note": "mechanical unique (query, revision) floor on pull+SQL",
        },
        "state_dedup_B_floor_minus_B": {
            "kind": "pairwise",
            "bytes": median_acq("B", "mechanical_dedup_floor") - median_acq("B"),
            "note": "mechanical unique delivery under stable contract",
        },
        "state_dedup_F_floor_minus_F": {
            "kind": "pairwise",
            "bytes": median_acq("F", "mechanical_dedup_floor") - median_acq("F"),
            "note": "mechanical floor beyond trajectory-preserving not_modified",
        },
    }


def classify_admissions(
    summaries: dict[str, dict[str, list[dict[str, Any]]]],
    safety: dict[str, Any],
) -> dict[str, str]:
    out = {}
    a_preserving = {
        item["replicate"]: item["acquisition_inclusive_taskview_bytes"]
        for item in summaries["A"]["trajectory_preserving"]
    }
    for candidate in PRIMARY_CANDIDATES:
        safe = safety["candidates"].get(candidate, {}).get("safe", False)
        preserving = summaries[candidate]["trajectory_preserving"]
        worse = sum(
            item["acquisition_inclusive_taskview_bytes"] > a_preserving[item["replicate"]]
            for item in preserving
        )
        gate = admit(preserving + summaries[candidate]["mechanical_dedup_floor"], safe, floor=True)
        if (not safe) or worse >= 3:
            if not safe:
                gate = "REJECT"
            elif worse >= 3 and gate == "ADMIT":
                # more expensive than v0.1 in >=3/4 without independent benefit
                if candidate == "A":
                    pass
                else:
                    gate = "REJECT"
        out[candidate] = gate
    return out


def run_accounting(ledger: CampaignLedger) -> dict[str, Any]:
    safety = evaluate_safety()
    summaries: dict[str, dict[str, list[dict[str, Any]]]] = {}
    greed = {
        episode.replicate: greed_metrics(episode) for episode in ledger.episodes
    }
    for candidate in PRIMARY_CANDIDATES + SENSITIVITY_CANDIDATES:
        summaries[candidate] = {}
        for level in LEVELS:
            rows = []
            for episode in ledger.episodes:
                items = replay_episode(episode, candidate, level)
                rows.append(summarize_episode(episode, candidate, level, items))
            summaries[candidate][level] = rows
    admissions = classify_admissions(summaries, safety)
    table = {}
    for level in ("trajectory_preserving", "mechanical_dedup_floor"):
        table[level] = []
        for candidate in PRIMARY_CANDIDATES:
            rows = summaries[candidate][level]
            deltas = [item["net_orientation_delta_acq"] for item in rows]
            table[level].append(
                {
                    "candidate": candidate,
                    "R1": deltas[0],
                    "R2": deltas[1],
                    "R3": deltas[2],
                    "R4": deltas[3],
                    "median": statistics.median(deltas),
                    "directional_wins": sum(delta < 0 for delta in deltas),
                    "safety": "PASS" if safety["candidates"][candidate]["safe"] else "FAIL",
                    "admission": admissions[candidate],
                }
            )
    acquisition = []
    for candidate in PRIMARY_CANDIDATES:
        rows = summaries[candidate]["trajectory_preserving"]
        acquisition.append(
            {
                "candidate": candidate,
                "contract": statistics.median(item["stable_contract_bytes"] for item in rows),
                "tool_schema": statistics.median(item["tool_schema_bytes"] for item in rows),
                "state": statistics.median(item["dynamic_row_bytes"] for item in rows),
                "epistemic": statistics.median(
                    item["semantic_context_bytes"] + item["epistemic_bytes"] for item in rows
                ),
                "grounding": statistics.median(item["grounding_bytes"] for item in rows),
                "maintenance": statistics.median(
                    item["maintenance_bytes"] + item["error_bytes"] for item in rows
                ),
                "total": statistics.median(
                    item["acquisition_inclusive_taskview_bytes"] for item in rows
                ),
            }
        )
    return {
        "serializer": serializer_hash(),
        "sql_facts": ledger.sql_facts,
        "campaign_id": ledger.campaign_id,
        "campaign_seal_sha256": ledger.campaign_seal_sha256,
        "manifest_sha256": ledger.manifest_sha256,
        "reconstruction": {
            episode.replicate: {
                "ok": episode.reconstruction_ok,
                "notes": episode.reconstruction_notes,
                "accesses": len(episode.accesses),
            }
            for episode in ledger.episodes
        },
        "budgets": ledger.budgets,
        "safety": safety,
        "summaries": summaries,
        "tables": {
            "trajectory_preserving": table["trajectory_preserving"],
            "mechanical_dedup_floor": table["mechanical_dedup_floor"],
            "acquisition_decomposition": acquisition,
            "savings_sources": savings_sources(summaries),
        },
        "admissions": admissions,
        "greed": greed,
        "participant_inference_calls": 0,
    }
