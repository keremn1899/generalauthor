"""Condition-aware MCP server for the bounded-reliance experiment.

The v0.1 `cursor_tool_server` is unchanged. This module is launched only when
a TaskView experimental condition is bound.
"""

from __future__ import annotations

import os

from research.taskview_orientation import cursor_tool_server as _base
from research.taskview_orientation.bounded_reliance.surface import wrap_surface


_original_episode_tools = _base._episode_tools


def _episode_tools(telemetry):
    tools, view = _original_episode_tools(telemetry)
    condition = os.environ.get("TASKVIEW_CONDITION", "")
    if condition in {"T00", "T10", "T01", "T11"} and tools.taskview is not None:
        tools.taskview = wrap_surface(
            tools.taskview,
            condition=condition,
            source_root=tools.source_root,
        )
    return tools, view


_base._episode_tools = _episode_tools
mcp = _base.mcp


def main() -> None:
    _base.main()


if __name__ == "__main__":
    main()
