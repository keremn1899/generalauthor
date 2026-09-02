"""Serve one compiled World on loopback for the explorer front end.

    uv run --extra all python scripts/run_world_explorer.py
    uv run --extra all python scripts/run_world_explorer.py --world data/worlds/bomS100.sqlite

    uv run --extra all python scripts/run_world_explorer.py \
        --construction research/.../constructor_v2/axis_d/trials/T1

Pairs with the Vite dev server, which proxies `/world` here. The default token
matches the local product's existing habit so a browser can carry
`?apiToken=devtoken` and nothing else has to be arranged.

`--construction` names one frozen constructor run — a trial directory holding
`passes/p0` … `passes/p8` — and opens the `/construction` plane over it. It is
optional and read-only; without it those routes answer 404 and the world plane
is unaffected. There is no default, because a run belongs to a campaign in
`research/` and guessing which one someone means is worse than asking.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from world_explorer.http import serve  # noqa: E402

DEFAULT_WORLD = REPO / "data" / "worlds" / "bomS1.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, default=DEFAULT_WORLD)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8139)
    parser.add_argument("--token", default="devtoken")
    parser.add_argument("--construction", type=Path, default=None)
    args = parser.parse_args()

    if not args.world.exists():
        parser.error(
            f"{args.world} does not exist — build it with scripts/build_world.py"
        )
    if args.construction and not (args.construction / "passes").is_dir():
        parser.error(f"{args.construction} holds no passes/ directory")
    print(f"world explorer: {args.world.name} on http://{args.host}:{args.port}/world")
    if args.construction:
        print(f"construction:   {args.construction} on /construction")
    serve(
        args.world,
        host=args.host,
        port=args.port,
        token=args.token or None,
        construction=args.construction,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
