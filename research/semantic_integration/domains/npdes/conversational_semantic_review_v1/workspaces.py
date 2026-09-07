"""Seed isolated workspaces. Hidden packets never enter host workspaces."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.issues import ISSUES
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.paths import (
    DRAFT_TRIAL,
    PARTICIPANT,
    PFPS,
)
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.prompts import PASS_TASK
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import document_inventory


def issues_markdown(issue_ids: list[str] | None = None) -> str:
    wanted = set(issue_ids) if issue_ids else {i["id"] for i in ISSUES}
    parts = ["# Draft semantic issues\n", "From a sealed successful draft construction. Not gold.\n"]
    for issue in ISSUES:
        if issue["id"] not in wanted:
            continue
        parts.append(f"## {issue['id']}\n")
        parts.append(f"**{issue['title']}**\n")
        parts.append(f"- purpose: {issue['purpose']}")
        parts.append(f"- requirement: `{json.dumps(issue['requirement_contract'])}`")
        parts.append("- relations: " + "; ".join(issue["relations"]))
        parts.append(f"- affected scope: {issue['affected_scope']}")
        parts.append("- structured evidence: " + "; ".join(issue["structured_evidence"]))
        if issue.get("evidence_snippets"):
            parts.append("- evidence snippets:")
            for snip in issue["evidence_snippets"]:
                parts.append(f"  - `{snip}`")
        parts.append(f"- current draft interpretation: {issue['current_interpretation']}")
        parts.append(f"- remaining uncertainty: {issue['remaining_uncertainty']}")
        parts.append(f"- status: {issue['status']}\n")
    return "\n".join(parts) + "\n"


def seed_sources(dest: Path) -> None:
    sources = dest / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "dmr_measurements.csv", sources / "dmr_measurements.csv")
    shutil.copy2(PARTICIPANT / "sources" / "structured" / "permit_limits.csv", sources / "permit_limits.csv")
    (sources / "document_inventory.json").write_text(
        json.dumps(document_inventory(), indent=2) + "\n", encoding="utf-8"
    )


def seed_host_workspace(
    dest: Path,
    *,
    issue_ids: list[str] | None = None,
    include_construction: bool = True,
    draft_trial: str = DRAFT_TRIAL,
) -> None:
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
    (dest / "PASS_TASK.md").write_text(PASS_TASK, encoding="utf-8")
    (dest / "ISSUES.md").write_text(issues_markdown(issue_ids), encoding="utf-8")
    (dest / "DRAFT_NOTES.md").write_text(
        f"Draft construction is from sealed trial {draft_trial}. Do not regenerate from scratch.\n",
        encoding="utf-8",
    )
    if include_construction:
        src = PFPS / "runs" / draft_trial / "iter1" / "construction.py"
        shutil.copy2(src, dest / "construction.py")
    (dest / "README.md").write_text(
        "Isolated conversational semantic-review probe. No gold. No hidden expert packets.\n",
        encoding="utf-8",
    )


def seed_proxy_workspace(dest: Path, *, stance: str, host_message: str) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / "EXPERT_STANCE.md").write_text(stance.strip() + "\n", encoding="utf-8")
    (dest / "HOST_MESSAGE.md").write_text(host_message.strip() + "\n", encoding="utf-8")
    (dest / "README.md").write_text(
        "You are a domain expert in an experiment. Reply in REPLY.md only.\n",
        encoding="utf-8",
    )
