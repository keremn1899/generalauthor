"""Structured-answer validation and field-level frozen oracle scoring."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import FROZEN_ROOT


PROMPTS_PATH = FROZEN_ROOT / "prompts.json"
ORACLE_PATH = FROZEN_ROOT / "oracle.json"


def load_prompts() -> dict[str, Any]:
    return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))


def load_oracle() -> dict[str, Any]:
    return json.loads(ORACLE_PATH.read_text(encoding="utf-8"))


def validate_answer(
    *, phase: int, answer: dict[str, Any], source_root: Path
) -> None:
    prompt = load_prompts()["phases"][phase - 1]
    expected = set(prompt["answer_fields"])
    actual = set(answer)
    if actual != expected:
        raise ValueError(
            f"phase {phase} answer fields differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    citations = answer["citations"]
    if not isinstance(citations, list) or not citations:
        raise ValueError(f"phase {phase} requires at least one citation")
    for citation in citations:
        if set(citation) != {"path", "start_line", "end_line"}:
            raise ValueError(f"invalid phase {phase} citation shape: {citation!r}")
        source = (source_root / citation["path"]).resolve()
        if not source.is_relative_to(source_root.resolve()) or not source.is_file():
            raise ValueError(f"citation is not participant-visible: {citation!r}")
        line_count = len(source.read_text(encoding="utf-8").splitlines())
        if not 1 <= citation["start_line"] <= citation["end_line"] <= line_count:
            raise ValueError(f"citation span does not resolve: {citation!r}")


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip()).casefold()
    if isinstance(value, list):
        return sorted((_normalize(item) for item in value), key=repr)
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in sorted(value.items())}
    return value


def _citation_support(answer: dict[str, Any], witnesses: list[list[Any]]) -> bool:
    for witness_path, witness_start, witness_end in witnesses:
        if not any(
            citation["path"] == witness_path
            and citation["start_line"] <= witness_end
            and citation["end_line"] >= witness_start
            for citation in answer["citations"]
        ):
            return False
    return True


def score_answer(phase: int, answer: dict[str, Any]) -> dict[str, Any]:
    """Score every non-citation field independently against the frozen oracle."""

    expected = load_oracle()["phases"][str(phase)]
    field_scores = {}
    for field, expected_value in expected.items():
        if field == "citation_witnesses":
            continue
        field_scores[field] = _normalize(answer[field]) == _normalize(expected_value)
    field_scores["citations"] = _citation_support(
        answer, expected["citation_witnesses"]
    )
    return {
        "phase": phase,
        "field_scores": field_scores,
        "correct_fields": sum(field_scores.values()),
        "field_count": len(field_scores),
        "all_fields_correct": all(field_scores.values()),
        "adjudication_policy": (
            "Semantically valid non-exact prose or ALTERNATIVE_VALID_LOCAL citations "
            "may be accepted after arm-blinded review; primary span labels never change."
        ),
    }

