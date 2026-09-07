"""Parse model JSON artifacts. Evaluator-only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DISPOSITIONS = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        text = path.read_text(encoding="utf-8")
        return extract_json_object(text)


def extract_json_object(text: str) -> Any:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def canon_disp(value: Any) -> str:
    text = str(value or "UNRESOLVED").strip().upper().replace(" ", "_")
    if text in {"SAME", "SAMEENTITY", "ACCEPT"}:
        text = "SAME_ENTITY"
    if text in {"DIFFERENT", "REJECT"}:
        text = "DISTINCT"
    if text in DISPOSITIONS:
        return text
    return "UNRESOLVED"


def evidence_in_packet(evidence: Any, packet: dict) -> bool:
    if not evidence:
        return True
    observations = packet.get("selected_observations") or []
    allowed = {
        (str(obs.get("source_path") or ""), str(obs.get("location") or ""))
        for obs in observations
        if isinstance(obs, dict)
    }
    if isinstance(evidence, dict):
        evidence = [evidence]
    if not isinstance(evidence, list):
        return False
    for item in evidence:
        if not isinstance(item, dict):
            return False
        key = (str(item.get("source_path") or ""), str(item.get("location") or ""))
        if key not in allowed:
            return False
    return True


def packet_observation_blob(packet: dict) -> str:
    parts = []
    for obs in packet.get("selected_observations") or []:
        if isinstance(obs, dict):
            parts.append(str(obs.get("excerpt") or ""))
    return " ".join(parts).lower()
