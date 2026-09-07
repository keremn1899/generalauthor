"""Host-side World/source smoke. Not a model trial."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    run_construction,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import seed_workspace

SMOKE = r'''
from source import Source, interval_contains
from world_api import World, Purpose

src = Source("sources")
world = World()
purpose = Purpose(world)

dmr = src.rows("dmr_measurements.csv")
limits = src.rows("permit_limits.csv")
docs = src.document_inventory()

world.relation("measurement", [
    ("measurement", "REFERENT"), ("permit_id", "TEXT"), ("outfall", "TEXT"),
    ("parameter_code", "TEXT"), ("period_end", "TEXT"), ("nodi_code", "TEXT"),
])
world.relation("limit_row", [
    ("limit", "REFERENT"), ("permit_id", "TEXT"), ("outfall", "TEXT"),
    ("parameter_code", "TEXT"), ("begin_date", "TEXT"), ("end_date", "TEXT"),
    ("limit_value", "TEXT"), ("comment", "TEXT"),
])
world.relation("source_document", [
    ("document", "REFERENT"), ("permit", "TEXT"), ("document_kind", "TEXT"),
])

mrows, lrows = [], []
for row in dmr:
    rid = world.referent("Measurement", {
        "permit": row["EXTERNAL_PERMIT_NMBR"],
        "outfall": row["PERM_FEATURE_NMBR"],
        "parameter": row["PARAMETER_CODE"],
        "period": row["MONITORING_PERIOD_END_DATE"],
        "vt": row.get("VALUE_TYPE_CODE") or "",
    })
    mrows.append({
        "measurement": rid,
        "permit_id": row["EXTERNAL_PERMIT_NMBR"],
        "outfall": row["PERM_FEATURE_NMBR"],
        "parameter_code": row["PARAMETER_CODE"],
        "period_end": row["MONITORING_PERIOD_END_DATE"],
        "nodi_code": row.get("NODI_CODE") or "",
    })
for row in limits:
    rid = world.referent("Limit", {"id": row["LIMIT_VALUE_ID"]})
    lrows.append({
        "limit": rid,
        "permit_id": row["EXTERNAL_PERMIT_NMBR"],
        "outfall": row["PERM_FEATURE_NMBR"],
        "parameter_code": row["PARAMETER_CODE"],
        "begin_date": row["LIMIT_BEGIN_DATE"],
        "end_date": row["LIMIT_END_DATE"],
        "limit_value": row.get("LIMIT_VALUE_NMBR") or "",
        "comment": row.get("DMR_COMMENT_TEXT") or "",
    })
world.map("measurement", mrows, grounding={"source": "dmr_measurements.csv"})
world.map("limit_row", lrows, grounding={"source": "permit_limits.csv"})
world.map("source_document", [
    {
        "document": world.referent("Document", {"path": d["path"]}),
        "permit": d["permit"],
        "document_kind": d["document_kind"],
    }
    for d in docs
], grounding={"source": "document_inventory.json"})

index = {}
for row in lrows:
    index.setdefault((row["permit_id"], row["outfall"], row["parameter_code"]), []).append(row)
cands = []
for m in mrows:
    for lim in index.get((m["permit_id"], m["outfall"], m["parameter_code"]), []):
        if interval_contains(m["period_end"], lim["begin_date"], lim["end_date"]):
            cands.append({
                "measurement": m["measurement"],
                "limit": lim["limit"],
                "permit_id": m["permit_id"],
                "parameter_code": m["parameter_code"],
                "limit_value": lim["limit_value"],
                "comment": lim["comment"],
                "nodi_code": m["nodi_code"],
            })
world.derive("candidate_limit", cands, roles=[
    ("measurement", "REFERENT"), ("limit", "REFERENT"), ("permit_id", "TEXT"),
    ("parameter_code", "TEXT"), ("limit_value", "TEXT"), ("comment", "TEXT"), ("nodi_code", "TEXT"),
], inputs=["measurement", "limit_row"])

purpose.require_unique("applicable_limit", per="measurement", candidates="candidate_limit", purpose="A")
purpose.require_numeric("numeric_limit", relation="candidate_limit", field="limit_value", purpose="A")
purpose.require_interpreted("nodi", relation="candidate_limit", field="nodi_code", known=[""], purpose="C")
purpose.require_interpreted("comments", relation="limit_row", field="comment", known=[""], purpose="B")
purpose.require_unique("one_doc", per="permit", candidates="source_document", purpose="A")
'''


def main() -> None:
    live = Path(tempfile.mkdtemp(prefix="pfps-live-"))
    clean_parent = Path(tempfile.mkdtemp(prefix="pfps-clean-"))
    try:
        seed_workspace(live)
        (live / "construction.py").write_text(SMOKE, encoding="utf-8")
        clean = clean_parent / "run"
        prepare_clean_run(live, clean)
        result = run_construction(clean)
        print("ok", result.get("ok"), "errors", result.get("errors"))
        print("rows", result.get("relation_row_counts"))
        print("groups", result.get("n_hole_groups"), "instances", result.get("n_hole_instances"))
        kinds = sorted({g["failure_kind"] for g in (result.get("hole_groups") or [])})
        print("kinds", kinds)
        if not result.get("ok"):
            raise SystemExit(result)
        needed = {
            "CARDINALITY_OVERSATISFIED",
            "MULTIPLE_CANDIDATES",
            "COMPARISON_OPERATOR_REQUIRED",
            "UNINTERPRETED",
        }
        missing = needed - set(kinds)
        if missing:
            raise SystemExit(f"missing {missing}")
        cands = (result.get("relation_row_counts") or {}).get("candidate_limit") or 0
        if cands < 1:
            raise SystemExit("candidate_limit empty")
    finally:
        shutil.rmtree(live, ignore_errors=True)
        shutil.rmtree(clean_parent, ignore_errors=True)


if __name__ == "__main__":
    main()
