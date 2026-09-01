"""Verbatim human-readable export of sealed Stage 1 v0.1 provider trajectories.

Zero participant inference.  No behavioral analysis.  No payload substitution.
"""

from __future__ import annotations

from pathlib import Path

EXPORTER_ID = "taskview-orientation-trajectory-export-v1"
PACKAGE_ROOT = Path(__file__).resolve().parent
EXPORT_ROOT = PACKAGE_ROOT.parent / "exports" / "stage1-v01-v4-searchfix"

SELECTED = (
    {"arm": "RAW", "replicate": 2, "filename": "raw-r2.txt"},
    {"arm": "TASKVIEW", "replicate": 2, "filename": "taskview-r2.txt"},
    {"arm": "RAW", "replicate": 4, "filename": "raw-r4.txt"},
    {"arm": "TASKVIEW", "replicate": 4, "filename": "taskview-r4.txt"},
)

# Exact first-turn / later-turn prefix used by the sealed v4 SDK adapter.
# Duplicated here so export does not construct a live Cursor session.
SDK_CONTRACT_PREFIX = (
    "Use only tools from the taskview-orientation MCP server. Return only one JSON "
    "object, without Markdown fences, conforming exactly to this schema: "
)
