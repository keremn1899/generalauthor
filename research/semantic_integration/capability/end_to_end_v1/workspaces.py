"""Seed participant workspaces. GOLD never enters."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from research.semantic_integration.capability.end_to_end_v1.paths import (
    CORE,
    DOMAINS,
    REPO,
    RUNTIME_V0,
    TASKVIEW,
)
from research.semantic_integration.capability.end_to_end_v1.prompts import (
    CONSUMER_RAW_TASK,
    CONSUMER_WORLD_TASK,
    PASS_TASK,
    RUNTIME_MD,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_py_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for path in src.iterdir():
        if path.name == "__pycache__" or path.suffix in {".pyc"}:
            continue
        if path.is_dir():
            continue
        if path.suffix == ".py" or path.name == "README.md":
            shutil.copy2(path, dest / path.name)


def seed_runtime(dest: Path) -> None:
    _copy_py_tree(TASKVIEW, dest / "taskview")
    research = dest / "research"
    (research / "semantic_integration" / "core").mkdir(parents=True, exist_ok=True)
    (research / "semantic_integration" / "runtime_v0").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "research" / "__init__.py", research / "__init__.py")
    shutil.copy2(
        REPO / "research" / "semantic_integration" / "__init__.py",
        research / "semantic_integration" / "__init__.py",
    )
    _copy_py_tree(CORE, research / "semantic_integration" / "core")
    for name in (
        "__init__.py",
        "world.py",
        "purpose.py",
        "source_helpers.py",
        "commit.py",
        "project.py",
    ):
        shutil.copy2(RUNTIME_V0 / name, research / "semantic_integration" / "runtime_v0" / name)


def seed_construction_workspace(dest: Path, domain_id: str) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    domain = DOMAINS / domain_id
    shutil.copytree(domain / "sources", dest / "sources")
    shutil.copy2(domain / "purpose.txt", dest / "purpose.txt")
    seed_runtime(dest)
    (dest / "PASS_TASK.md").write_text(PASS_TASK, encoding="utf-8")
    (dest / "RUNTIME.md").write_text(RUNTIME_MD, encoding="utf-8")
    shutil.copy2(Path(__file__).parent / "run_world.py", dest / "run_world.py")
    (dest / "README.md").write_text(
        "Isolated semantic compilation workspace. Purpose + sources + frozen runtime_v0. No gold.\n",
        encoding="utf-8",
    )


def questions_markdown(questions: list[dict]) -> str:
    lines = ["# Hidden competency questions", "", "Answer in `answers.json`. Do not invent unsupported facts.", ""]
    for item in questions:
        lines.append(f"## {item['id']}")
        lines.append("")
        lines.append(item["question"])
        lines.append("")
    return "\n".join(lines) + "\n"


def seed_world_consumer(dest: Path, *, domain_id: str, accepted: Path, questions: list[dict]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(DOMAINS / domain_id / "purpose.txt", dest / "purpose.txt")
    shutil.copytree(accepted, dest / "world")
    seed_runtime(dest)
    (dest / "QUESTIONS.md").write_text(questions_markdown(questions), encoding="utf-8")
    (dest / "CONSUMER.md").write_text(CONSUMER_WORLD_TASK, encoding="utf-8")
    shutil.copy2(Path(__file__).parent / "inspect_world.py", dest / "inspect_world.py")
    (dest / "README.md").write_text(
        "WORLD consumer. Query accepted/world only. No raw sources.\n",
        encoding="utf-8",
    )


def seed_raw_consumer(dest: Path, *, domain_id: str, questions: list[dict]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    domain = DOMAINS / domain_id
    shutil.copytree(domain / "sources", dest / "sources")
    shutil.copy2(domain / "purpose.txt", dest / "purpose.txt")
    (dest / "QUESTIONS.md").write_text(questions_markdown(questions), encoding="utf-8")
    (dest / "CONSUMER.md").write_text(CONSUMER_RAW_TASK, encoding="utf-8")
    (dest / "README.md").write_text(
        "RAW consumer. Raw evidence only. No compiled World.\n",
        encoding="utf-8",
    )
