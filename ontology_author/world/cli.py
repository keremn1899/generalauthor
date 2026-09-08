"""Public command line for project-local Worlds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runtime import entry
from .server import open_world
from .workspaces import WorldSelectionError, discover, project_root, select, world_ref


def _attach_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")


def _merge_agents(path: Path, body: str) -> None:
    start = "<!-- ontology-author:start -->"
    end = "<!-- ontology-author:end -->"
    block = f"{start}\n{body.rstrip()}\n{end}"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if start in existing and end in existing:
        before = existing.split(start, 1)[0].rstrip()
        after = existing.split(end, 1)[1].lstrip()
        output = "\n\n".join(part for part in (before, block, after) if part) + "\n"
    else:
        output = existing.rstrip() + ("\n\n" if existing.strip() else "") + block + "\n"
    if output != existing:
        path.write_text(output, encoding="utf-8")


def attach(project: Path, clients: list[str]) -> dict[str, object]:
    from importlib.resources import files

    canonical = files("ontology_author.world").joinpath("CAPABILITY.md").read_text(encoding="utf-8")
    selected = {"cursor", "codex", "claude"} if "all" in clients else set(clients)
    attached: list[str] = []
    cursor = "---\ndescription: Use project-local Worlds for conversational semantic construction and inspection\nglobs:\nalwaysApply: true\n---\n\n" + canonical
    claude = "---\nname: ontology-author\ndescription: Construct, maintain, query, and inspect project-local Worlds\n---\n\n" + canonical
    if "cursor" in selected:
        _attach_file(project / ".cursor" / "rules" / "ontology-author.mdc", cursor)
        attached.append("cursor")
    if "claude" in selected:
        _attach_file(project / ".claude" / "skills" / "ontology-author" / "SKILL.md", claude)
        attached.append("claude")
    if "codex" in selected:
        skill = project / ".codex" / "skills" / "ontology-author" / "SKILL.md"
        _attach_file(skill, canonical)
        _merge_agents(
            project / "AGENTS.md",
            "When working on Worlds, read and follow `.codex/skills/ontology-author/SKILL.md`.",
        )
        attached.append("codex")
    return {"project": str(project), "attached": attached, "files": [
        str(project / ".cursor" / "rules" / "ontology-author.mdc") if "cursor" in selected else None,
        str(project / ".claude" / "skills" / "ontology-author" / "SKILL.md") if "claude" in selected else None,
        str(project / ".codex" / "skills" / "ontology-author" / "SKILL.md") if "codex" in selected else None,
    ]}


def _workspace(args: argparse.Namespace):
    return world_ref(args.project, args.world)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="author", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create a World authoring workspace")
    create.add_argument("world", nargs="?", default="world")
    create.add_argument("--project", type=Path, default=Path("."))

    rebuild = commands.add_parser("rebuild", help="construct and rebuild one World")
    rebuild.add_argument("world")
    rebuild.add_argument("--project", type=Path, default=Path("."))

    listing = commands.add_parser("list", help="list project-local Worlds")
    listing.add_argument("--project", type=Path, default=Path("."))

    attach_parser = commands.add_parser("attach", help="attach World instructions to a coding-agent harness")
    attach_parser.add_argument("client", nargs="?", choices=("cursor", "codex", "claude", "all"))
    attach_parser.add_argument("--client", action="append", choices=("cursor", "codex", "claude", "all"), dest="clients")
    attach_parser.add_argument("--project", type=Path, default=Path("."))

    opener = commands.add_parser("open", help="open the bundled read-only World inspector")
    opener.add_argument("world", nargs="?")
    opener.add_argument("--project", type=Path, default=Path("."))
    opener.add_argument("--no-browser", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            ref = _workspace(args)
            path = entry.create(ref.path)
            print(json.dumps({"world": ref.name, "workspace": str(path), "purpose": str(path / "PURPOSE.md")}))
            return 0
        if args.command == "rebuild":
            ref = _workspace(args)
            result = entry.rebuild(ref.path)
            print(json.dumps({"world": ref.name, "succeeded": result.succeeded, "reason": result.reason, "errors": list(result.errors)}))
            return 0 if result.succeeded else 1
        if args.command == "list":
            print(json.dumps([{"name": item.name, "path": str(item.path)} for item in discover(args.project)], indent=2))
            return 0
        if args.command == "attach":
            clients = args.clients or ([args.client] if args.client else ["cursor"])
            print(json.dumps(attach(project_root(args.project), clients), indent=2))
            return 0
        if args.command == "open":
            ref = select(args.project, args.world)
            if args.no_browser:
                print(json.dumps({"world": ref.name, "path": str(ref.world)}))
                return 0
            open_world(ref.world)
            return 0
    except (FileNotFoundError, ValueError, WorldSelectionError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
