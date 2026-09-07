"""Seed isolated workspaces. Establishability audit and GOLD never enter."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import (
    DRAFT_TRIAL,
    MAX_DOCUMENTS_OPENED,
    MAX_RETAINED_SNIPPETS,
    PARTICIPANT,
    PERMIT_TEXT,
    PFPS,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.freeze import (
    host_visible_occurrence,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.prompts import (
    PASS_TASK,
    PASS_TASK_ADJUDICATE,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import (
    document_inventory,
)


def seed_sources(dest: Path) -> None:
    sources = dest / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "dmr_measurements.csv", sources / "dmr_measurements.csv")
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "permit_limits.csv", sources / "permit_limits.csv")
    (sources / "document_inventory.json").write_text(
        json.dumps(document_inventory(), indent=2) + "\n", encoding="utf-8"
    )


def seed_documents(dest: Path) -> list[dict]:
    docs = dest / "documents"
    docs.mkdir(parents=True)
    listed = []
    for src in sorted(PERMIT_TEXT.glob("*/*.txt")):
        rel = f"{src.parent.name}/{src.name}"
        target = docs / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        listed.append({"workspace_path": f"documents/{rel}", "chars": src.stat().st_size, "kind": src.stem, "facility": src.parent.name})
    index = ["# Document inventory", "", "Permit-package text extracts. Search only for the current obligation.", ""]
    for row in listed:
        index.append(f"- `{row['workspace_path']}` kind={row['kind']} facility={row['facility']} bytes={row['chars']}")
    (docs / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return listed


def seed_common(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    purposes = dest / "purposes"
    purposes.mkdir()
    for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
        shutil.copy2(PARTICIPANT / "purposes" / name, purposes / name)
    seed_sources(dest)
    shutil.copy2(PFPS / "source.py", dest / "source.py")
    shutil.copy2(PFPS / "world_api.py", dest / "world_api.py")
    shutil.copy2(PFPS / "frozen" / "principles.md", dest / "PRINCIPLES.md")
    shutil.copy2(PFPS / "frozen" / "WORLD_API.md", dest / "WORLD_API.md")
    shutil.copy2(PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py", dest / "construction.py")
    (dest / "PASS_TASK.md").write_text(PASS_TASK, encoding="utf-8")
    (dest / "DRAFT_NOTES.md").write_text(
        f"Draft construction is sealed trial {DRAFT_TRIAL}. Do not regenerate from scratch.\n",
        encoding="utf-8",
    )


def seed_retrieve_workspace(dest: Path, obligation: dict) -> None:
    seed_common(dest)
    listed = seed_documents(dest)
    (dest / "OBLIGATION.md").write_text(
        json.dumps(obligation, indent=2) + "\n",
        encoding="utf-8",
    )
    (dest / "BUDGET.md").write_text(
        f"Soft retrieval budget: max documents opened = {MAX_DOCUMENTS_OPENED}; "
        f"max retained snippets = {MAX_RETAINED_SNIPPETS}. Exceeding requires BUDGET_EXCEPTION.md.\n"
        f"Document files available: {len(listed)}.\n",
        encoding="utf-8",
    )
    (dest / "README.md").write_text("Obligation-first retrieval workspace. No gold.\n", encoding="utf-8")


def seed_adjudicate_workspace(dest: Path, packet: dict, construction_src: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(construction_src, dest / "construction.py")
    shutil.copy2(PFPS / "world_api.py", dest / "world_api.py")
    shutil.copy2(PFPS / "source.py", dest / "source.py")
    (dest / "PACKET.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    (dest / "PASS_TASK_ADJUDICATE.md").write_text(PASS_TASK_ADJUDICATE, encoding="utf-8")
    (dest / "README.md").write_text(
        "Bounded adjudicator. Packet only. No document corpus and no CSV search.\n",
        encoding="utf-8",
    )


def seed_occurrence_workspace(dest: Path, case: dict) -> None:
    seed_common(dest)
    seed_documents(dest)
    (dest / "OCCURRENCE.md").write_text(json.dumps(host_visible_occurrence(case), indent=2) + "\n", encoding="utf-8")
    (dest / "README.md").write_text("Occurrence-first baseline. One row. No factorized sibling obligation.\n", encoding="utf-8")
