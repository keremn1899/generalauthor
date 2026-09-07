"""Seed participant workspaces. GOLD never enters. Worlds copied read-only."""

from __future__ import annotations

import shutil
from pathlib import Path

from research.semantic_integration.capability.end_to_end_v1.workspaces import seed_runtime
from research.semantic_integration.capability.world_read_programming_v1.paths import (
    DOMAIN_IDS,
    E2E,
    ROOT,
    t1_accepted,
)
from research.semantic_integration.capability.world_read_programming_v1.prompts import (
    CONSUMER_A0,
    CONSUMER_A1,
    CONTRACT,
    PROGRAMMER_A0,
    PROGRAMMER_A1,
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


def questions_markdown(questions: list[dict]) -> str:
    lines = ["# Diagnostic questions", "", "Answer in `answers.json`. Do not invent unsupported facts.", ""]
    current = None
    for item in questions:
        domain = item["domain"]
        if domain != current:
            lines.append(f"# Domain `{domain}`")
            lines.append("")
            current = domain
        lines.append(f"## {item['id']}")
        lines.append("")
        lines.append(item["question"])
        lines.append("")
    return "\n".join(lines) + "\n"


def purposes_markdown() -> str:
    lines = ["# Declared purposes", ""]
    for domain_id in DOMAIN_IDS:
        lines.append(f"## {domain_id}")
        lines.append("")
        lines.append(purpose_text(domain_id).strip())
        lines.append("")
    return "\n".join(lines) + "\n"


def seed_part_a(dest: Path, *, arm: str, questions: list[dict]) -> dict[str, int]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    seed_runtime(dest)
    for domain_id in DOMAIN_IDS:
        copy_accepted_world(t1_accepted(domain_id), dest / "worlds" / domain_id)
    (dest / "PURPOSE.md").write_text(purposes_markdown(), encoding="utf-8")
    (dest / "QUESTIONS.md").write_text(questions_markdown(questions), encoding="utf-8")
    consumer = CONSUMER_A1 if arm == "A1" else CONSUMER_A0
    (dest / "CONSUMER.md").write_text(consumer, encoding="utf-8")
    contract_bytes = 0
    if arm == "A1":
        (dest / "CONTRACT.md").write_text(CONTRACT, encoding="utf-8")
        contract_bytes = len(CONTRACT.encode("utf-8"))
    shutil.copy2(ROOT / "inspect_worlds.py", dest / "inspect_worlds.py")
    (dest / "README.md").write_text(
        "Part A consumer. Query worlds/<domain> only. No raw sources.\n",
        encoding="utf-8",
    )
    initial = sum(
        (dest / name).stat().st_size
        for name in ("CONSUMER.md", "PURPOSE.md", "QUESTIONS.md", "README.md")
        if (dest / name).exists()
    )
    if arm == "A1":
        initial += contract_bytes
    return {
        "initial_context_bytes": initial,
        "contract_bytes": contract_bytes,
        "questions_bytes": (dest / "QUESTIONS.md").stat().st_size,
        "purpose_bytes": (dest / "PURPOSE.md").stat().st_size,
    }


def tasks_markdown(tasks: list[dict]) -> str:
    lines = ["# Programming tasks", "", "Answer all three from this World. Write `answers.json`.", ""]
    for item in tasks:
        lines.append(f"## {item['id']}")
        lines.append("")
        lines.append(item["prompt"])
        lines.append("")
    return "\n".join(lines) + "\n"


def seed_part_b(dest: Path, *, domain_id: str, arm: str, tasks: list[dict]) -> dict[str, int]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    seed_runtime(dest)
    copy_accepted_world(t1_accepted(domain_id), dest / "world")
    (dest / "PURPOSE.txt").write_text(purpose_text(domain_id), encoding="utf-8")
    (dest / "TASKS.md").write_text(tasks_markdown(tasks), encoding="utf-8")
    programmer = PROGRAMMER_A1 if arm == "A1" else PROGRAMMER_A0
    (dest / "PROGRAMMER.md").write_text(programmer, encoding="utf-8")
    contract_bytes = 0
    if arm == "A1":
        (dest / "CONTRACT.md").write_text(CONTRACT, encoding="utf-8")
        contract_bytes = len(CONTRACT.encode("utf-8"))
    shutil.copy2(ROOT / "inspect_world.py", dest / "inspect_world.py")
    (dest / "README.md").write_text(
        "Part B programmer. Query world/ only. No raw sources. Do not modify the World.\n",
        encoding="utf-8",
    )
    names = ["PROGRAMMER.md", "PURPOSE.txt", "TASKS.md", "README.md"]
    initial = sum((dest / name).stat().st_size for name in names if (dest / name).exists())
    if arm == "A1":
        initial += contract_bytes
    return {
        "initial_context_bytes": initial,
        "contract_bytes": contract_bytes,
        "tasks_bytes": (dest / "TASKS.md").stat().st_size,
        "purpose_bytes": (dest / "PURPOSE.txt").stat().st_size,
    }
