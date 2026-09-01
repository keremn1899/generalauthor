"""T10-style contract plus matched initial representation delivery."""

from __future__ import annotations

from research.taskview_orientation.bounded_reliance.contracts import (
    RELIANCE_SECTION,
    vocabulary_lines,
)
from research.taskview_orientation.compiled_projection.projection import presentation_for
from research.taskview_orientation.surface import ExperimentTaskViewSurface


DELIVERY_PREFACE = """Coarse task-conditioned state currently retained in TaskView.
This block is a deterministic presentation of existing TaskView relations and completeness metadata.
Named relations, SQL, describe, assertion, and rerun remain available.
describe(relation="migration_surface") returns this presentation recomputed from current canonical state after assertion or rerun."""


FORBIDDEN_INSTRUCTION_NEEDLES = (
    "trust TaskView",
    "minimize queries",
    "avoid rechecking",
    "prefer the compiled",
    "should be cheaper",
    "semantic reassembly",
)


def stable_contract_text(surface: ExperimentTaskViewSurface) -> str:
    lines = vocabulary_lines(surface)
    lines.append(RELIANCE_SECTION)
    return "\n".join(lines) + "\n"


def system_prompt_suffix(surface: ExperimentTaskViewSurface, condition: str) -> str:
    body = presentation_for(condition, surface)
    text = stable_contract_text(surface) + "\n" + DELIVERY_PREFACE + "\n\n" + body
    lowered = text.lower()
    for needle in FORBIDDEN_INSTRUCTION_NEEDLES:
        if needle.lower() in lowered:
            raise RuntimeError(f"delivery text contains forbidden instruction: {needle}")
    return text


def initial_delivery_bytes(surface: ExperimentTaskViewSurface, condition: str) -> int:
    return len(presentation_for(condition, surface).encode("utf-8"))
