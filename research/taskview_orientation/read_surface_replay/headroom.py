"""Behavioral headroom / break-even map for candidate B.

This is not a valid counterfactual of participant behavior.  It answers only:

    How much of the observed B trajectory has to disappear for acquisition-
    inclusive TaskView bytes to fall below the repository-orientation budget?

No participant or provider inference.  Serializers stay frozen.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from research.taskview_orientation.read_surface_replay import SEALED_RESULTS_ROOT
from research.taskview_orientation.read_surface_replay.accounting import summarize_episode
from research.taskview_orientation.read_surface_replay.candidates import (
    ChargedItem,
    ReplayState,
    TOOL_SCHEMAS,
    _a_read_item,
    _charge,
    _maintenance_item,
    _query_item,
    contract_for,
    replay_episode,
)
from research.taskview_orientation.read_surface_replay.ledger import (
    CampaignLedger,
    EpisodeLedger,
    LogicalAccess,
)
from research.taskview_orientation.read_surface_replay.serialize import (
    dumps,
    stable_contract_text,
    tool_schema_payload,
)


# Local-name / cell match floor.  Short tokens ("v2", "id") are not evidence
# that a returned row contributed to the written conclusion.
MIN_MATCH_CHARS = 4

# Frozen oracle-field → relation map.  This is not participant intent.
# It is a sensitivity definition: relations that hold the sealed oracle's
# TaskView-addressable facts for each phase.
ORACLE_REQUIRED_RELATIONS: dict[int, frozenset[str]] = {
    1: frozenset({"requires_change"}),
    2: frozenset({"protected_by", "compatible_via", "verified_by"}),
    3: frozenset({"excluded", "boundary", "unresolved_scope", "boundary_affected_service"}),
    4: frozenset({"verified_by", "verification_gap"}),
    5: frozenset({"verification_gap", "affected_service", "unresolved_scope"}),
}

COMPACT_EPISTEMIC_KEYS = ("relation", "state", "derivation", "completeness")

# Named scenarios.  Order is report order, not search order.
SCENARIO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "B_as_observed",
        "describe": "full",
        "sql": "full",
        "speculative_keep": 1.0,
        "conservative": False,
        "note": "Trajectory-preserving B. Not a counterfactual.",
    },
    {
        "id": "drop_contract_redundant_describe",
        "describe": "drop_redundant",
        "sql": "full",
        "speculative_keep": 1.0,
        "conservative": True,
        "note": "Contract-redundant targeted describes disappear; mixed describes compact to epistemic remainder; SQL unchanged.",
    },
    {
        "id": "answer_supported_breadth_only",
        "describe": "full",
        "sql": "contributing",
        "speculative_keep": 0.0,
        "conservative": False,
        "note": "Keep SQL only for relations whose returned cells or relation name appear in the citation-stripped phase answer.",
    },
    {
        "id": "redundant_describe_and_contributing_breadth",
        "describe": "drop_redundant",
        "sql": "contributing",
        "speculative_keep": 0.0,
        "conservative": False,
        "note": "Both cuts. Completeness scans that did not mark the answer are dropped.",
    },
    {
        "id": "both_epistemic_conservative",
        "describe": "drop_redundant",
        "sql": "contributing",
        "speculative_keep": 0.0,
        "conservative": True,
        "note": "Both cuts, but why-describes, compact completeness/currentness, and post-mutation derived reads stay.",
    },
    {
        "id": "redundant_describe_plus_25pct_speculative_cut",
        "describe": "drop_redundant",
        "sql": "full",
        "speculative_keep": 0.75,
        "conservative": True,
        "note": "Drop contract-redundant describes and the largest speculative (phase, relation) groups until ≤75% of speculative SQL bytes remain.",
    },
    {
        "id": "all_relation_describe_gone_plus_half_breadth",
        "describe": "drop_all_relation",
        "sql": "half_breadth",
        "speculative_keep": 0.5,
        "conservative": True,
        "note": "Harsh bound: every relation describe gone; keep half the queried (phase, relation) pairs, preferring answer-supported ones.",
    },
    {
        "id": "fixed_overhead_only",
        "describe": "drop_all_describe",
        "sql": "none",
        "speculative_keep": 0.0,
        "conservative": False,
        "note": "Lower bound under B: contract + tool schema + assertion/rerun. No TaskView reads.",
    },
)

# Least-to-most severe search.  First combo with acq < budget is the break-even.
BREAK_EVEN_SEARCH: tuple[str, ...] = (
    "drop_contract_redundant_describe",
    "redundant_describe_plus_25pct_speculative_cut",
    "both_epistemic_conservative",
    "redundant_describe_and_contributing_breadth",
    "all_relation_describe_gone_plus_half_breadth",
    "fixed_overhead_only",
)


@dataclass(frozen=True)
class HeadroomPolicy:
    describe: str
    sql: str
    speculative_keep: float
    conservative: bool


def _strip_citations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_citations(item)
            for key, item in value.items()
            if key != "citations"
        }
    if isinstance(value, list):
        return [_strip_citations(item) for item in value]
    return value


def load_phase_answers(episode: EpisodeLedger) -> dict[int, Any]:
    path = SEALED_RESULTS_ROOT / episode.episode_id / "record.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    return {int(item["phase"]): item["answer"] for item in record["answers"]}


def answer_blob(answer: Any) -> str:
    return json.dumps(_strip_citations(answer), ensure_ascii=False).lower()


def cell_matches_answer(cell: Any, blob: str) -> bool:
    if cell is None or isinstance(cell, bool):
        return False
    text = str(cell).strip()
    if len(text) < MIN_MATCH_CHARS:
        return False
    lowered = text.lower()
    if lowered in blob:
        return True
    if ":" in text:
        local = text.rsplit(":", 1)[-1].strip()
        if len(local) >= MIN_MATCH_CHARS and local.lower() in blob:
            return True
    return False


def sql_supported_by_answer(access: LogicalAccess, blob: str) -> bool:
    if access.sql is None or access.is_error:
        return False
    relation = access.sql.relation
    if relation and relation.lower() in blob:
        return True
    for row in access.returned_rows:
        for cell in row.values():
            if cell_matches_answer(cell, blob):
                return True
    return False


def classify_relation_describe(access: LogicalAccess) -> str:
    """Mechanical split of targeted describe(relation), not model intent."""

    if access.operation != "describe" or access.describe_kind != "relation":
        return "not_relation"
    if access.is_error:
        return "epistemic_error"
    payload = access.reconstructed_payload if isinstance(access.reconstructed_payload, dict) else {}
    relation = payload.get("relation") or {}
    mode = relation.get("mode")
    completeness = relation.get("completeness")
    derivation = relation.get("derivation")
    state = relation.get("state")
    if completeness:
        return "epistemic_bearing"
    if mode == "DERIVED":
        return "epistemic_bearing"
    if derivation and derivation not in {"BASE"}:
        return "epistemic_bearing"
    if state and state != "CURRENT":
        return "epistemic_bearing"
    return "contract_redundant"


def compact_epistemic_body(access: LogicalAccess) -> str:
    payload = access.reconstructed_payload if isinstance(access.reconstructed_payload, dict) else {}
    relation = payload.get("relation") or {}
    name = relation.get("name") or (access.raw_arguments or {}).get("relation")
    compact: dict[str, Any] = {}
    for key in COMPACT_EPISTEMIC_KEYS:
        if key == "relation":
            if name:
                compact["relation"] = name
            continue
        value = relation.get(key)
        if value is None:
            continue
        if key == "derivation" and isinstance(value, dict):
            stripped = {inner: item for inner, item in value.items() if inner != "inputs"}
            if stripped:
                compact[key] = stripped
            continue
        compact[key] = value
    return dumps(compact)


def contributing_relations(episode: EpisodeLedger) -> dict[int, set[str]]:
    answers = load_phase_answers(episode)
    out: dict[int, set[str]] = {phase: set() for phase in range(1, 6)}
    blobs = {phase: answer_blob(answers[phase]) for phase in answers}
    for access in episode.accesses:
        if access.operation != "query_sql" or access.sql is None:
            continue
        blob = blobs.get(access.phase, "")
        if sql_supported_by_answer(access, blob):
            out[access.phase].add(access.sql.relation)
    return out


def conservative_sql_sequences(episode: EpisodeLedger) -> set[int]:
    """Sequences that remain if epistemic checks stay fully conservative.

    Kept mechanically:
    - first successful DERIVED query that carries a completeness receipt,
      per (relation, relevant_revision_token);
    - successful query_sql after an assertion/rerun in the same phase whose
      relation is the asserted or rerun relation.
    """

    keep: set[int] = set()
    seen_complete: set[tuple[str, str]] = set()
    mutated: dict[int, set[str]] = defaultdict(set)
    for access in episode.accesses:
        if access.operation in {"assertion", "rerun"} and not access.is_error:
            name = (access.raw_arguments or {}).get("relation")
            if isinstance(name, str) and name:
                mutated[access.phase].add(name)
        if access.operation != "query_sql" or access.is_error or access.sql is None:
            continue
        relation = access.sql.relation
        meaning = (access.relation_meanings or {}).get(relation) or {}
        has_completeness = bool(access.completeness_status.get(relation))
        if meaning.get("mode") == "DERIVED" and has_completeness:
            token = (relation, access.relevant_revision_token)
            if token not in seen_complete:
                seen_complete.add(token)
                keep.add(access.sequence)
        if relation in mutated[access.phase]:
            keep.add(access.sequence)
    return keep


def _b_init_items(episode: EpisodeLedger, *, level: str) -> list[ChargedItem]:
    contract_body = stable_contract_text(contract_for(episode))
    tool_body = dumps(tool_schema_payload(TOOL_SCHEMAS["B"]))
    return [
        ChargedItem(
            candidate="B",
            level=level,
            replicate=episode.replicate,
            phase=0,
            operation="contract",
            kind="stable_contract",
            body=contract_body,
            categories=_charge(
                contract_body, {"stable_contract": len(contract_body.encode("utf-8"))}
            ),
        ),
        ChargedItem(
            candidate="B",
            level=level,
            replicate=episode.replicate,
            phase=0,
            operation="tool_schema",
            kind="tool_schema",
            body=tool_body,
            categories=_charge(tool_body, {"tool_schema": len(tool_body.encode("utf-8"))}),
        ),
    ]


def _compact_describe_item(
    episode: EpisodeLedger, access: LogicalAccess, *, level: str
) -> ChargedItem:
    body = compact_epistemic_body(access)
    return ChargedItem(
        candidate="B",
        level=level,
        replicate=episode.replicate,
        phase=access.phase,
        operation="describe",
        kind="describe_relation_compact",
        body=body,
        categories=_charge(body, {"epistemic": len(body.encode("utf-8"))}),
        query_key=f"compact|{access.raw_arguments.get('relation')}|{access.relevant_revision_token}",
    )


def _sql_group_bytes(episode: EpisodeLedger) -> dict[tuple[int, str], int]:
    state = ReplayState()
    out: dict[tuple[int, str], int] = defaultdict(int)
    for access in episode.accesses:
        if access.operation != "query_sql" or access.sql is None or access.is_error:
            continue
        item = _query_item(episode, "B", "trajectory_preserving", access, state)
        out[(access.phase, access.sql.relation)] += item.total
    return dict(out)


def _drop_speculative_to_frac(
    keys: set[tuple[int, str]],
    contributing: dict[int, set[str]],
    group_bytes: dict[tuple[int, str], int],
    keep_frac: float,
    *,
    protected: set[tuple[int, str]] | None = None,
) -> set[tuple[int, str]]:
    protected = protected or set()
    contrib = {key for key in keys if key[1] in contributing.get(key[0], set())} | (
        protected & keys
    )
    speculative = [key for key in keys if key not in contrib]
    if keep_frac >= 1.0:
        return set(keys)
    if keep_frac <= 0.0:
        return contrib
    spec_total = sum(group_bytes.get(key, 0) for key in speculative)
    budget = spec_total * keep_frac
    speculative.sort(key=lambda key: (-group_bytes.get(key, 0), key[0], key[1]))
    remaining = set(speculative)
    remaining_bytes = spec_total
    for key in speculative:
        if remaining_bytes <= budget:
            break
        remaining.discard(key)
        remaining_bytes -= group_bytes.get(key, 0)
    return contrib | remaining


def _half_breadth(
    keys: set[tuple[int, str]], contributing: dict[int, set[str]]
) -> set[tuple[int, str]]:
    by_phase: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for key in keys:
        by_phase[key[0]].append(key)
    keep: set[tuple[int, str]] = set()
    for phase, group in by_phase.items():
        target = (len(group) + 1) // 2
        ranked = sorted(
            group,
            key=lambda key: (
                0 if key[1] in contributing.get(phase, set()) else 1,
                key[1],
            ),
        )
        keep.update(ranked[:target])
    return keep


def selected_sql_keys(
    episode: EpisodeLedger,
    policy: HeadroomPolicy,
    contributing: dict[int, set[str]],
    conservative_seq: set[int],
    group_bytes: dict[tuple[int, str], int],
) -> set[tuple[int, str]]:
    all_keys: set[tuple[int, str]] = set()
    seq_to_key: dict[int, tuple[int, str]] = {}
    for access in episode.accesses:
        if access.operation != "query_sql" or access.sql is None or access.is_error:
            continue
        key = (access.phase, access.sql.relation)
        all_keys.add(key)
        seq_to_key[access.sequence] = key
    if policy.sql == "none":
        return set()
    if policy.sql == "full":
        keys = set(all_keys)
        if policy.speculative_keep < 1.0:
            protected = set()
            if policy.conservative:
                protected = {seq_to_key[seq] for seq in conservative_seq if seq in seq_to_key}
            keys = _drop_speculative_to_frac(
                keys,
                contributing,
                group_bytes,
                policy.speculative_keep,
                protected=protected,
            )
        return keys
    if policy.sql == "contributing":
        keys = {key for key in all_keys if key[1] in contributing.get(key[0], set())}
        if policy.conservative:
            keys |= {seq_to_key[seq] for seq in conservative_seq if seq in seq_to_key}
        return keys
    if policy.sql == "oracle":
        keys = {
            key
            for key in all_keys
            if key[1] in ORACLE_REQUIRED_RELATIONS.get(key[0], frozenset())
        }
        if policy.conservative:
            keys |= {seq_to_key[seq] for seq in conservative_seq if seq in seq_to_key}
        return keys
    if policy.sql == "half_breadth":
        return _half_breadth(all_keys, contributing)
    raise ValueError(f"unknown sql policy {policy.sql}")


def keep_describe(access: LogicalAccess, policy: HeadroomPolicy) -> str:
    """Return skip / full / compact."""

    kind = access.describe_kind
    if kind == "catalog":
        return "skip"
    if kind == "why":
        if policy.describe == "drop_all_describe":
            return "skip"
        if policy.conservative or policy.describe != "drop_all_relation":
            return "full"
        return "skip"
    if kind != "relation":
        return "skip"
    bucket = classify_relation_describe(access)
    if policy.describe == "full":
        return "full"
    if policy.describe in {"drop_all_describe", "drop_all_relation"}:
        return "skip"
    # drop_redundant: BASE+CURRENT vocabulary calls vanish; mixed compact.
    if bucket == "contract_redundant":
        return "skip"
    if bucket == "epistemic_error":
        return "full"
    return "compact"


def replay_b_headroom(episode: EpisodeLedger, policy: HeadroomPolicy) -> list[ChargedItem]:
    level = "headroom"
    contributing = contributing_relations(episode)
    conservative_seq = conservative_sql_sequences(episode)
    group_bytes = _sql_group_bytes(episode)
    sql_keys = selected_sql_keys(
        episode, policy, contributing, conservative_seq, group_bytes
    )
    items = _b_init_items(episode, level=level)
    state = ReplayState()
    for access in episode.accesses:
        if access.operation == "describe":
            action = keep_describe(access, policy)
            if action == "skip":
                continue
            if action == "compact":
                items.append(_compact_describe_item(episode, access, level=level))
                continue
            items.append(
                _a_read_item(
                    episode, "B", level, access, kind=f"describe_{access.describe_kind}"
                )
            )
            continue
        if access.operation in {"assertion", "rerun"}:
            items.append(_maintenance_item(episode, "B", level, access))
            continue
        if access.operation == "query_sql":
            if access.sql is None or access.is_error:
                continue
            if (access.phase, access.sql.relation) not in sql_keys:
                continue
            items.append(_query_item(episode, "B", level, access, state))
    return items


def _kind_totals(items: list[ChargedItem]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for item in items:
        out[item.kind] += item.total
    return dict(out)


def episode_anatomy(episode: EpisodeLedger) -> dict[str, Any]:
    contributing = contributing_relations(episode)
    conservative_seq = conservative_sql_sequences(episode)
    group_bytes = _sql_group_bytes(episode)
    answers = load_phase_answers(episode)
    queried: dict[str, list[str]] = {}
    speculative_bytes = 0
    contributing_bytes = 0
    phase_rows = []
    for phase in range(1, 6):
        rels = sorted(
            {
                access.sql.relation
                for access in episode.accesses
                if access.operation == "query_sql"
                and access.sql
                and not access.is_error
                and access.phase == phase
            }
        )
        queried[str(phase)] = rels
        contrib = sorted(contributing[phase])
        spec = [name for name in rels if name not in contributing[phase]]
        c_bytes = sum(group_bytes.get((phase, name), 0) for name in contrib)
        s_bytes = sum(group_bytes.get((phase, name), 0) for name in spec)
        contributing_bytes += c_bytes
        speculative_bytes += s_bytes
        phase_rows.append(
            {
                "phase": phase,
                "queried": rels,
                "answer_supported": contrib,
                "oracle_required": sorted(ORACLE_REQUIRED_RELATIONS[phase]),
                "speculative": spec,
                "answer_supported_sql_bytes": c_bytes,
                "speculative_sql_bytes": s_bytes,
                "answer_blob_chars": len(answer_blob(answers[phase])),
            }
        )
    describe_rows = []
    redundant_bytes = 0
    epistemic_full_bytes = 0
    epistemic_compact_bytes = 0
    why_bytes = 0
    for access in episode.accesses:
        if access.operation != "describe" or access.describe_kind == "catalog":
            continue
        if access.describe_kind == "why":
            item = _a_read_item(
                episode, "B", "trajectory_preserving", access, kind="describe_why"
            )
            why_bytes += item.total
            describe_rows.append(
                {
                    "phase": access.phase,
                    "kind": "why",
                    "class": "grounding",
                    "full_bytes": item.total,
                    "compact_bytes": item.total,
                    "error": access.is_error,
                }
            )
            continue
        bucket = classify_relation_describe(access)
        full = _a_read_item(
            episode, "B", "trajectory_preserving", access, kind="describe_relation"
        )
        compact = compact_epistemic_body(access) if bucket == "epistemic_bearing" else ""
        compact_n = len(compact.encode("utf-8")) if compact else 0
        if bucket == "contract_redundant":
            redundant_bytes += full.total
        else:
            epistemic_full_bytes += full.total
            epistemic_compact_bytes += compact_n
        describe_rows.append(
            {
                "phase": access.phase,
                "kind": "relation",
                "relation": (access.raw_arguments or {}).get("relation"),
                "class": bucket,
                "full_bytes": full.total,
                "compact_bytes": compact_n,
            }
        )
    observed = replay_episode(episode, "B", "trajectory_preserving")
    acq = sum(item.total for item in observed)
    budget = episode.raw_o_post - episode.repository_o_post
    kinds = _kind_totals(observed)
    fixed = (
        kinds.get("stable_contract", 0)
        + kinds.get("tool_schema", 0)
        + kinds.get("assertion", 0)
        + kinds.get("rerun", 0)
    )
    return {
        "replicate": episode.replicate,
        "episode_id": episode.episode_id,
        "budget": budget,
        "observed_acq": acq,
        "observed_gap": acq - budget,
        "fixed_overhead_bytes": fixed,
        "fixed_overhead_exceeds_budget": fixed >= budget,
        "row_bytes": kinds.get("rows", 0),
        "describe_relation_bytes": kinds.get("describe_relation", 0),
        "describe_why_bytes": why_bytes,
        "contract_redundant_describe_bytes": redundant_bytes,
        "epistemic_describe_full_bytes": epistemic_full_bytes,
        "epistemic_describe_compact_bytes": epistemic_compact_bytes,
        "vocabulary_strip_savings": redundant_bytes
        + max(0, epistemic_full_bytes - epistemic_compact_bytes),
        "contributing_sql_bytes": contributing_bytes,
        "speculative_sql_bytes": speculative_bytes,
        "conservative_sql_sequences": sorted(conservative_seq),
        "conservative_sql_count": len(conservative_seq),
        "queried_relation_counts": {phase: len(names) for phase, names in queried.items()},
        "answer_supported_relation_counts": {
            str(phase): len(names) for phase, names in contributing.items()
        },
        "phases": phase_rows,
        "describes": describe_rows,
        "limitations": [
            "Answer support matches cell text / referent local-name / relation name into the citation-stripped phase answer. Shared identifiers (checkout, reporting) over-include relations that merely mention the same entity.",
            "Prose conclusions without those tokens under-include. Relation-name substring match over-includes when the answer discusses the relation without using its rows.",
            "This is an accounting floor, not a prediction that a live agent would query only the contributing set.",
        ],
    }


def _gap_after_describe_cut(anatomy: dict[str, Any]) -> dict[str, Any]:
    """Bytes still needed after contract-redundant describes disappear."""

    gap = anatomy["observed_gap"]
    describe_cut = anatomy["vocabulary_strip_savings"]
    remaining = gap - describe_cut
    spec = anatomy["speculative_sql_bytes"]
    contrib = anatomy["contributing_sql_bytes"]
    needed_spec_frac = None
    needed_all_sql_frac = None
    if remaining > 0 and spec > 0 and remaining <= spec:
        needed_spec_frac = remaining / spec
    if remaining > 0 and (spec + contrib) > 0 and remaining <= (spec + contrib):
        needed_all_sql_frac = remaining / (spec + contrib)
    return {
        "gap_after_vocabulary_strip": remaining,
        "speculative_sql_fraction_that_must_disappear": needed_spec_frac,
        "all_sql_fraction_that_must_disappear": needed_all_sql_frac,
        "crosses_zero_from_describe_cut_alone": remaining <= 0,
        "crosses_zero_if_all_speculative_sql_also_dropped": remaining - spec <= 0,
        "still_short_after_zero_sql": remaining - spec - contrib > 0,
    }


def _scenario_row(
    episode: EpisodeLedger, spec: dict[str, Any], anatomy: dict[str, Any]
) -> dict[str, Any]:
    policy = HeadroomPolicy(
        describe=spec["describe"],
        sql=spec["sql"],
        speculative_keep=float(spec["speculative_keep"]),
        conservative=bool(spec["conservative"]),
    )
    items = replay_b_headroom(episode, policy)
    summary = summarize_episode(episode, "B", spec["id"], items)
    kinds = _kind_totals(items)
    return {
        "id": spec["id"],
        "note": spec["note"],
        "replicate": episode.replicate,
        "acquisition_inclusive_taskview_bytes": summary["acquisition_inclusive_taskview_bytes"],
        "budget": anatomy["budget"],
        "net_orientation_delta_acq": summary["net_orientation_delta_acq"],
        "win": summary["net_orientation_delta_acq"] < 0,
        "kind_bytes": kinds,
        "sql_calls_kept": sum(1 for item in items if item.kind == "rows"),
        "relation_describes_kept": sum(
            1
            for item in items
            if item.kind in {"describe_relation", "describe_relation_compact"}
        ),
        "why_describes_kept": sum(1 for item in items if item.kind == "describe_why"),
    }


def _break_even_for_replicate(scenario_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["id"]: row for row in scenario_rows}
    for scenario_id in BREAK_EVEN_SEARCH:
        row = by_id[scenario_id]
        if row["win"]:
            return {
                "scenario_id": scenario_id,
                "net": row["net_orientation_delta_acq"],
                "possible": True,
            }
    return {
        "scenario_id": None,
        "net": by_id["fixed_overhead_only"]["net_orientation_delta_acq"],
        "possible": False,
        "blocker": "B fixed overhead (contract + tool schema + assertion/rerun) already exceeds the orientation budget",
    }


def _aggregate_scenario(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nets = [row["net_orientation_delta_acq"] for row in rows]
    wins = sum(row["win"] for row in rows)
    return {
        "id": rows[0]["id"],
        "note": rows[0]["note"],
        "R1": rows[0]["net_orientation_delta_acq"],
        "R2": rows[1]["net_orientation_delta_acq"],
        "R3": rows[2]["net_orientation_delta_acq"],
        "R4": rows[3]["net_orientation_delta_acq"],
        "median": statistics.median(nets),
        "wins": wins,
        "R1_acq": rows[0]["acquisition_inclusive_taskview_bytes"],
        "R2_acq": rows[1]["acquisition_inclusive_taskview_bytes"],
        "R3_acq": rows[2]["acquisition_inclusive_taskview_bytes"],
        "R4_acq": rows[3]["acquisition_inclusive_taskview_bytes"],
    }


def _justification(aggregates: dict[str, dict[str, Any]], break_evens: list[dict[str, Any]]) -> dict[str, Any]:
    modest = aggregates["redundant_describe_plus_25pct_speculative_cut"]
    both_cons = aggregates["both_epistemic_conservative"]
    harsh = aggregates["all_relation_describe_gone_plus_half_breadth"]
    floor = aggregates["fixed_overhead_only"]
    impossible_count = sum(not item["possible"] for item in break_evens)
    if modest["wins"] >= 3:
        label = "PLAUSIBLE_MODEST_SHIFT"
        prose = (
            "Dropping contract-redundant describes plus a 25% speculative-breadth cut "
            f"already yields {modest['wins']}/4 economic wins. A live T0/T1 contrast "
            "has a plausible causal target on retrieval strategy, not merely catalog bytes."
        )
    elif both_cons["wins"] >= 3:
        label = "PLAUSIBLE_IF_BREADTH_COLLAPSES"
        prose = (
            "Contract-redundant describes plus answer-supported breadth (epistemic checks "
            f"kept) yields {both_cons['wins']}/4 wins. Live T0/T1 is justified only as a "
            "test of whether the contract actually collapses relation breadth and "
            "targeted introspection."
        )
    elif harsh["wins"] >= 3:
        label = "REQUIRES_LARGE_SHIFT"
        prose = (
            "Even removing every relation describe and halving relation breadth is what "
            f"it takes to reach {harsh['wins']}/4. That is an implausibly huge "
            "behavioral change to assume from a stable contract. Do not buy inference "
            "expecting economic wins from T1 alone."
        )
    elif floor["wins"] >= 3:
        label = "REQUIRES_NEAR_ZERO_READS"
        prose = (
            f"Only the no-read fixed-overhead floor reaches {floor['wins']}/4. "
            "A modest describe-plus-25%-speculative cut does not, and neither does "
            "dropping every relation describe and halving breadth. Do not buy "
            "inference expecting T1 to produce net-positive economics. If a live "
            "T0/T1 contrast happens, its only remaining justification is a "
            "retrieval-strategy measurement (Δ breadth, Δ introspection, Δ state "
            "queries, Δ repository exploration) with epistemic caution intact."
        )
    else:
        label = "IMPOSSIBLE_UNDER_B_FIXED_OVERHEAD"
        prose = (
            f"The B fixed overhead already exceeds budget in {impossible_count}/4 "
            "replicates, so no read-side behavioral shift under B can produce a 3/4 "
            "economic win. Stop for economics. A live T0/T1 contrast is only worth "
            "doing if the question is strategy, not net bytes."
        )
    return {
        "label": label,
        "modest_25pct_wins": modest["wins"],
        "both_conservative_wins": both_cons["wins"],
        "harsh_half_breadth_wins": harsh["wins"],
        "fixed_overhead_wins": floor["wins"],
        "replicates_that_cannot_cross_zero_under_B": impossible_count,
        "prose": prose,
    }


def run_headroom(ledger: CampaignLedger) -> dict[str, Any]:
    anatomies = []
    per_episode_scenarios: dict[str, list[dict[str, Any]]] = defaultdict(list)
    break_evens = []
    for episode in ledger.episodes:
        anatomy = episode_anatomy(episode)
        anatomy["describe_cut_math"] = _gap_after_describe_cut(anatomy)
        anatomies.append(anatomy)
        rows = [_scenario_row(episode, spec, anatomy) for spec in SCENARIO_SPECS]
        for row in rows:
            per_episode_scenarios[row["id"]].append(row)
        break_evens.append(
            {
                "replicate": episode.replicate,
                **_break_even_for_replicate(rows),
            }
        )
    aggregates = {
        spec["id"]: _aggregate_scenario(per_episode_scenarios[spec["id"]])
        for spec in SCENARIO_SPECS
    }
    observed_match = []
    for episode, anatomy in zip(ledger.episodes, anatomies):
        items = replay_episode(episode, "B", "trajectory_preserving")
        observed_match.append(
            anatomy["observed_acq"] == sum(item.total for item in items)
        )
    justification = _justification(aggregates, break_evens)
    return {
        "not_valid_behavior": True,
        "question": "How much observed B behavior has to change for acquisition-inclusive TaskView bytes to fall below the orientation budget?",
        "matcher": {
            "min_match_chars": MIN_MATCH_CHARS,
            "oracle_required_relations": {
                str(phase): sorted(names)
                for phase, names in ORACLE_REQUIRED_RELATIONS.items()
            },
            "compact_epistemic_keys": list(COMPACT_EPISTEMIC_KEYS),
        },
        "anatomies": anatomies,
        "scenarios": aggregates,
        "per_replicate": {
            spec["id"]: per_episode_scenarios[spec["id"]] for spec in SCENARIO_SPECS
        },
        "break_even": break_evens,
        "justification": justification,
        "observed_b_totals_match": all(observed_match),
        "live_measurement_if_authorized": {
            "purpose": "Not whether moving the catalog into the contract saves ~8KB (already known). Whether a stable semantic contract alters retrieval strategy.",
            "deltas": [
                "relation_breadth",
                "targeted_introspection",
                "state_queries",
                "repository_exploration",
            ],
            "guardrail": "epistemic caution stays intact (why / completeness / post-mutation checks)",
            "if_barely_move": "flat broad retrieval is the preferred strategy at this scale; TaskView needs a more fundamental delivery/economic model",
            "if_collapse": "uncertainty about the semantic interface was causing overconsumption of TaskView and the repository",
        },
        "participant_inference_calls": 0,
    }
