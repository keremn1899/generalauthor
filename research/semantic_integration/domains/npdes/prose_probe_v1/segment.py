"""Mechanical page/section segmentation of participant permit prose. No semantic summary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_integration.domains.npdes.prose_probe_v1.paths import CORPUS, FROZEN


def split_pages(text: str) -> list[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    pages = raw.split("\f")
    if pages and pages[-1].strip() == "":
        pages = pages[:-1]
    return pages


def infer_section(page_text: str) -> str:
    head = page_text[:800].upper()
    if "FACT SHEET" in head:
        return "fact_sheet"
    if "STATEMENT OF BASIS" in head:
        return "statement_of_basis"
    if "PART I" in head or "PAGE 1 OF PART I" in head or "PAGE 2 OF PART I" in head:
        return "part_i"
    if "PART II" in head:
        return "part_ii"
    if "PART III" in head:
        return "part_iii"
    if "PART IV" in head or "SEWAGE SLUDGE" in head:
        return "part_iv"
    if "AUTHORIZATION TO DISCHARGE" in head:
        return "cover"
    if "INTENTIONALLY LEFT BLANK" in head or "INTENTIONALLY LEFT BLANK" in page_text.upper():
        return "blank"
    return "body"


def load_documents() -> list[dict]:
    docs = []
    for path in sorted(CORPUS.rglob("*.txt")):
        rel = path.relative_to(CORPUS).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        pages = split_pages(text)
        docs.append({"document": rel, "path": path, "pages": pages})
    return docs


def build_segments() -> list[dict]:
    """One segment per PDF page. Same segmentation in every B3 replicate."""
    segments = []
    for doc in load_documents():
        for i, page in enumerate(doc["pages"], start=1):
            section = infer_section(page)
            seg_id = f"{doc['document']}#p{i}"
            segments.append(
                {
                    "segment_id": seg_id,
                    "document": doc["document"],
                    "page": i,
                    "section": section,
                    "n_chars": len(page),
                    "sha256": hashlib.sha256(page.encode("utf-8")).hexdigest(),
                    "text": page,
                }
            )
    return segments


def write_segmentation() -> Path:
    FROZEN.mkdir(parents=True, exist_ok=True)
    segments = build_segments()
    slim = [{k: v for k, v in s.items() if k != "text"} for s in segments]
    payload = {
        "unit": "pdf_page",
        "n_segments": len(segments),
        "documents": sorted({s["document"] for s in segments}),
        "segments": slim,
    }
    path = FROZEN / "segmentation.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    texts = FROZEN / "segmentation_pages.json"
    texts.write_text(json.dumps(segments, indent=2) + "\n", encoding="utf-8")
    return path


def page_text(document: str, page: int) -> str:
    path = CORPUS / document
    pages = split_pages(path.read_text(encoding="utf-8", errors="replace"))
    return pages[page - 1]


def _collapse_ws(text: str) -> str:
    return " ".join(text.split())


def find_span(document: str, needle: str) -> dict:
    path = CORPUS / document
    pages = split_pages(path.read_text(encoding="utf-8", errors="replace"))
    for i, page in enumerate(pages, start=1):
        idx = page.find(needle)
        if idx >= 0:
            return {
                "document": document,
                "page": i,
                "section": infer_section(page),
                "start": idx,
                "exact_span": page[idx : idx + len(needle)],
            }
        collapsed_page = _collapse_ws(page)
        collapsed_needle = _collapse_ws(needle)
        cidx = collapsed_page.find(collapsed_needle)
        if cidx >= 0:
            # recover a contiguous original excerpt containing the first/last tokens
            tokens = collapsed_needle.split()
            first, last = tokens[0], tokens[-1]
            start = page.find(first)
            end = page.rfind(last)
            if start >= 0 and end >= start:
                excerpt = page[start : end + len(last)]
                return {
                    "document": document,
                    "page": i,
                    "section": infer_section(page),
                    "start": start,
                    "exact_span": excerpt,
                }
    raise ValueError(f"needle not found in {document}: {needle[:80]!r}")
