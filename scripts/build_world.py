"""Build a World IR file the read-side explorer can open.

A World the explorer can render is not what the compiler alone produces. It is
four things on disk:

    bomS1.sqlite                    TaskView: referents, relations, tuples
    bomS1.sqlite.origins.json       MECHANICAL / SEMANTIC per assertion
    bomS1.demand.json               the purpose and what it leaves unresolved
    bomS1.demand.json.sha256

The origins sidecar is the part that is easy to miss. `compile_c1` records
`DERIVED` in `_tv_assertions.origin` for computed relations and *nothing at all*
for the rest, so a freshly compiled world raises `OriginMetadataError` on the
first `origin_account()` and cannot tell a mechanical tuple from an authored
one. Construction origin is one of the two things the canvas encodes — a filled
chip is a semantic assertion, a knockout is mechanical — so a world without the
backfill cannot be drawn correctly, only drawn.

Nothing here re-implements construction. S1 goes through the sealed
`construct_experimental_world`, which is the same path the world-programming
benchmark used, so the world the UI opens is the world that experiment measured.
The larger scales reuse the same compiler over the scaling fixtures; they carry
no semantic assertions, because the frozen C2 adjudications exist only for S1's
two packets. That makes S1 the demo world and S10/S100 performance fixtures, and
the summary printed at the end says so rather than leaving it to be discovered.

    uv run --extra all python scripts/build_world.py
    uv run --extra all python scripts/build_world.py --scale S1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.core.kernel import SemanticWorld  # noqa: E402
from research.semantic_integration.domains.bom.compiler import compile_c1  # noqa: E402
from research.semantic_integration.domains.bom.operational_frontier.generate import (  # noqa: E402
    freeze_operational_frontier,
)

# `_backfill_mechanical_origins` is imported rather than copied on purpose. It is
# the only code that decides what MECHANICAL means, and a second copy of that
# decision is exactly how an origin account drifts from the world it describes.
from research.semantic_integration.domains.bom.world_programming.construct import (  # noqa: E402
    _backfill_mechanical_origins,
    construct_experimental_world,
)

SCALES = REPO / "research" / "taskview_bom_scaling" / "scales"
DEFAULT_OUT = REPO / "data" / "worlds"

#: S1 is built by the sealed research path, which compiles the `taskview_bom`
#: fixture rather than `scales/S1`, and then inserts the frozen C2 acceptances.
SEMANTIC_SCALE = "S1"
SCALE_IDS = ("S1", "S10", "S100")


@dataclass(frozen=True)
class BuiltWorld:
    scale: str
    path: Path
    compile_seconds: float
    relations: int
    referents: int
    assertions: int
    origins: dict[str, int]
    obligations: int
    demanded: int


def _clear(path: Path) -> None:
    """Remove a world and every sidecar that would otherwise outlive it.

    A stale `.origins.json` beside a rebuilt database is worse than no origins:
    the ids no longer match, so assertions silently resolve to the wrong
    construction origin instead of failing.
    """
    for candidate in (
        path,
        Path(str(path) + "-journal"),
        Path(str(path) + ".origins.json"),
        path.with_suffix(".demand.json"),
        path.with_suffix(".demand.json.sha256"),
    ):
        if candidate.exists():
            candidate.unlink()


def build(scale: str, out_dir: Path) -> BuiltWorld:
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / f"bom{scale}.sqlite"
    _clear(db_path)

    started = time.perf_counter()
    if scale == SEMANTIC_SCALE:
        experimental = construct_experimental_world(db_path)
        world = experimental.world
        demanded = len(experimental.demanded)
    else:
        compilation = compile_c1(db_path, source_dir=SCALES / scale)
        world = SemanticWorld.wrap(
            compilation.view, world_id=f"bom-world-{scale.lower()}"
        )
        _backfill_mechanical_origins(world)
        demanded = 0
    compile_seconds = time.perf_counter() - started

    view = world.taskview
    document = freeze_operational_frontier(view, db_path.with_suffix(".demand.json"))
    if scale != SEMANTIC_SCALE:
        demanded = document["candidate_case_count"]

    described = view.describe()
    built = BuiltWorld(
        scale=scale,
        path=db_path,
        compile_seconds=compile_seconds,
        relations=len(described["relations"]),
        referents=view.query("SELECT COUNT(*) AS c FROM _tv_referents")[0]["c"],
        assertions=view.query("SELECT COUNT(*) AS c FROM _tv_assertions")[0]["c"],
        origins=world.origin_account(),
        obligations=document["obligation_count"],
        demanded=demanded,
    )
    # Closing is what writes the origins sidecar. A world left open has correct
    # origins in memory and none on disk, which is the failure this whole
    # script exists to prevent.
    world.close()
    return built


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scale",
        action="append",
        choices=SCALE_IDS,
        help="scale to build; repeatable. Default: all.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    scales = args.scale or list(SCALE_IDS)
    for scale in scales:
        built = build(scale, args.out)
        origins = ", ".join(
            f"{name.lower()} {count}" for name, count in sorted(built.origins.items())
        )
        print(
            f"{built.scale:5s} {built.path.name:18s} "
            f"{built.compile_seconds:7.1f}s  "
            f"{built.relations:3d} relations  "
            f"{built.referents:5d} referents  "
            f"{built.assertions:6d} assertions"
        )
        print(f"      origins: {origins}")
        print(
            f"      demand: {built.demanded} demanded cases, "
            f"{built.obligations} unresolved"
        )
        if built.origins.get("SEMANTIC", 0) == 0:
            print("      (no semantic assertions — performance fixture only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
