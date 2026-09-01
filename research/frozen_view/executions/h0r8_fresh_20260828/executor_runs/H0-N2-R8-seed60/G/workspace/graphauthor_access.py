#!/usr/bin/env python3
"""Bounded Graphauthor retrieval client installed by the experiment harness."""
import contextlib, io, json, os, sys, time
from pathlib import Path
from mcp_server.retrieve import Retrieve
from mcp_server.surface import Surface

def ids(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "id" and isinstance(item, str): found.append(item)
            else: found.extend(ids(item))
    elif isinstance(value, list):
        for item in value: found.extend(ids(item))
    return sorted(set(found))
def relation_ids(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"edge_label", "label"} and isinstance(item, str):
                parts = item.split("|", 2)
                if len(parts) == 3 and parts[2].startswith("rel:"): found.append(parts[2])
            found.extend(relation_ids(item))
    elif isinstance(value, list):
        for item in value: found.extend(relation_ids(item))
    return sorted(set(found))
def audit(event):
    path = Path(os.environ["FROZEN_VIEW_GRAPH_AUDIT"])
    event["order"] = time.time_ns()
    with path.open("a", encoding="utf-8") as h: h.write(json.dumps(event, sort_keys=True) + "\n")
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"lookup", "expand", "path"}:
        raise SystemExit("usage: graphauthor_access.py lookup|expand|path '<JSON arguments object>'")
    operation, kwargs = sys.argv[1], json.loads(sys.argv[2])
    if not isinstance(kwargs, dict): raise SystemExit("arguments must be a JSON object")
    forbidden = {"search", "read_cypher", "include_content", "context_ref", "graph_version"}
    if forbidden.intersection(kwargs): raise SystemExit("this experiment exposes only bounded non-content graph reads")
    # Surface initialization maintains version/receipt state and may emit
    # diagnostic structural-index messages. Those diagnostics contain derived
    # topology labels and are deliberately not participant-visible.
    diagnostics = io.StringIO()
    surface = None
    try:
        with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
            surface = Surface(Path("view.lbug"), capabilities=("query",))
            method = getattr(Retrieve(surface), operation)
            result = method(**kwargs)
        audit({"event": "graph_operation", "operation": operation, "arguments": kwargs,
               "returned_ids": ids(result), "used_relation_ids": relation_ids(result), "outcome": result.get("outcome")})
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        audit({"event": "graph_operation_failure", "operation": operation, "arguments": kwargs, "error": repr(exc)})
        raise
    finally:
        if surface is not None:
            with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics): surface.close()
if __name__ == "__main__": main()
