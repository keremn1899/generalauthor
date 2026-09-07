"""Acquire-freeze NPDES FY2025 participant/evaluator fixtures. No constructor inference."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = NPDES.parents[3]
RAW = Path("/tmp/npdes-raw")
PART = ROOT / "participant_sources"
EVAL = ROOT / "evaluator_only"
MANIFESTS = ROOT / "manifests"

PERMITS = {
    "NM0020583": {"name": "City of Farmington WWTP", "folder": "farmington"},
    "NM0028762": {"name": "City of Aztec Water Treatment Plant", "folder": "aztec"},
    "NM0000116": {"name": "GCC Rio Grande", "folder": "gcc"},
}
OPTIONAL_SUBSTITUTE = "NM0030279"
FY_START = "2024-10-01"
FY_END = "2025-09-30"

DMR_KEEP = [
    "ACTIVITY_ID", "EXTERNAL_PERMIT_NMBR", "VERSION_NMBR",
    "PERM_FEATURE_ID", "PERM_FEATURE_NMBR", "PERM_FEATURE_TYPE_CODE",
    "LIMIT_SET_ID", "LIMIT_SET_DESIGNATOR", "LIMIT_SET_SCHEDULE_ID", "LIMIT_ID",
    "LIMIT_BEGIN_DATE", "LIMIT_END_DATE",
    "NMBR_OF_SUBMISSION", "NMBR_OF_REPORT",
    "PARAMETER_CODE", "PARAMETER_DESC", "MONITORING_LOCATION_CODE",
    "STAY_TYPE_CODE", "STAY_VALUE_NMBR",
    "LIMIT_VALUE_ID", "LIMIT_VALUE_TYPE_CODE", "LIMIT_VALUE_NMBR",
    "LIMIT_UNIT_CODE", "LIMIT_UNIT_DESC",
    "STANDARD_UNIT_CODE", "STANDARD_UNIT_DESC", "LIMIT_VALUE_STANDARD_UNITS",
    "STATISTICAL_BASE_CODE", "STATISTICAL_BASE_TYPE_CODE",
    "LIMIT_VALUE_QUALIFIER_CODE", "OPTIONAL_MONITORING_FLAG",
    "LIMIT_SAMPLE_TYPE_CODE", "LIMIT_FREQ_OF_ANALYSIS_CODE", "LIMIT_TYPE_CODE",
    "DMR_EVENT_ID", "MONITORING_PERIOD_END_DATE",
    "DMR_SAMPLE_TYPE_CODE", "DMR_FREQ_OF_ANALYSIS_CODE",
    "DMR_FORM_VALUE_ID", "VALUE_TYPE_CODE", "DMR_VALUE_ID",
    "DMR_VALUE_NMBR", "DMR_UNIT_CODE", "DMR_UNIT_DESC",
    "DMR_VALUE_STANDARD_UNITS", "DMR_VALUE_QUALIFIER_CODE",
    "VALUE_RECEIVED_DATE", "NODI_CODE",
]
DMR_REMOVE = [
    "REPORTED_EXCURSION_NMBR", "DAYS_LATE", "EXCEEDENCE_PCT",
    "NPDES_VIOLATION_ID", "VIOLATION_CODE",
    "RNC_DETECTION_CODE", "RNC_DETECTION_DATE",
    "RNC_RESOLUTION_CODE", "RNC_RESOLUTION_DATE",
]

NODI_MEANING = {
    "C": "No Discharge",
    "9": "Conditional Monitoring - Not Required",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(bytes.fromhex(sha256_file(path)))
    return h.hexdigest()


def parse_float(raw: str | None) -> float | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_mdy(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def filter_csv(src: Path, id_col: str) -> tuple[list[str], list[dict[str, str]]]:
    with src.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = [row for row in reader if (row.get(id_col) or "").strip() in PERMITS]
    return header, rows


def suitability(dmr: list[dict[str, str]], limits: list[dict[str, str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for pid, meta in PERMITS.items():
        drows = [r for r in dmr if r["EXTERNAL_PERMIT_NMBR"] == pid]
        lrows = [r for r in limits if r["EXTERNAL_PERMIT_NMBR"] == pid]
        params = sorted({f"{r['PARAMETER_CODE']}:{r['PARAMETER_DESC']}" for r in drows})
        outfalls = sorted({r["PERM_FEATURE_NMBR"] for r in drows})
        numeric = sum(1 for r in drows if (r.get("LIMIT_VALUE_NMBR") or "").strip())
        report_only = len(drows) - numeric
        nodi = Counter((r.get("NODI_CODE") or "").strip() or "(blank)" for r in drows)
        optional = Counter((r.get("OPTIONAL_MONITORING_FLAG") or "").strip() or "(blank)" for r in drows)
        intervals = sorted({(r.get("LIMIT_BEGIN_DATE"), r.get("LIMIT_END_DATE")) for r in drows})
        out[pid] = {
            "name": meta["name"],
            "fy2025_dmr_rows": len(drows),
            "limit_rows": len(lrows),
            "parameters": len(params),
            "parameter_list": params,
            "outfalls": outfalls,
            "numeric_limit_rows": numeric,
            "no_numeric_limit_rows": report_only,
            "nodi": dict(nodi),
            "optional_monitoring_flag": dict(optional),
            "limit_effective_intervals": intervals,
            "documents": sorted(p.name for p in (RAW / "permits" / meta["folder"]).glob("*.pdf")),
        }
    out["substitution"] = {
        "optional_candidate": OPTIONAL_SUBSTITUTE,
        "substituted": False,
        "reason": "All three primary facilities have FY2025 DMR rows, multiple parameters, and official permit documents.",
    }
    return out


def gold_m_row(row: dict[str, str]) -> dict[str, Any]:
    value = parse_float(row.get("DMR_VALUE_NMBR"))
    limit = parse_float(row.get("LIMIT_VALUE_NMBR"))
    nodi = (row.get("NODI_CODE") or "").strip()
    optional = (row.get("OPTIONAL_MONITORING_FLAG") or "").strip().upper() == "Y"
    base_type = (row.get("STATISTICAL_BASE_TYPE_CODE") or "").strip().upper()
    epa_pct = parse_float(row.get("EXCEEDENCE_PCT"))
    epa_violation = (row.get("VIOLATION_CODE") or "").strip()
    comparable = limit is not None and value is not None and not nodi
    enforceable_numeric = limit is not None and not optional
    report_only = (limit is None) or optional
    mechanical_exceedance = None
    if comparable and enforceable_numeric:
        if base_type in {"MN", "MIN"}:
            mechanical_exceedance = value < limit
        else:
            mechanical_exceedance = value > limit
    epa_exceedance = None
    if epa_pct is not None:
        epa_exceedance = epa_pct > 0
    elif epa_violation:
        epa_exceedance = True
    conflict = False
    if mechanical_exceedance is not None and epa_exceedance is not None:
        conflict = bool(mechanical_exceedance) != bool(epa_exceedance)
    return {
        "permit": row.get("EXTERNAL_PERMIT_NMBR"),
        "outfall": row.get("PERM_FEATURE_NMBR"),
        "parameter_code": row.get("PARAMETER_CODE"),
        "parameter_desc": row.get("PARAMETER_DESC"),
        "monitoring_period_end": parse_mdy(row.get("MONITORING_PERIOD_END_DATE")),
        "reported_value": value,
        "reported_unit": row.get("DMR_UNIT_DESC"),
        "statistical_base_code": row.get("STATISTICAL_BASE_CODE"),
        "statistical_base_type": base_type,
        "limit_value": limit,
        "limit_unit": row.get("LIMIT_UNIT_DESC"),
        "limit_type_code": row.get("LIMIT_TYPE_CODE"),
        "limit_begin": parse_mdy(row.get("LIMIT_BEGIN_DATE")),
        "limit_end": parse_mdy(row.get("LIMIT_END_DATE")),
        "optional_monitoring": optional,
        "enforceable_numeric": enforceable_numeric,
        "report_only": report_only,
        "nodi_code": nodi or None,
        "mechanical_exceedance": mechanical_exceedance,
        "epa_exceedance_pct": epa_pct,
        "epa_violation_code": epa_violation or None,
        "oracle_conflict": conflict,
        "scoreable": comparable and enforceable_numeric and not conflict,
    }


def gold_e_row(row: dict[str, str]) -> dict[str, Any]:
    value = parse_float(row.get("DMR_VALUE_NMBR"))
    nodi = (row.get("NODI_CODE") or "").strip()
    optional = (row.get("OPTIONAL_MONITORING_FLAG") or "").strip().upper() == "Y"
    if value is not None and not nodi:
        state = "OBSERVATION_PRESENT"
    elif nodi == "C":
        state = "ESTABLISHED_NO_DISCHARGE"
    elif nodi == "9":
        state = "ESTABLISHED_MONITORING_NOT_REQUIRED"
    elif nodi:
        state = "OTHER_DOCUMENTED_NODI"
    elif optional:
        state = "UNRESOLVED"
    else:
        state = "REQUIRED_MONITORING_MISSING"
    return {
        "permit": row.get("EXTERNAL_PERMIT_NMBR"),
        "outfall": row.get("PERM_FEATURE_NMBR"),
        "parameter_code": row.get("PARAMETER_CODE"),
        "parameter_desc": row.get("PARAMETER_DESC"),
        "monitoring_period_end": parse_mdy(row.get("MONITORING_PERIOD_END_DATE")),
        "nodi_code": nodi or None,
        "nodi_meaning": NODI_MEANING.get(nodi),
        "reported_value": value,
        "optional_monitoring": optional,
        "state": state,
    }


def gold_s_ledger() -> list[dict[str, Any]]:
    return [
        {
            "id": "S-FARM-TDS-STAGE",
            "permit": "NM0020583",
            "source_document": "farmington/final_permit.pdf",
            "native_location": "Part I, TDS Net Increase footnotes *10 and *11",
            "clause": "TDS net-increase limits begin on the effective date through 3 years from effective date (*10); then *11 limits apply from 3 years after effective date through expiration.",
            "concept_governed": "time-staged numeric limits",
            "effective_interval": "2021-12-01/2024-11-30 then 2024-12-01/2026-11-30",
            "scope": "Outfall 001 TDS net increase",
            "expected_semantic_interpretation": "FY2025 falls in the *11 interval (after 2024-12-01). Applicable numeric limits are 24,992 lbs/day and 449 mg/L, not the *10 values.",
            "oracle_disposition": "ACCEPT_STAGE_11_IN_FY2025",
        },
        {
            "id": "S-FARM-CN-SCHEDULE",
            "permit": "NM0020583",
            "source_document": "farmington/final_permit.pdf",
            "native_location": "Part I Section B Schedule of Compliance",
            "clause": "Achieve final Cyanide effluent limitations 12 months after permit effective date.",
            "concept_governed": "compliance schedule then final numeric limit",
            "effective_interval": "final limits after 2022-12-01",
            "scope": "Cyanide Outfall 001",
            "expected_semantic_interpretation": "FY2025 is after the 12-month schedule. Final cyanide limits apply. Schedule completion is not an excuse for FY2025 exceedance.",
            "oracle_disposition": "FINAL_LIMITS_APPLY",
        },
        {
            "id": "S-FARM-TRC-CONDITIONAL",
            "permit": "NM0020583",
            "source_document": "farmington/final_permit.pdf",
            "native_location": "Part I footnote *5",
            "clause": "TRC shall be monitored any time chlorine is used within the treatment plant. Facility uses UV disinfection.",
            "concept_governed": "conditional monitoring / event-dependent TRC",
            "effective_interval": "permit term",
            "scope": "Total Residual Chlorine",
            "expected_semantic_interpretation": "TRC monitoring is required when chlorine is used, not as routine UV-plant effluent monitoring. Absence of TRC values may be conditional rather than missing required monitoring.",
            "oracle_disposition": "CONDITIONAL",
        },
        {
            "id": "S-FARM-REPORT-ONLY",
            "permit": "NM0020583",
            "source_document": "farmington/final_permit.pdf",
            "native_location": "Part I effluent table Report / N/A cells",
            "clause": "Flow, TDS discharge, TDS intake, several toxics, and WET are Report rather than numeric effluent limits.",
            "concept_governed": "report-only monitoring vs enforceable numeric limit",
            "effective_interval": "permit term",
            "scope": "named Report parameters",
            "expected_semantic_interpretation": "Report-only parameters are not numeric exceedance findings.",
            "oracle_disposition": "REPORT_ONLY",
        },
        {
            "id": "S-AZTEC-WHEN-DISCHARGING",
            "permit": "NM0028762",
            "source_document": "aztec/final_permit.pdf",
            "native_location": "Part I footnote *1",
            "clause": "Monitoring frequencies marked *1 apply When discharging.",
            "concept_governed": "when-discharging / intermittent-flow monitoring obligation",
            "effective_interval": "2022-01-01/2026-12-31",
            "scope": "Outfall 001 intermittent flow",
            "expected_semantic_interpretation": "Monitoring is required when a discharge occurs. No-discharge periods do not create a missing-monitoring violation.",
            "oracle_disposition": "CONDITIONAL_ON_DISCHARGE",
        },
        {
            "id": "S-AZTEC-REPORT-ONLY",
            "permit": "NM0028762",
            "source_document": "aztec/final_permit.pdf",
            "native_location": "Part I effluent table",
            "clause": "Flow, Cyanide Total Recoverable, and TDS are Report. TSS and TRC and pH have numeric limits.",
            "concept_governed": "report-only vs numeric",
            "effective_interval": "permit term",
            "scope": "Outfall 001",
            "expected_semantic_interpretation": "Cyanide and TDS quarterly Report values are not numeric exceedances.",
            "oracle_disposition": "REPORT_ONLY",
        },
        {
            "id": "S-AZTEC-WET-SEASONAL",
            "permit": "NM0028762",
            "source_document": "aztec/final_permit.pdf",
            "native_location": "Part I footnote *4",
            "clause": "WET once per permit term during the first springtime after effective date, during irrigation season.",
            "concept_governed": "seasonal / special-study / once-per-term monitoring",
            "effective_interval": "first spring after 2022-01-01",
            "scope": "WET Ceriodaphnia dubia and Pimephales promelas",
            "expected_semantic_interpretation": "FY2025 is not automatically a required WET monitoring year. Applicability is unresolved unless evidence shows the once-per-term test remains outstanding.",
            "oracle_disposition": "UNRESOLVED_UNLESS_EVIDENCE",
        },
        {
            "id": "S-AZTEC-DELTA-BHC",
            "permit": "NM0028762",
            "source_document": "aztec/final_permit.pdf",
            "native_location": "Part I Section B Schedule of Compliance Delta-BHC Study",
            "clause": "Submit a detailed plan to test for Delta-BHC at the source water intake within six months after the effective date.",
            "concept_governed": "special study / compliance schedule",
            "effective_interval": "plan due by 2022-07-01",
            "scope": "Delta-BHC study",
            "expected_semantic_interpretation": "This is a special-study obligation, not a routine DMR numeric limit. FY2025 DMR absence of Delta-BHC is not by itself a discharge-limit exceedance.",
            "oracle_disposition": "SPECIAL_STUDY",
        },
        {
            "id": "S-GCC-EVENT-DISCHARGE",
            "permit": "NM0000116",
            "source_document": "gcc/final_permit.pdf",
            "native_location": "Part I Section A Outfall 001 authorization",
            "clause": "Authorized to discharge storm runoffs from storage and production areas, once-through cooling water, cleaning water, and Artesian well water from Outfall 001.",
            "concept_governed": "event-dependent / conditional authorization",
            "effective_interval": "2021-06-01/2026-05-31",
            "scope": "Outfall 001",
            "expected_semantic_interpretation": "No-discharge DMR NODI C is consistent with event-dependent authorization. Monitoring is required when discharging.",
            "oracle_disposition": "CONDITIONAL_ON_DISCHARGE",
        },
        {
            "id": "S-GCC-REPORT-ONLY",
            "permit": "NM0000116",
            "source_document": "gcc/final_permit.pdf",
            "native_location": "Part I effluent table",
            "clause": "Flow is Report. Dissolved copper and dissolved cadmium are Report. Hardness daily max is Report. TSS monthly average is Report; TSS daily max is 50 mg/L. Total aluminum and total copper have numeric limits.",
            "concept_governed": "report-only vs numeric",
            "effective_interval": "permit term including 2023 minor modification table",
            "scope": "Outfall 001",
            "expected_semantic_interpretation": "Do not treat Report parameters as numeric exceedances. TSS daily maximum 50 mg/L is enforceable when discharging.",
            "oracle_disposition": "MIXED_NUMERIC_AND_REPORT",
        },
        {
            "id": "S-GCC-WET-FIRST-DISCHARGE",
            "permit": "NM0000116",
            "source_document": "gcc/final_permit.pdf",
            "native_location": "Part I footnote (2)",
            "clause": "Perform WET testing at first discharge. Frequency Once/5 years.",
            "concept_governed": "event-triggered special monitoring",
            "effective_interval": "first discharge then once/5 years",
            "scope": "WET",
            "expected_semantic_interpretation": "WET is not a monthly DMR numeric limit. Missing monthly WET is not a numeric exceedance.",
            "oracle_disposition": "EVENT_TRIGGERED",
        },
        {
            "id": "S-SOURCE-AUTHORITY",
            "permit": "ALL",
            "source_document": "permits vs statement_of_basis/fact_sheet",
            "native_location": "cover pages vs SOB/fact sheet",
            "clause": "Effluent limitations and monitoring requirements are set forth in the permit Parts. Fact sheets/statements of basis explain the basis for those conditions.",
            "concept_governed": "operative permit condition vs supporting rationale",
            "effective_interval": "FY2025",
            "scope": "all facilities",
            "expected_semantic_interpretation": "Operative obligations ground in permit Parts I/II. Fact sheet/SOB text is supporting rationale, not an independent effluent limit.",
            "oracle_disposition": "AUTHORITY_HIERARCHY",
        },
    ]


def copy_permits() -> list[dict[str, str]]:
    inventory = []
    for pid, meta in PERMITS.items():
        src = RAW / "permits" / meta["folder"]
        dest = PART / "sources" / meta["folder"]
        dest.mkdir(parents=True, exist_ok=True)
        for pdf in sorted(src.glob("*.pdf")):
            shutil.copy2(pdf, dest / pdf.name)
            inventory.append(
                {
                    "permit": pid,
                    "path": f"sources/{meta['folder']}/{pdf.name}",
                    "sha256": sha256_file(dest / pdf.name),
                    "bytes": str((dest / pdf.name).stat().st_size),
                    "origin": "epa.gov official permit package",
                }
            )
        text_src = RAW / "permit_text" / meta["folder"]
        text_dest = EVAL / "permit_text" / meta["folder"]
        if text_src.exists():
            if text_dest.exists():
                shutil.rmtree(text_dest)
            shutil.copytree(text_src, text_dest)
    return inventory


def write_purposes() -> None:
    dest = PART / "purposes"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "visible_a.md").write_text(
        """# Purpose A — applicable discharge limits

