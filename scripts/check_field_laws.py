#!/usr/bin/env python3
"""Refuse a hand-rolled duration where the spine has a value for it.

The design language of the live surfaces is two laws, and both are code:
`styles/motion.ts` is gravity — emit, absorb, settle, flow, hold, with their
real durations and analytically derived curves — and `styles/light.ts` is
illumination, falling off through the graph from whatever a person acted on.

Neither is enforceable by a document, because a document is a *second*
statement of something and the second one drifts. What is enforceable is the
absence of a first: if no stylesheet on a live surface ever writes a duration
of its own, the spine is the only place a duration exists, and the reference
cannot go stale because there is nothing to disagree with.

So this is not a style check. It is what makes "the transitions are the spine"
a fact about the repository rather than a claim in a markdown file.

    uv run python scripts/check_field_laws.py

Prints nothing and exits 0 when clean; prints file:line and exits 1 otherwise.

Scope is the live World IR surfaces. `product/` and `explorations/` are the
frozen lineage and the workbench, which predate the spine and are not being
brought onto it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SURFACES = [
    REPO / "frontend/src/world",
    REPO / "frontend/src/construction",
    REPO / "frontend/src/styles",
]

# A `transition` / `animation` / `*-duration` / `*-delay` declaration, wherever
# it sits — the rule has to hold for `.x { transition: opacity 240ms; }` on one
# line as much as for a declaration spread over five.
DECLARATION = re.compile(
    r"(?:transition|animation)(?:-duration|-delay)?\s*:[^;{}]*",
    re.IGNORECASE,
)
LITERAL_TIME = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)(ms|s)(?![\w-])")

# A literal inside `var(--motion-…, 280ms)` is the fallback for the spine's own
# value, which is the one place a number is allowed to be written twice: CSS
# needs it when the variable has not reached the element yet.
FALLBACK = re.compile(r"var\(\s*--[a-z-]+\s*,[^)]*\)", re.IGNORECASE)

COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

ALLOW = "field-laws: allow"

# How far back an exception may sit. A declaration's reason is normally the
# comment directly above it, which is where a reader looks for it.
ALLOW_REACH = 6


def offences(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    allowed_after = {
        index
        for index, line in enumerate(lines, start=1)
        if ALLOW in line
    }

    found: list[tuple[int, str]] = []
    for match in DECLARATION.finditer(COMMENT.sub(lambda m: " " * len(m.group(0)), text)):
        declaration = match.group(0)
        number = text.count("\n", 0, match.start()) + 1
        # The exception may be on the declaration, or in the comment above it.
        if any(number - reach in allowed_after for reach in range(0, ALLOW_REACH)):
            continue
        # Zero is not a duration, it is the absence of one — `visibility 0s`.
        stripped = FALLBACK.sub(" ", declaration)
        times = [
            f"{value}{unit}"
            for value, unit in LITERAL_TIME.findall(stripped)
            if float(value) != 0
        ]
        if times:
            flat = " ".join(declaration.split())
            found.append((number, f"{', '.join(times)} in `{flat}`"))
    return found


def main() -> int:
    problems: list[str] = []
    for surface in SURFACES:
        for path in sorted(surface.rglob("*.css")):
            for number, detail in offences(path):
                problems.append(f"{path.relative_to(REPO)}:{number}: {detail}")

    if not problems:
        return 0

    print("A duration written by hand where the spine has one.\n")
    for problem in problems:
        print(f"  {problem}")
    print(
        "\nUse var(--motion-<intent>-duration) and var(--motion-<intent>-curve).\n"
        "The five intents and what causes each are in styles/transition_map.md §1.\n"
        f"A deliberate exception carries `/* {ALLOW}: <reason> */` on the declaration."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
