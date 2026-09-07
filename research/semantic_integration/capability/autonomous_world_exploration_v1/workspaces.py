"""Seed workspaces. GOLD and discovery targets never enter."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.capability.end_to_end_v1.workspaces import seed_runtime
from research.semantic_integration.capability.autonomous_world_exploration_v1.header import ACCESS, render_header
from research.semantic_integration.capability.autonomous_world_exploration_v1.paths import E2E, t1_accepted
from research.semantic_integration.capability.autonomous_world_exploration_v1.prompts import (
    E0_AGENT,
    E1_ORIENT_AGENT,
    E1_TASK_AGENT,
)


def copy_accepted_world(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in (
        "world.sqlite",
        "world.sqlite.origins.json",
        "world.purpose.json",
        "world.admission.json",
    ):
        item = src / name
        if item.exists():
            shutil.copy2(item, dest / name)


def purpose_text(domain_id: str) -> str:
    return (E2E / "domains" / domain_id / "purpose.txt").read_text(encoding="utf-8")


def tasks_markdown(tasks: list[dict]) -> str:
    lines = ["# Downstream tasks", "", "Answer T1–T6 in `answers.json`. Do not invent unsupported facts.", ""]
    for item in tasks:
        lines.append(f"## {item['id']}")
        lines.append("")
        lines.append(item["prompt"])
        lines.append("")
    return "\n".join(lines) + "\n"


def seed_common(dest: Path, *, domain_id: str) -> dict[str, int]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    seed_runtime(dest)
    accepted = t1_accepted(domain_id)
    copy_accepted_world(accepted, dest / "world")
    purpose = purpose_text(domain_id)
    header = render_header(purpose=purpose, world_dir=dest / "world")
    (dest / "HEADER.md").write_text(header, encoding="utf-8")
    (dest / "ACCESS.md").write_text(ACCESS, encoding="utf-8")
    (dest / "README.md").write_text(
        "Compiled World plus compact semantic header. No raw sources. Do not modify the World.\n",
        encoding="utf-8",
    )
    return {
        "header_bytes": len(header.encode("utf-8")),
        "access_bytes": len(ACCESS.encode("utf-8")),
        "purpose_bytes": len(purpose.encode("utf-8")),
    }


def seed_e0(dest: Path, *, domain_id: str, tasks: list[dict]) -> dict[str, int]:
    sizes = seed_common(dest, domain_id=domain_id)
    (dest / "TASKS.md").write_text(tasks_markdown(tasks), encoding="utf-8")
    (dest / "AGENT.md").write_text(E0_AGENT, encoding="utf-8")
    sizes["tasks_bytes"] = (dest / "TASKS.md").stat().st_size
    sizes["agent_bytes"] = (dest / "AGENT.md").stat().st_size
    sizes["initial_context_bytes"] = (
        sizes["header_bytes"] + sizes["access_bytes"] + sizes["tasks_bytes"] + sizes["agent_bytes"]
    )
    return sizes


def seed_e1_orient(dest: Path, *, domain_id: str) -> dict[str, int]:
    sizes = seed_common(dest, domain_id=domain_id)
    (dest / "AGENT.md").write_text(E1_ORIENT_AGENT, encoding="utf-8")
    sizes["agent_bytes"] = (dest / "AGENT.md").stat().st_size
    sizes["initial_context_bytes"] = sizes["header_bytes"] + sizes["access_bytes"] + sizes["agent_bytes"]
    return sizes


def reveal_tasks(dest: Path, *, tasks: list[dict]) -> None:
    (dest / "TASKS.md").write_text(tasks_markdown(tasks), encoding="utf-8")
    (dest / "AGENT.md").write_text(E1_TASK_AGENT, encoding="utf-8")
