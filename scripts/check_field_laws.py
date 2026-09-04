#!/usr/bin/env python3
"""Refuse a hand-rolled value where a module already has one.

The design language of the live surfaces is code, not documentation.
`styles/motion.ts` is gravity — emit, absorb, settle, flow, hold, with their
real durations and analytically derived curves. `styles/light.ts` is
illumination, falling off through the graph from whatever a person acted on.
`styles/type.ts` is the type scale — five steps, because before it there were
seventeen sizes and nobody had chosen any of them.

Neither is enforceable by a document, because a document is a *second*
statement of something and the second one drifts. What is enforceable is the
absence of a first: if no stylesheet on a live surface ever writes a duration
or a font size of its own, the modules are the only place those values exist,
and the reference cannot go stale because there is nothing to disagree with.

So this is not a style check. It is what makes "the transitions are the spine"
and "the type is the scale" facts about the repository rather than claims in a
markdown file.

    uv run python scripts/check_field_laws.py

Prints nothing and exits 0 when clean; prints file:line and exits 1 otherwise.

Scope is the live World IR surfaces, plus the handful of `product/`
stylesheets those surfaces import — see `SHARED`. The rest of `product/` and
all of `explorations/` are the frozen lineage and the workbench, which predate
the spine and are not being brought onto it.
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

# Four stylesheets that live in the frozen lineage and dress a live surface.
#
# `product/` as a whole is out of scope — see the note below — but these four
# are imported by `WorldPage` and `WorldLabPage`, so the reader's heading, the
# finder and the whole instrument band are wearing them. A file cannot be
# half-governed: whatever laws the World surface is held to, the stylesheets it
# is actually painted with are held to as well. The rest of `product/` keeps
# its own type, because changing it would be changing the frozen product for
# no live surface's benefit.
SHARED = [
    REPO / "frontend/src/product/ProductShell.css",
    REPO / "frontend/src/product/NodeFinder.css",
    REPO / "frontend/src/product/NodeReaderPanel.css",
    REPO / "frontend/src/product/GraphWorkspace.css",
    REPO / "frontend/src/product/OverlayPanel.css",
    REPO / "frontend/src/product/overlayChrome.css",
]

# A `transition` / `animation` / `*-duration` / `*-delay` declaration, wherever
# it sits — the rule has to hold for `.x { transition: opacity 240ms; }` on one
# line as much as for a declaration spread over five.
DECLARATION = re.compile(
    r"(?:transition|animation)(?:-duration|-delay)?\s*:[^;{}]*",
    re.IGNORECASE,
)
LITERAL_TIME = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)(ms|s)(?![\w-])")

# A `font-size` written as a length rather than read from the scale. `em` and
# `%` are relative to the inherited size, so they compose with a step instead
# of replacing it — a `0.9em` sub-label still moves when its step does. `rem`
# and `px` do not, and they are what produced the seventeen.
FONT_SIZE = re.compile(r"font-size\s*:[^;{}]*", re.IGNORECASE)
LITERAL_SIZE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)(rem|px)(?![\w-])")

# A literal inside `var(--motion-…, 280ms)` is the fallback for the spine's own
# value, which is the one place a number is allowed to be written twice: CSS
# needs it when the variable has not reached the element yet.
FALLBACK = re.compile(r"var\(\s*--[a-z-]+\s*,[^)]*\)", re.IGNORECASE)

COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

ALLOW = "field-laws: allow"

# How far back an exception may sit. A declaration's reason is normally the
# comment directly above it, which is where a reader looks for it.
ALLOW_REACH = 6

MOTION_USE = "use var(--motion-<intent>-duration) / -curve"
TYPE_USE = "use var(--type-<step>); the five steps are in styles/type.ts"


def offences(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    allowed_after = {
        index
        for index, line in enumerate(lines, start=1)
        if ALLOW in line
    }

    blanked = COMMENT.sub(lambda m: " " * len(m.group(0)), text)

    def scan(
        declarations: re.Pattern[str],
        literals: re.Pattern[str],
        use: str,
    ) -> list[tuple[int, str]]:
        out: list[tuple[int, str]] = []
        for match in declarations.finditer(blanked):
            declaration = match.group(0)
            number = text.count("\n", 0, match.start()) + 1
            # The exception may be on the declaration, or in the comment above.
            if any(number - reach in allowed_after for reach in range(0, ALLOW_REACH)):
                continue
            # Zero is not a value, it is the absence of one — `visibility 0s`.
            stripped = FALLBACK.sub(" ", declaration)
            values = [
                f"{value}{unit}"
                for value, unit in literals.findall(stripped)
                if float(value) != 0
            ]
            if values:
                flat = " ".join(declaration.split())
                out.append((number, f"{', '.join(values)} in `{flat}` — {use}"))
        return out

    found = scan(DECLARATION, LITERAL_TIME, MOTION_USE)
    found += scan(FONT_SIZE, LITERAL_SIZE, TYPE_USE)
    return sorted(found)


def main() -> int:
    problems: list[str] = []
    paths = [path for surface in SURFACES for path in sorted(surface.rglob("*.css"))]
    paths += [path for path in SHARED if path.exists()]
    for path in paths:
        for number, detail in offences(path):
            problems.append(f"{path.relative_to(REPO)}:{number}: {detail}")

    if not problems:
        return 0

    print("A value written by hand where a module already has one.\n")
    for problem in problems:
        print(f"  {problem}")
    print(
        "\nThe five motion intents and what causes each are in\n"
        "styles/transition_map.md §1; the five type steps are in styles/type.ts.\n"
        f"A deliberate exception carries `/* {ALLOW}: <reason> */` above the declaration."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
