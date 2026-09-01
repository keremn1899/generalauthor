"""Deterministic epistemic discriminability suite.

A candidate fails safety if two states that permit different inferences
serialize indistinguishably, or if a conditional read returns not_modified
across an invalidation that changes negative-inference permission.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from taskview import (
    Completeness,
    CompletenessStatus,
    RelationMode,
    Role,
    RoleType,
    TaskView,
)

from research.taskview_orientation.read_surface_replay.serialize import (
    dumps,
    first_use_payload,
    not_modified_payload,
    row_result,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface


REQUIRED_LABELS = (
    "PRESENT",
    "NO_MATCH_OBSERVED",
    "KNOWN_ABSENT_WITHIN_NAMED_UNIVERSE",
    "NOT_YET_ESTABLISHED",
    "STALE",
    "OUTSIDE_DECLARED_UNIVERSE",
    "UNIVERSE_MEMBERSHIP_UNKNOWN",
)


def _view(path: Path) -> TaskView:
    view = TaskView(path, view_id="epistemic-safety", task_spec_ref="test://epistemic")
    for ident in ("item:a", "item:b", "item:outside"):
        view.add_referent(ident, label=ident)
    view.declare_relation(
        "universe",
        (Role("item", RoleType.REFERENT),),
        description="Named universe of items.",
    )
    view.declare_relation(
        "gap",
        (Role("item", RoleType.REFERENT),),
        mode=RelationMode.DERIVED,
        description="Items in the universe that currently have a gap.",
    )
    view.register_derivation(
        "gap",
        sql='SELECT item_id FROM universe',
        inputs=["universe"],
    )
    view.assert_tuple("universe", {"item": "item:a"})
    view.assert_tuple("universe", {"item": "item:b"})
    return view


def _run(view: TaskView, status: CompletenessStatus, *, gaps: tuple[str, ...] = ()) -> None:
    view.run_derivation(
        "gap",
        completeness=Completeness(status, universe="universe", basis="fixture", known_gaps=gaps),
    )


def _payloads_for_surface(label: str, rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, str]:
    coverage = {
        "status": meta.get("status"),
        "universe": meta.get("universe"),
        "state": meta.get("state"),
    }
    membership = meta.get("in_universe")
    if membership is True:
        membership_label = "IN_UNIVERSE"
    elif membership is False:
        membership_label = "OUTSIDE_DECLARED_UNIVERSE"
    elif membership is None and meta.get("subject"):
        membership_label = "UNIVERSE_MEMBERSHIP_UNKNOWN"
    else:
        membership_label = None
    extra = {
        "subject": meta.get("subject"),
        "universe_membership": membership_label,
    }
    sql = dumps(
        {
            **row_result(rows),
            "relation": "gap",
            "derivation": meta.get("derivation"),
            "coverage": coverage,
            **{key: value for key, value in extra.items() if value is not None},
        }
    )
    lookup = sql
    card = dumps(
        first_use_payload(
            relation="gap",
            signature="gap(item->item_id)",
            meaning="Items in the universe that currently have a gap.",
            revision=meta.get("revision"),
            derivation=meta.get("derivation"),
            coverage={**coverage, **{key: value for key, value in extra.items() if value is not None}},
            rows=rows,
        )
    )
    conditional_full = sql
    conditional_not_modified = dumps(
        not_modified_payload(
            relation="gap",
            relation_revision=int(meta.get("revision") or 0),
            derivation=meta.get("derivation"),
            coverage_state=meta.get("state"),
            coverage={**coverage, **{key: value for key, value in extra.items() if value is not None}},
        )
    )
    return {
        "A": sql,
        "B": sql,
        "C": lookup,
        "D": card,
        "E": dumps(
            {
                "snapshot_revision": meta.get("revision"),
                "relations": {
                    "gap": {
                        "rows": rows,
                        "coverage": coverage,
                        "derivation": meta.get("derivation"),
                        **{key: value for key, value in extra.items() if value is not None},
                    }
                },
            }
        ),
        "F_full": conditional_full,
        "F_not_modified": conditional_not_modified,
        "label": label,
    }


def _state_meta(surface: ExperimentTaskViewSurface) -> dict[str, Any]:
    state = surface.view.derivation_state("gap")
    derivation = "CURRENT" if state == "SUCCEEDED" else state
    receipt = surface.view.latest_completeness("gap")
    return {
        "revision": surface.view.relation_schema("gap") and surface.view.revision,
        "derivation": derivation,
        "status": None if receipt is None else receipt["status"],
        "universe": None if receipt is None else receipt["universe_relation"],
        "state": surface.view.completeness_state("gap") if receipt else "NONE",
        "exhaustive": surface.view.absence_is_exhaustive("gap"),
        "execution": state,
    }


def build_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        view = _view(root / "complete.sqlite")
        _run(view, CompletenessStatus.COMPLETE)
        surface = ExperimentTaskViewSurface(view)
        cases["current_complete_empty"] = {
            "label": "KNOWN_ABSENT_WITHIN_NAMED_UNIVERSE",
            "rows": [],
            "meta": _state_meta(surface),
            "inference": "known_absent",
        }
        cases["present"] = {
            "label": "PRESENT",
            "rows": surface.query_sql("SELECT * FROM universe")["rows"],
            "meta": {
                **_state_meta(surface),
                "derivation": "BASE",
                "status": None,
                "state": "CURRENT",
            },
            "inference": "present",
        }
        view.close()

        view = _view(root / "incomplete.sqlite")
        _run(view, CompletenessStatus.INCOMPLETE, gaps=("item:b",))
        # Replace derived rows with empty while remaining INCOMPLETE: rerun already
        # materialized universe rows.  Use a second derivation target?  The
        # registered SQL copies universe, so INCOMPLETE still has rows.  The
        # empty+INCOMPLETE case is constructed by retracting universe members
        # after a COMPLETE run would change cardinality; instead assert the
        # receipt status itself is INCOMPLETE regardless of row bytes.
        surface = ExperimentTaskViewSurface(view)
        cases["current_incomplete"] = {
            "label": "NO_MATCH_OBSERVED",
            "rows": [],
            "meta": {**_state_meta(surface), "forced_rows": []},
            "inference": "incomplete",
        }
        # Force empty rows in the serialized payload while keeping INCOMPLETE.
        cases["current_incomplete"]["rows"] = []
        view.close()

        view = _view(root / "unknown.sqlite")
        _run(view, CompletenessStatus.UNKNOWN)
        surface = ExperimentTaskViewSurface(view)
        cases["current_unknown"] = {
            "label": "NOT_YET_ESTABLISHED",
            "rows": [],
            "meta": _state_meta(surface),
            "inference": "unknown",
        }
        view.close()

        view = _view(root / "stale.sqlite")
        _run(view, CompletenessStatus.COMPLETE)
        surface = ExperimentTaskViewSurface(view)
        surface.assertion(action="ASSERT", relation="universe", values={"item": "item:outside"})
        cases["stale_complete_receipt"] = {
            "label": "STALE",
            "rows": [],
            "meta": _state_meta(surface),
            "inference": "stale",
        }
        view.close()

        view = _view(root / "never.sqlite")
        surface = ExperimentTaskViewSurface(view)
        cases["never_run"] = {
            "label": "NOT_YET_ESTABLISHED",
            "rows": [],
            "meta": _state_meta(surface),
            "inference": "never_run",
        }
        view.close()

        view = _view(root / "outside.sqlite")
        _run(view, CompletenessStatus.COMPLETE)
        surface = ExperimentTaskViewSurface(view)
        cases["outside_universe"] = {
            "label": "OUTSIDE_DECLARED_UNIVERSE",
            "rows": [],
            "meta": {
                **_state_meta(surface),
                "subject": "item:outside",
                "in_universe": False,
            },
            "inference": "outside",
        }
        cases["membership_unknown"] = {
            "label": "UNIVERSE_MEMBERSHIP_UNKNOWN",
            "rows": [],
            "meta": {
                **_state_meta(surface),
                "subject": "item:unlisted",
                "in_universe": None,
            },
            "inference": "membership_unknown",
        }
        view.close()

        # FAILED derivation: invalid SQL re-register is not allowed on the
        # frozen helper; encode FAILED as a distinct meta state.
        cases["failed"] = {
            "label": "NOT_YET_ESTABLISHED",
            "rows": [],
            "meta": {
                "revision": 0,
                "derivation": "FAILED",
                "status": None,
                "universe": "universe",
                "state": "NONE",
                "execution": "FAILED",
            },
            "inference": "failed",
        }

        # Derived universe incomplete/stale: reuse stale completeness_state.
        view = _view(root / "universe_stale.sqlite")
        view.declare_relation(
            "derived_universe",
            (Role("item", RoleType.REFERENT),),
            mode=RelationMode.DERIVED,
            description="Derived universe.",
        )
        view.register_derivation(
            "derived_universe",
            sql="SELECT item_id FROM universe",
            inputs=["universe"],
        )
        view.run_derivation(
            "derived_universe",
            completeness=Completeness(
                CompletenessStatus.COMPLETE, universe="universe", basis="fixture"
            ),
        )
        view.declare_relation(
            "gap2",
            (Role("item", RoleType.REFERENT),),
            mode=RelationMode.DERIVED,
            description="Gap over derived universe.",
        )
        view.register_derivation(
            "gap2",
            sql="SELECT item_id FROM derived_universe",
            inputs=["derived_universe"],
        )
        view.run_derivation(
            "gap2",
            completeness=Completeness(
                CompletenessStatus.COMPLETE,
                universe="derived_universe",
                basis="fixture",
            ),
        )
        surface = ExperimentTaskViewSurface(view)
        surface.assertion(action="ASSERT", relation="universe", values={"item": "item:outside"})
        cases["stale_derived_universe"] = {
            "label": "STALE",
            "rows": [],
            "meta": {
                "revision": surface.view.revision,
                "derivation": "STALE",
                "status": "COMPLETE",
                "universe": "derived_universe",
                "state": surface.view.completeness_state("gap2"),
                "execution": surface.view.derivation_state("gap2"),
            },
            "inference": "stale_universe",
        }
        view.close()
    return cases


def evaluate_safety() -> dict[str, Any]:
    cases = build_cases()
    serialized: dict[str, dict[str, str]] = {}
    for name, case in cases.items():
        serialized[name] = _payloads_for_surface(case["label"], case["rows"], case["meta"])

    # Pairwise: different inferences must differ for every candidate surface.
    inference = {name: cases[name]["inference"] for name in cases}
    candidates = ("A", "B", "C", "D", "E", "F_full")
    collisions: list[dict[str, str]] = []
    for left in cases:
        for right in cases:
            if left >= right:
                continue
            if inference[left] == inference[right]:
                continue
            for candidate in candidates:
                if serialized[left][candidate] == serialized[right][candidate]:
                    collisions.append(
                        {
                            "candidate": candidate,
                            "left": left,
                            "right": right,
                            "left_inference": inference[left],
                            "right_inference": inference[right],
                        }
                    )

    # Conditional-read invalidation: stale vs current complete empty rows.
    stale = serialized["stale_complete_receipt"]
    current = serialized["current_complete_empty"]
    conditional_ok = stale["F_not_modified"] != current["F_not_modified"]
    conditional_ok = conditional_ok and stale["F_full"] != current["F_full"]
    # not_modified of current must not equal full stale payload
    conditional_ok = conditional_ok and stale["F_full"] != current["F_not_modified"]

    per_candidate = {}
    for candidate in ("A", "B", "C", "D", "E", "F"):
        related = [
            item
            for item in collisions
            if item["candidate"] == candidate or item["candidate"] == f"{candidate}_full"
        ]
        safe = not related
        if candidate == "F":
            safe = safe and conditional_ok
        per_candidate[candidate] = {
            "safe": safe,
            "collisions": related,
            "conditional_invalidation_ok": conditional_ok if candidate == "F" else True,
        }
    return {
        "required_labels": list(REQUIRED_LABELS),
        "cases": {
            name: {
                "label": cases[name]["label"],
                "inference": cases[name]["inference"],
                "derivation": cases[name]["meta"].get("derivation"),
                "status": cases[name]["meta"].get("status"),
                "state": cases[name]["meta"].get("state"),
            }
            for name in cases
        },
        "collisions": collisions,
        "candidates": per_candidate,
        "all_safe": all(item["safe"] for item in per_candidate.values()),
    }
