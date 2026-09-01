"""Serve one compiled World on loopback for the explorer front end.

    uv run --extra all python scripts/run_world_explorer.py
    uv run --extra all python scripts/run_world_explorer.py --world data/worlds/bomS100.sqlite

Pairs with the Vite dev server, which proxies `/world` here. The default token
matches the local product's existing habit so a browser can carry
`?apiToken=devtoken` and nothing else has to be arranged.
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
    args = parser.parse_args()

    if not args.world.exists():
        parser.error(
            f"{args.world} does not exist — build it with scripts/build_world.py"
        )
    print(f"world explorer: {args.world.name} on http://{args.host}:{args.port}/world")
    serve(args.world, host=args.host, port=args.port, token=args.token or None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
