#!/usr/bin/env python3
"""The exact frozen One-off Graph Programming v1 experiment surface."""
import contextlib, io, json, os, sys, time
from pathlib import Path
from mcp_server.retrieve import Retrieve
from mcp_server.surface import Surface
from research.abstraction_frontier.treatment import ExcludedEphemeralOperation, validate_frozen_ephemeral_program

ALLOWED = {"describe", "lookup", "expand", "path", "run_ephemeral_traversal"}
def walk(value, key):
    out=[]
    if isinstance(value, dict):
        for k,v in value.items():
            if k == key and isinstance(v,str): out.append(v)
            out.extend(walk(v,key))
    elif isinstance(value,list):
        for v in value: out.extend(walk(v,key))
    return sorted(set(out))
def audit(event):
    event["order"] = time.time_ns()
    with Path(os.environ["AF_GRAPH_AUDIT"]).open("a", encoding="utf-8") as h: h.write(json.dumps(event, sort_keys=True)+"\n")
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ALLOWED: raise SystemExit("usage: graphauthor_access.py OPERATION JSON")
    operation, args = sys.argv[1], json.loads(sys.argv[2])
    if not isinstance(args, dict): raise SystemExit("arguments must be an object")
    if {"search", "read_cypher", "include_content", "context_ref", "graph_version", "explain"} & set(args): raise SystemExit("not exposed by this frozen treatment")
    if operation == "run_ephemeral_traversal":
        try: validate_frozen_ephemeral_program(args.get("program") or {})
        except ExcludedEphemeralOperation as exc:
            audit({"event":"graph_operation_rejected", "operation":operation, "arguments":args, "error":str(exc), "before_execution":True})
            raise SystemExit(str(exc))
    silence=io.StringIO(); surface=None
    try:
        with contextlib.redirect_stdout(silence), contextlib.redirect_stderr(silence):
            surface=Surface(Path("view.lbug"), capabilities=("query",))
            if operation == "describe": result=surface.describe()
            elif operation == "run_ephemeral_traversal": result=surface.run_ephemeral_traversal(args.get("program") or {}, args.get("parameters"), evidence="packet")
            else: result=getattr(Retrieve(surface), operation)(**args)
        audit_packet = None
        ref = result.get("audit_evidence_ref") if isinstance(result,dict) else None
        if ref: audit_packet = surface._traversal_audit_packets.get(ref, {})
        audit({"event":"graph_operation", "operation":operation, "arguments":args, "outcome":result.get("outcome"), "returned_ids":walk(result,"id") + walk(result,"answer_node_ids"), "used_relation_ids":walk(audit_packet,"relation_id") + walk(result,"relation_id"), "receipt":result.get("execution_receipt"), "audit_evidence_ref":ref})
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        audit({"event":"graph_operation_failure", "operation":operation, "arguments":args, "error":repr(exc)})
        raise
    finally:
        if surface:
            with contextlib.redirect_stdout(silence), contextlib.redirect_stderr(silence): surface.close()
if __name__ == "__main__": main()
