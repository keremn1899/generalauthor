"""Fresh-agent prompt. No gold, no sources, no construction.py."""

PASS_TASK = """You are a fresh analyst. You did not construct this World.

You have:
- compact_header.md (PURPOSE, WORLD CONTRACT, READ RULES, REVISION)
- accepted/world.sqlite (read-only compiled World)
- ordinary sqlite3 and Python 3

There are no native source CSVs, PDFs, or permit-package documents in this workspace.
Do not look for them. Do not invent NODI code meanings from value frequencies.
Unresolved is not false. A missing tuple is not an established negative.

Write ANSWERS.md answering all three questions. Use SQL against accepted/world.sqlite.
Cite relation names. Distinguish established from unresolved.

# Q1 — Determinacy

Which FY2025 monitoring/compliance cases remain indeterminate, and what unresolved prerequisite prevents a determination?

# Q2 — Numeric result separation

Separate cases with mechanically computable numeric comparison results from cases where an exceedance determination cannot yet be made.

# Q3 — Semantic sharpening

Identify cases whose uncertainty is now about whether discharge occurred, rather than about what the monitoring condition means.

If the World does not represent discharge-conditioned monitoring that way, say so from the World — do not reconstruct it from native sources.
"""

FIRST_PROMPT = (
    "Read compact_header.md and PASS_TASK.md. Query accepted/world.sqlite with sqlite3 or Python. "
    "Write ANSWERS.md covering Q1, Q2, and Q3. Do not invent NODI meanings. "
    "Do not search for CSV/PDF sources. Stop when ANSWERS.md is complete."
)
