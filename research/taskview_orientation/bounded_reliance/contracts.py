"""Stable vocabulary plus experimental reliance / freshness contract text."""

from __future__ import annotations

from typing import Any

from research.taskview_orientation.bounded_reliance import TASKVIEW_CONDITIONS
from research.taskview_orientation.surface import ExperimentTaskViewSurface


VOCABULARY_HEADER = (
    "Stable schema-versioned TaskView vocabulary. Relation names, roles, "
    "meanings, and BASE/DERIVED mode do not change with ordinary row updates."
)

CURRENT_EXISTING = (
    "describe may report a relation or completeness receipt as CURRENT when the "
    "retained TaskView execution for that object succeeded against its current "
    "semantic inputs."
)

RELIANCE_SECTION = """Reliance semantics (permission, not an instruction):
CURRENT means consistent with the current retained TaskView semantic inputs.
A valid COMPLETE over U receipt licenses controlled negative inference only inside U.
These guarantees concern coarse TaskView semantic state.
They do not establish local implementation behavior and do not remove the need for source inspection where exact local behavior or citations are required.
This contract does not claim freshness of external grounding evidence.
Source inspection remains available. Do not treat this text as an instruction to avoid verification or repository reads."""

FRESHNESS_SECTION = """Grounding freshness (factual definition only):
Assertions grounded in participant-visible source evidence may carry a grounding receipt with grounding_state FRESH, CHANGED, or UNKNOWN.
FRESH: the current source-file digest equals the digest recorded at grounding time.
CHANGED: the current source-file digest differs from the digest recorded at grounding time.
UNKNOWN: the source cannot be compared (missing file, missing digest, or non-source grounding).
A source mutation can change grounding metadata. It does not itself add, retract, or reinterpret a semantic assertion.
Derived relation state is logically separate from upstream grounding validity.
This definition does not tell you how strongly to rely on the signal."""

CONJUNCTION_SECTION = """Bounded reuse of a coarse semantic commitment is justified only to the extent that, when those properties are applicable:
internal TaskView state is CURRENT,
the required completeness receipt is valid,
and relevant grounding is FRESH.
This remains permission, not an instruction.
Source inspection remains available and is required where the task needs local implementation evidence."""


def vocabulary_lines(surface: ExperimentTaskViewSurface) -> list[str]:
    description = surface.view.describe()
    lines = [
        f"task_view={description['view']['view_id']}",
        VOCABULARY_HEADER,
        CURRENT_EXISTING,
    ]
    for relation in sorted(description["relations"], key=lambda item: item["name"]):
        roles = ", ".join(
            f"{role['name']}:{role['type']}->{role['column']}" for role in relation["roles"]
        )
        lines.append(f"{relation['name']}({roles})")
        lines.append(f"  {relation['description']}")
        if relation["mode"] == "DERIVED":
            inputs = ",".join(relation["derivation"]["inputs"])
            lines.append(f"  DERIVED inputs={inputs}")
        else:
            lines.append("  BASE")
    return lines


def experimental_sections(condition: str) -> list[str]:
    if condition not in TASKVIEW_CONDITIONS:
        return []
    sections: list[str] = []
    if condition in {"T10", "T11"}:
        sections.append(RELIANCE_SECTION)
    if condition in {"T01", "T11"}:
        sections.append(FRESHNESS_SECTION)
    if condition == "T11":
        sections.append(CONJUNCTION_SECTION)
    return sections


def stable_contract_text(surface: ExperimentTaskViewSurface, condition: str) -> str:
    lines = vocabulary_lines(surface)
    lines.extend(experimental_sections(condition))
    return "\n".join(lines) + "\n"


def contract_fingerprint_parts(condition: str) -> dict[str, Any]:
    return {
        "condition": condition,
        "has_reliance": condition in {"T10", "T11"},
        "has_freshness": condition in {"T01", "T11"},
        "has_conjunction": condition == "T11",
        "reliance_section": RELIANCE_SECTION if condition in {"T10", "T11"} else "",
        "freshness_section": FRESHNESS_SECTION if condition in {"T01", "T11"} else "",
        "conjunction_section": CONJUNCTION_SECTION if condition == "T11" else "",
    }
