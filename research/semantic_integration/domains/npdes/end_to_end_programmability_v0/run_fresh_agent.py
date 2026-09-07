"""Fresh Composer 2.5 consumers against source-free accepted Worlds."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.agent import run_probe_agent
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.gold import write_gold
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.isolation import (
    SOURCE_MARKERS,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    FRESH,
    ISOLATED,
    MODEL,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.prompts import FIRST_PROMPT, PASS_TASK


def seed_agent_workspace(state_id: str) -> Path:
    src = ISOLATED / state_id
    live = new_live_workspace()
    shutil.copytree(src / "accepted", live / "accepted")
    shutil.copy2(src / "compact_header.md", live / "compact_header.md")
    (live / "PASS_TASK.md").write_text(PASS_TASK, encoding="utf-8")
    (live / "README.md").write_text(
        "Fresh-agent workspace. Compact header + accepted World only. No sources, no construction.py, no gold.\n",
        encoding="utf-8",
    )
    return live


def _source_attempts(text: str) -> list[str]:
    lower = text.lower()
    return [m for m in SOURCE_MARKERS if m.lower() in lower]


def run_state_agent(state_id: str) -> dict:
    FRESH.mkdir(parents=True, exist_ok=True)
    dest = FRESH / state_id
    dest.mkdir(parents=True, exist_ok=True)
    live = seed_agent_workspace(state_id)
    preflight = preflight_isolation(live)
    result = run_probe_agent(workspace=live, prompt=FIRST_PROMPT, timeout_seconds=TIMEOUT_SECONDS)
    answers = ""
    answers_path = live / "ANSWERS.md"
    if answers_path.exists():
        answers = answers_path.read_text(encoding="utf-8")
        shutil.copy2(answers_path, dest / "ANSWERS.md")
    blob = (result.get("assistant_text") or "") + "\n" + answers
    payload = {
        "state_id": state_id,
        "model": MODEL,
        "reported_model": result.get("reported_model"),
        "returncode": result.get("returncode"),
        "timed_out": result.get("timed_out"),
        "usage": result.get("usage"),
        "tools": result.get("tools"),
        "exploration": result.get("exploration"),
        "preflight_ok": bool(preflight.get("ok")),
        "source_marker_hits": _source_attempts(json.dumps(result.get("events") or []) + blob),
        "n_sql_queries": sum(
            1
            for ev in (result.get("events") or [])
            if "sqlite" in json.dumps(ev).lower() or "select " in json.dumps(ev).lower()
        ),
        "assistant_text_len": len(result.get("assistant_text") or ""),
        "has_answers_md": answers_path.exists(),
    }
    (dest / "run.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (dest / "assistant.md").write_text(result.get("assistant_text") or "", encoding="utf-8")
    (dest / "events.json").write_text(json.dumps(result.get("events") or [], indent=2)[:2_000_000], encoding="utf-8")
    remove_live_workspace(live)
    return payload


def run_fresh_agents() -> dict:
    write_gold()
    # Isolated calls. State C must not see State A transcript.
    a = run_state_agent("state_a")
    c = run_state_agent("state_c")
    payload = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "state_a": a,
        "state_c": c,
    }
    (FRESH / "campaign.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    run_fresh_agents()