For Federal FY2025 (2024-10-01 through 2025-09-30 inclusive), determine which enforceable numeric discharge limit applies to each relevant facility, discharge point, parameter, and monitoring period for which we have reported measurements. Determine whether each available reported measurement exceeds the applicable limit. Distinguish enforceable numeric limits from report-only monitoring or monitoring for which no numeric compliance comparison is applicable. Preserve uncertainty where applicability cannot be established from the available evidence.

Write purpose_ir/a/output.json as a JSON object with:
- purpose: applicable_discharge_limits
- rows: list of objects describing the evaluated measurement/limit pairs
- unresolved: list of cases whose applicability cannot be established
"""
    )
    (dest / "visible_b.md").write_text(
        """# Purpose B — monitoring obligations

For Federal FY2025, determine which monitoring requirements were actually applicable for the selected facilities, including requirements that depend on discharge occurrence, season, permit year, special studies, event conditions, or other permit conditions. For each evaluated requirement, determine whether the evidence establishes that monitoring was required, establishes that it was not required, or leaves applicability unresolved.

Write purpose_ir/b/output.json as a JSON object with:
- purpose: monitoring_obligations
- rows: list of evaluated monitoring requirements and their applicability
- unresolved: list of requirements whose applicability cannot be established
"""
    )
    (dest / "visible_c.md").write_text(
        """# Purpose C — missing-evidence semantics

