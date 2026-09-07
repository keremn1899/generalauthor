"""Workspaces for v1.1. Evaluator labels never enter participant workspaces."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.prose_probe_v1.workspaces import (
    adjacent_pages,
    copy_purposes,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.paths import KERNEL
from research.semantic_integration.domains.npdes.prose_probe_v1_1.prompts import PROMPTS


def write_task(dest: Path, condition: str) -> None:
    (dest / "PASS_TASK.md").write_text(PROMPTS[condition], encoding="utf-8")
    (dest / "README.md").write_text(
        "Isolated NPDES prose probe v1.1 workspace. Purposes A/B/C only. No gold answers.\n",
        encoding="utf-8",
    )


def _document_txt(candidate: dict) -> str:
    raw = str(candidate.get("_document") or candidate.get("source") or "")
    return raw.replace(".pdf", ".txt")


def seed_b4_lite(dest: Path, candidate: dict) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    write_task(dest, "b4_lite")
    src = candidate.get("source") or candidate.get("_document") or ""
    loc = candidate.get("locator") or ""
    span = candidate.get("exact_span") or ""
    page = int(candidate.get("_page") or 1)
    document = _document_txt(candidate)
    context = ""
    try:
        context = adjacent_pages(document, page)
    except Exception:
        context = ""
    lines = [
        "# Source passage (automatically nominated)",
        "",
        f"Document: {src}",
        f"Locator: {loc}",
        "",
        "## Target span",
        "",
        "```",
        span,
        "```",
        "",
        "## Local structural context (adjacent pages of the source document)",
        "",
        context,
    ]
    (dest / "PASSAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def seed_p5(dest: Path, obligation: dict, candidate: dict) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    shutil.copy2(KERNEL, dest / "KERNEL.md")
    write_task(dest, "p5")
    obl_id = str(obligation.get("obligation_id") or candidate.get("candidate_id") or "auto:b4lite")
    question = (
        obligation.get("question_or_proposition")
        or obligation.get("question")
        or ""
    )
    required = obligation.get("required_context") or obligation.get("semantic_arguments") or []
    if isinstance(required, str):
        required = [required]
    row = {
        "obligation_id": obl_id,
        "relation": obligation.get("relation") or "probe_obligation",
        "values": required,
        "why_demanded": question,
        "required_by": [obligation.get("affected_purpose") or "A"],
        "current_epistemic_state": "UNRESOLVED",
        "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
    }
    (dest / "03_obligations.json").write_text(json.dumps([row], indent=2) + "\n")
    observations = [
        {
            "source_path": candidate.get("source") or candidate.get("_document"),
            "location": candidate.get("locator"),
            "excerpt": candidate.get("exact_span"),
        }
    ]
    document = _document_txt(candidate)
    page = int(candidate.get("_page") or 1)
    try:
        observations.append(
            {
                "source_path": document.replace(".txt", ".pdf"),
                "location": f"adjacent pages around {page}",
                "excerpt": adjacent_pages(document, page)[:8000],
            }
        )
    except Exception:
        pass
    packet = {
        "obligation_id": obl_id,
        "selected_observations": observations,
        "selection_rationale": "Automatically assembled from the nominated clause plus local structural context used at obligation formation.",
        "known_missing_information": [
            "Packet is auto-assembled from the nominated passage; it may be evidence-insufficient."
        ],
    }
    packets = dest / "04_packets"
    packets.mkdir()
    safe_name = re_sub_id(obl_id)
    (packets / f"{safe_name}.json").write_text(json.dumps(packet, indent=2) + "\n")


def re_sub_id(obl_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in obl_id)
