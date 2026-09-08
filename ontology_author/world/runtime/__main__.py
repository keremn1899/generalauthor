"""Low-level runtime primitive: create or rebuild one World workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .entry import create, rebuild


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="World construction primitive")
    parser.add_argument("command", choices=("create", "rebuild"))
    parser.add_argument("workspace", nargs="?", default=".")
    args = parser.parse_args(argv)
    workspace = Path(args.workspace).resolve()
    if args.command == "create":
        print(create(workspace))
        return 0
    result = rebuild(workspace)
    print(json.dumps({"succeeded": result.succeeded, "reason": result.reason, "errors": list(result.errors)}))
    return 0 if result.succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