For Federal FY2025 monitoring expectations without an ordinary numeric reported result, determine what the available evidence establishes. Distinguish documented no-discharge periods, periods where conditional monitoring was not required, other documented no-data states, required monitoring that appears to lack adequate evidence, and cases that remain unresolved. Do not treat missing data by itself as evidence of compliance or violation.

Write purpose_ir/c/output.json as a JSON object with:
- purpose: missing_evidence_semantics
- rows: list of evaluated no-result / NODI / missing-evidence cases and the established state
- unresolved: list of cases that remain unresolved
"""
    )


def write_purpose_d() -> None:
    (EVAL / "purpose_d.md").write_text(
        """# Purpose D — held-out compliance follow-up

Identify FY2025 facility/discharge-point/parameter/monitoring-period combinations requiring compliance follow-up because either:

1. an enforceable applicable numeric limit was exceeded, or
2. monitoring was required but the available evidence does not adequately establish the required observation.

Exclude report-only measurements from numeric exceedance findings. Exclude periods where the evidence establishes that monitoring was legitimately not required or that there was no discharge when that removes the monitoring obligation. Preserve unresolved cases separately rather than classifying them automatically as violations.

Write purpose_ir/d/output.json and 08_outputs/d.json as a JSON object with:
- purpose: compliance_follow_up
- follow_up: list of combinations requiring follow-up, each with reason exceedance | missing_required_monitoring
- unresolved: list of cases preserved as unresolved
- excluded: list of cases excluded because report-only, not required, or no discharge
"""
    )


def main() -> None:
    dmr_src = RAW / "structured" / "unpacked" / "NM_FY2025_NPDES_DMRS.csv"
    lim_src = RAW / "structured" / "unpacked" / "NM_FY2025_NPDES_LIMITS.csv"
    vio_src = RAW / "structured" / "violations" / "NM_NPDES_EFF_VIOLATIONS.csv"
    dmr_header, dmr_rows = filter_csv(dmr_src, "EXTERNAL_PERMIT_NMBR")
    lim_header, lim_rows = filter_csv(lim_src, "EXTERNAL_PERMIT_NMBR")
    vio_header, vio_rows = filter_csv(vio_src, "NPDES_ID")

    missing_keep = [c for c in DMR_KEEP if c not in dmr_header]
    missing_remove = [c for c in DMR_REMOVE if c not in dmr_header]
    if missing_keep or missing_remove:
        raise RuntimeError(f"column mismatch keep={missing_keep} remove={missing_remove}")

    participant_dmr = [{k: r.get(k, "") for k in DMR_KEEP} for r in dmr_rows]
    write_csv(PART / "sources" / "structured" / "dmr_measurements.csv", DMR_KEEP, participant_dmr)
    write_csv(PART / "sources" / "structured" / "permit_limits.csv", lim_header, lim_rows)
    write_csv(EVAL / "structured" / "dmr_full.csv", dmr_header, dmr_rows)
    write_csv(EVAL / "structured" / "permit_limits_full.csv", lim_header, lim_rows)
    write_csv(EVAL / "structured" / "effluent_violations.csv", vio_header, vio_rows)

    suit = suitability(dmr_rows, lim_rows)
    gold_m = [gold_m_row(r) for r in dmr_rows]
    gold_e = [gold_e_row(r) for r in dmr_rows]
    gold_s = gold_s_ledger()
    conflicts = [r for r in gold_m if r["oracle_conflict"]]
    inventory = copy_permits()
    write_purposes()
    write_purpose_d()

    column_manifest = {
        "dmr_source": "ECHO ICIS-NPDES NM_FY2025_NPDES_DMRS.csv",
        "limits_source": "ECHO ICIS-NPDES NM_FY2025_NPDES_LIMITS.csv",
        "violations_source": "ECHO ICIS-NPDES NM_NPDES_EFF_VIOLATIONS.csv (evaluator-only)",
        "participant_dmr_columns_kept": DMR_KEEP,
        "participant_dmr_columns_removed": DMR_REMOVE,
        "removal_rule": "Remove answer labels, not evidence.",
        "removed_reason": {
            "REPORTED_EXCURSION_NMBR": "system-generated excursion total / compliance label",
            "DAYS_LATE": "system-generated lateness",
            "EXCEEDENCE_PCT": "precomputed exceedance percent",
            "NPDES_VIOLATION_ID": "violation identifier",
            "VIOLATION_CODE": "violation code",
            "RNC_DETECTION_CODE": "RNC detection label",
            "RNC_DETECTION_DATE": "RNC detection label date",
            "RNC_RESOLUTION_CODE": "RNC resolution label",
            "RNC_RESOLUTION_DATE": "RNC resolution label date",
        },
        "limits_columns": "all native limit/monitoring-requirement columns retained for participant",
        "violations_file": "entire file evaluator-only",
    }

    source_manifest = {
        "domain": "EPA NPDES individual permit compliance",
        "jurisdiction": "New Mexico",
        "period": {"label": "Federal FY2025", "start": FY_START, "end": FY_END},
        "facilities": PERMITS,
        "structured_origin": {
            "dmr_limits_zip": "https://echo.epa.gov/files/echodownloads/NPDES_by_state_year/NM_FY2025_NPDES_DMRS_LIMITS.zip",
            "violations_zip": "https://echo.epa.gov/files/echodownloads/NPDES_by_state_year/NM_NPDES_EFF_VIOLATIONS.zip",
        },
        "permit_files": inventory,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    (PART / "sources" / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2) + "\n")

    (EVAL / "gold_m.json").write_text(
        json.dumps(
            {
                "n_rows": len(gold_m),
                "n_scoreable": sum(1 for r in gold_m if r["scoreable"]),
                "n_oracle_conflict": len(conflicts),
                "n_mechanical_exceedance": sum(1 for r in gold_m if r["mechanical_exceedance"] is True),
                "rows": gold_m,
            },
            indent=2,
        )
        + "\n"
    )
    (EVAL / "gold_s.json").write_text(json.dumps({"clauses": gold_s}, indent=2) + "\n")
    (EVAL / "gold_e.json").write_text(
        json.dumps(
            {
                "n_rows": len(gold_e),
                "by_state": dict(Counter(r["state"] for r in gold_e)),
                "rows": gold_e,
            },
            indent=2,
        )
        + "\n"
    )
    (MANIFESTS / "column_keep_remove.json").write_text(json.dumps(column_manifest, indent=2) + "\n")
    (MANIFESTS / "suitability.json").write_text(json.dumps(suit, indent=2) + "\n")
    (MANIFESTS / "facility_selection.json").write_text(
        json.dumps(
            {
                "selected": list(PERMITS),
                "optional_substitute_unused": OPTIONAL_SUBSTITUTE,
                "substituted": False,
            },
            indent=2,
        )
        + "\n"
    )

    print(json.dumps({
        "dmr_rows": len(dmr_rows),
        "limit_rows": len(lim_rows),
        "gold_m_scoreable": sum(1 for r in gold_m if r["scoreable"]),
        "oracle_conflicts": len(conflicts),
        "gold_e_states": dict(Counter(r["state"] for r in gold_e)),
        "suitability_dmr": {k: v["fy2025_dmr_rows"] for k, v in suit.items() if k.startswith("NM")},
    }, indent=2))


if __name__ == "__main__":
    main()
