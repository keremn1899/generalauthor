from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.taskview_orientation.runtime import (
    MCP_SERVER_NAME,
    MODEL,
    MODEL_DISPLAY_NAME,
    mcp_identity,
    provider_tools,
    provider_validation_rejections,
    runtime_binding,
    stream_events,
)
from research.taskview_orientation.runtime_sdk import (
    BUILTIN_TOOL_ALLOWLIST,
    _tool_name,
    runtime_binding as sdk_runtime_binding,
)


def test_cursor_composer_25_is_the_default_binding():
    binding = runtime_binding()
    assert binding["provider"] == "cursor"
    assert binding["model"] == MODEL == "composer-2.5"
    assert binding["model_display_name"] == MODEL_DISPLAY_NAME == "Composer 2.5"
    assert binding["adapter"] == "taskview-cursor-agent-v2"


def test_provider_tool_serialization_keeps_frozen_name_and_schema():
    result = provider_tools(
        [{"name": "read_source", "description": "Read frozen source."}]
    )
    assert result[0]["server"] == MCP_SERVER_NAME
    assert result[0]["name"] == "read_source"
    assert result[0]["inputSchema"]["required"] == ["path"]


def test_cursor_stream_parser_and_mcp_identity_match_observed_shape():
    event = {
        "type": "tool_call",
        "subtype": "started",
        "tool_call": {
            "mcpToolCall": {
                "args": {
                    "name": "taskview-orientation-read_source",
                    "providerIdentifier": "taskview-orientation",
                    "serverIdentifier": "taskview-orientation",
                    "toolName": "read_source",
                    "args": {"path": "x"},
                }
            }
        },
    }
    parsed = stream_events(json.dumps(event) + "\nnot-json\n")
    assert parsed == [event]
    assert mcp_identity(parsed[0]) == ("taskview-orientation", "read_source")


def test_runtime_policy_invalidates_non_experiment_cursor_tools():
    policy = runtime_binding()["tool_policy"]
    assert "Cursor built-in" in policy
    assert "unrelated MCP" in policy


def test_provider_validation_rejection_is_recoverable_canonical_tool_attempt():
    event = {
        "type": "tool_call",
        "subtype": "completed",
        "call_id": "tool-bad-1",
        "tool_call": {
            "mcpToolCall": {
                "args": {
                    "toolCallId": "tool-bad-1",
                    "toolName": "read_source",
                    "args": {"query": "direct", "scope": "."},
                },
                "result": {
                    "success": {
                        "content": [
                            {
                                "text": {
                                    "text": (
                                        "Error executing tool read_source: 1 validation error "
                                        "for read_sourceArguments; path Field required"
                                    )
                                }
                            }
                        ],
                        "isError": False,
                    }
                },
            }
        },
    }
    assert provider_validation_rejections([event]) == [
        {
            "call_id": "tool-bad-1",
            "tool_name": "read_source",
            "tool_arguments": {"query": "direct", "scope": "."},
            "provider_result": event["tool_call"]["mcpToolCall"]["result"],
        }
    ]


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v1/"
    "taskview-orientation-v1-e01-raw-r1/provider_trajectory.jsonl"
)
def test_sealed_raw1_failure_replays_as_one_validation_rejection():
    trajectory = Path(
        "research/taskview_orientation/results/stage1-cursor-v1/"
        "taskview-orientation-v1-e01-raw-r1/provider_trajectory.jsonl"
    )
    events = [json.loads(line) for line in trajectory.read_text(encoding="utf-8").splitlines()]
    started = [
        event
        for event in events
        if event.get("type") == "tool_call"
        and event.get("subtype") == "started"
        and "mcpToolCall" in event.get("tool_call", {})
    ]
    rejections = provider_validation_rejections(events)
    bridge = Path(
        "research/taskview_orientation/results/stage1-cursor-v1/"
        "taskview-orientation-v1-e01-raw-r1/provider_workspace/"
        "logical_tool_telemetry.jsonl"
    )
    logical = [
        json.loads(line)
        for line in bridge.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["event_type"] == "TOOL_CALL"
    ]
    assert len(started) == 39
    assert len(logical) == 38
    assert len(rejections) == 1
    assert rejections[0]["tool_name"] == "read_source"
    assert len(logical) + len(rejections) == len(started)


def test_sdk_v4_exposes_only_mcp_capability_and_inline_frozen_names():
    binding = sdk_runtime_binding()
    assert binding["adapter"] == "taskview-cursor-sdk-v4"
    assert binding["accounting_model"] == "cursor-mcp-identity-v1"
    assert BUILTIN_TOOL_ALLOWLIST == ("mcp",)
    assert binding["builtin_tool_allowlist"] == ["mcp"]
    assert "inline taskview-orientation server" in binding["tool_policy"]
    allowed = {"read_source", "query_sql"}
    assert _tool_name("read_source", allowed) == "read_source"
    assert _tool_name("taskview-orientation-read_source", allowed) == "read_source"
    assert _tool_name("glob", allowed) is None
