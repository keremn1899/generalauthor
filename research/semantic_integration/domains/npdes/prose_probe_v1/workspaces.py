"""Workspaces for isolated probe conditions. Gold cards never enter participant workspaces."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.prose_probe_v1.paths import (
    KERNEL,
    PARTICIPANT,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.prompts import PROMPTS
from research.semantic_integration.domains.npdes.prose_probe_v1.score import load_frozen
from research.semantic_integration.domains.npdes.prose_probe_v1.segment import page_text

PURPOSES = PARTICIPANT / "purposes"


def copy_purposes(dest: Path) -> None:
    d = dest / "purposes"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
        shutil.copy2(PURPOSES / name, d / name)


def write_task(dest: Path, condition: str) -> None:
    (dest / "PASS_TASK.md").write_text(PROMPTS[condition], encoding="utf-8")
    (dest / "README.md").write_text(
        "Isolated NPDES prose probe workspace. Purposes A/B/C only. No gold answers.\n",
        encoding="utf-8",
    )


def adjacent_pages(document: str, page: int) -> str:
    chunks = []
    for p in (page - 1, page, page + 1):
        if p < 1:
            continue
        try:
            chunks.append(f"--- page {p} ---\n{page_text(document, p)}")
        except IndexError:
            continue
    return "\n\n".join(chunks)


def seed_b1(dest: Path, gold_id: str, *, span_only: bool = False) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    pas = load_frozen("passages.json")["positives"][gold_id]
    write_task(dest, "c1" if span_only else "b1")
    lines = [
        f"# Source passage",
        "",
        f"Document: {pas['document'].replace('.txt', '.pdf')}",
    ]
    if pas.get("heading") and not span_only:
        lines.extend(["", f"Section heading: {pas['heading']}"])
    if pas.get("adjacent") and not span_only:
        lines.extend(["", f"Attached context: {pas['adjacent']}"])
    lines.extend(["", "## Target span(s)", ""])
    pages = []
    for span in pas["spans"]:
        pages.append(span["page"])
        lines.extend(
            [
                f"Locator: {span['document'].replace('.txt', '.pdf')} page {span['page']} section {span['section']}",
                "",
                "```",
                span["exact_span"],
                "```",
                "",
            ]
        )
    for span in pas.get("paired_spans") or []:
        lines.extend(
            [
                f"Related document locator: {span['document'].replace('.txt', '.pdf')} page {span['page']}",
                "",
                "```",
                span["exact_span"],
                "```",
                "",
            ]
        )
    if not span_only:
        lines.extend(["", "## Local structural context (adjacent pages of the primary document)", ""])
        primary_page = pages[0] if pages else 1
        lines.append(adjacent_pages(pas["document"], primary_page))
        # footnotes often sit on the same page as the table; include that full page
    (dest / "PASSAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def seed_b3(dest: Path, segment: dict) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    write_task(dest, "b3")
    header = (
        f"Document: {segment['document'].replace('.txt', '.pdf')}\n"
        f"Page: {segment['page']}\n"
        f"Section: {segment['section']}\n"
        f"Segment id: {segment['segment_id']}\n"
    )
    (dest / "SEGMENT.md").write_text(
        header + "\n" + segment["text"] + "\n",
        encoding="utf-8",
    )


def _packet_from_spans(gold_id: str) -> dict:
    pas = load_frozen("passages.json")
    pos = pas["positives"][gold_id]
    observations = []
    for span in pos["spans"] + (pos.get("paired_spans") or []):
        observations.append(
            {
                "source_path": span["document"].replace(".txt", ".pdf"),
                "location": f"page {span['page']} section {span['section']}",
                "excerpt": span["exact_span"],
            }
        )
    # cover dates for time-staged / schedule seams
    if gold_id.startswith("S-FARM"):
        observations.append(
            {
                "source_path": "farmington/final_permit.pdf",
                "location": "cover page",
                "excerpt": "This permit shall become effective on December 1, 2021. This permit and the authorization to discharge shall expire at midnight, November 30, 2026.",
            }
        )
    if gold_id.startswith("S-AZTEC"):
        observations.append(
            {
                "source_path": "aztec/final_permit.pdf",
                "location": "cover page",
                "excerpt": "shall become effective on January 1, 2022. This permit and the authorization to discharge shall expire at midnight, December 31, 2026.",
            }
        )
    if gold_id.startswith("S-GCC"):
        observations.append(
            {
                "source_path": "gcc/final_permit.pdf",
                "location": "cover page",
                "excerpt": "This permit shall become effective on June 1, 2021. This permit and the authorization to discharge shall expire at midnight, May 31, 2026.",
            }
        )
    observations.append(
        {
            "source_path": "purposes/visible_a.md",
            "location": "purpose A period",
            "excerpt": "Federal FY2025 (2024-10-01 through 2025-09-30 inclusive)",
        }
    )
    known_missing = []
    if gold_id == "S-FARM-TRC-CONDITIONAL":
        known_missing.append("No operational chlorine-use log for FY2025 months is in this packet. NODI code legends are not in this packet.")
    if gold_id == "S-AZTEC-WET-SEASONAL":
        known_missing.append("No evidence in this packet that the once-per-term WET test was or was not performed.")
    if gold_id == "S-GCC-EVENT-DISCHARGE":
        known_missing.append("NODI code legends are not in this packet.")
    return {
        "obligation_id": f"oracle:{gold_id}",
        "selected_observations": observations,
        "selection_rationale": "Smallest participant-corpus spans that state the operative clause plus cover dates and the FY2025 window.",
        "known_missing_information": known_missing,
    }


def seed_b2(dest: Path, gold_id: str) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    shutil.copy2(KERNEL, dest / "KERNEL.md")
    write_task(dest, "b2")
    oracle = next(o for o in load_frozen("oracle_obligations.json") if o["gold_id"] == gold_id)
    obligation = {
        "obligation_id": oracle["obligation_id"],
        "relation": oracle["relation"],
        "values": oracle["values"],
        "why_demanded": oracle["question"],
        "required_by": ["A", "B", "C"],
        "current_epistemic_state": "UNRESOLVED",
        "allowed_dispositions": oracle["allowed_dispositions"],
    }
    (dest / "03_obligations.json").write_text(json.dumps([obligation], indent=2) + "\n")
    packet = _packet_from_spans(gold_id)
    packets = dest / "04_packets"
    packets.mkdir()
    (packets / f"{oracle['obligation_id']}.json").write_text(json.dumps(packet, indent=2) + "\n")
    contract = {
        "ORACLE_INTERVENTION": True,
        "note": "Evaluator-provided probe relation contract so P5 understands proposition semantics. Not a World vocabulary change. Do not persist into a compiled World.",
        "name": oracle["relation"],
        "meaning": oracle["relation_meaning"],
        "allowed_dispositions": oracle["allowed_dispositions"],
    }
    (dest / "oracle_relation_contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def seed_b4(dest: Path, candidate: dict, segment: dict | None = None) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    write_task(dest, "b4")
    loc = candidate.get("locator") or ""
    src = candidate.get("source") or (segment or {}).get("document") or ""
    span = candidate.get("exact_span") or ""
    context = ""
    if segment:
        context = segment.get("text") or ""
    lines = [
        "# Source passage (automatically nominated; not gold)",
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
        "## Local structural context",
        "",
        f"Section: {(segment or {}).get('section')}",
        f"Page: {(segment or {}).get('page')}",
        "",
        context,
    ]
    (dest / "PASSAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def seed_b4_p5(dest: Path, obligation: dict, candidate: dict) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copy_purposes(dest)
    shutil.copy2(KERNEL, dest / "KERNEL.md")
    write_task(dest, "b2")
    obl_id = str(obligation.get("obligation_id") or "auto:b4")
    row = {
        "obligation_id": obl_id,
        "relation": obligation.get("relation") or "probe_obligation",
        "values": obligation.get("semantic_arguments") or obligation.get("values") or {},
        "why_demanded": obligation.get("question") or "",
        "required_by": [obligation.get("affected_purpose") or "A"],
        "current_epistemic_state": "UNRESOLVED",
    }
    (dest / "03_obligations.json").write_text(json.dumps([row], indent=2) + "\n")
    packet = {
        "obligation_id": obl_id,
        "selected_observations": [
            {
                "source_path": candidate.get("source"),
                "location": candidate.get("locator"),
                "excerpt": candidate.get("exact_span"),
            }
        ],
        "selection_rationale": "Automatically assembled from the nominated clause plus the obligation text.",
        "known_missing_information": ["Packet is auto-assembled; may be evidence-insufficient."],
    }
    packets = dest / "04_packets"
    packets.mkdir()
    (packets / f"{obl_id}.json").write_text(json.dumps(packet, indent=2) + "\n")
