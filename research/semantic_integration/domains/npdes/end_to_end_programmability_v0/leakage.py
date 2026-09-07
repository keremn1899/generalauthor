"""Consumer semantic-leakage audit. Relation names are not leakage."""

from __future__ import annotations

import re
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import CONSUMERS

PATTERNS = {
    "native_csv_filename": re.compile(r"dmr_measurements\.csv|permit_limits\.csv", re.I),
    "native_pdf_or_txt": re.compile(r"final_permit\.txt|fact_sheet\.txt|\.pdf", re.I),
    "native_source_path": re.compile(r"participant_sources|permit_text|documents/", re.I),
    "comment_literal": re.compile(r"WHEN DISCHARGING", re.I),
    "nodi_legend": re.compile(
        r"NODI.{0,40}(no discharge|closed|inundat|means )|\{['\"]C['\"]\s*:",
        re.I,
    ),
    "comment_parse": re.compile(r"DMR_COMMENT_TEXT|dmr_comment_text", re.I),
}


def audit_consumers() -> dict:
    files = [
        CONSUMERS / "sql" / "monitoring_analysis.sql",
        CONSUMERS / "python" / "monitoring_analysis.py",
    ]
    hits: dict[str, list[dict]] = {key: [] for key in PATTERNS}
    native_logic_lines = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for key, pattern in PATTERNS.items():
                if pattern.search(line):
                    # SQL/Python comments that forbid these things are not leakage.
                    stripped = line.strip()
                    if stripped.startswith("--") or stripped.startswith("#"):
                        continue
                    hits[key].append({"file": str(path.name), "line": i, "text": line.strip()[:200]})
                    native_logic_lines += 1
    n_hits = sum(len(v) for v in hits.values())
    if n_hits == 0:
        label = "NONE"
    elif n_hits <= 2 and not hits["nodi_legend"] and not hits["comment_literal"]:
        label = "LOW"
    else:
        label = "MATERIAL"
    return {
        "consumer_semantic_leakage": label,
        "native_logic_line_hits": native_logic_lines,
        "hits": hits,
    }
