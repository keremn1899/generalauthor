"""Semantic construction for harbor towing billing."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.runtime_v0.source_helpers import looks_numeric


def construct(source, world, purpose):
    ref = RoleType.REFERENT
    text = RoleType.TEXT
    real = RoleType.REAL

    world.declare_relation(
        "tow_job",
        [
            Role("job", ref),
            Role("vessel_id", text),
            Role("berth", text),
            Role("start_time", text),
            Role("end_time", text),
            Role("service_code", text),
            Role("billed_hours", text),
            Role("comment", text),
        ],
        description="Towing job records from jobs.csv.",
        scope="WORLD",
    )
    world.declare_relation(
        "vessel",
        [
            Role("vessel", ref),
            Role("vessel_class", text),
            Role("home_port", text),
            Role("display_name", text),
        ],
        description="Vessel registry from vessels.csv.",
        scope="WORLD",
    )
    world.declare_relation(
        "rate_card",
        [
            Role("service_code", text),
            Role("name", text),
            Role("rate_per_hour", real),
            Role("minimum_hours", real),
        ],
        description="Published hourly rates from rate_card.csv.",
        scope="WORLD",
    )
    world.declare_relation(
        "berth_restriction",
        [
            Role("berth", text),
            Role("restriction", text),
        ],
        description="Berth operating restrictions from berth_notice.txt.",
        scope="WORLD",
    )

    world.declare_relation(
        "effective_rate",
        [
            Role("job", ref),
            Role("rate_service_code", text),
            Role("rate_per_hour", real),
            Role("basis", text),
        ],
        description="Applicable hourly rate for a job after service conditions.",
        scope="PURPOSE",
    )
    world.declare_relation(
        "billable_hours",
        [
            Role("job", ref),
            Role("hours", real),
            Role("basis", text),
        ],
        description="Established billable hours for a job.",
        scope="PURPOSE",
    )
    world.declare_relation(
        "job_charge",
        [
            Role("job", ref),
            Role("charge", real),
            Role("basis", text),
        ],
        description="Computed charge when evidence supports confident billing.",
        scope="PURPOSE",
    )
    world.declare_relation(
        "billing_outcome",
        [
            Role("job", ref),
            Role("status", text),
            Role("reason", text),
        ],
        description="Whether a job is billable, not billable, or insufficiently evidenced.",
        scope="PURPOSE",
    )

    rates = {}
    for row in source.rows("rate_card.csv"):
        code = row["service_code"]
        rates[code] = {
            "name": row["name"],
            "rate_per_hour": float(row["rate_per_hour"]),
            "minimum_hours": float(row["minimum_hours"]),
        }
        world.assert_tuple(
            "rate_card",
            {
                "service_code": code,
                "name": row["name"],
                "rate_per_hour": float(row["rate_per_hour"]),
                "minimum_hours": float(row["minimum_hours"]),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("rate_card.csv", f"service_code={code}"),
        )

    for row in source.rows("vessels.csv"):
        vid = row["vessel_id"]
        world.add_referent(
            f"vessel:{vid}",
            label=row["display_name"],
            observations=[source.observation("vessels.csv", f"vessel_id={vid}")],
        )
        world.assert_tuple(
            "vessel",
            {
                "vessel": f"vessel:{vid}",
                "vessel_class": row["class"],
                "home_port": row["home_port"],
                "display_name": row["display_name"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("vessels.csv", f"vessel_id={vid}"),
        )

    jobs = []
    for row in source.rows("jobs.csv"):
        job_id = row["job_id"]
        world.add_referent(
            f"job:{job_id}",
            label=job_id,
            observations=[source.observation("jobs.csv", f"job_id={job_id}")],
        )
        world.assert_tuple(
            "tow_job",
            {
                "job": f"job:{job_id}",
                "vessel_id": row["vessel_id"],
                "berth": row["berth"],
                "start_time": row["start"],
                "end_time": row["end"],
                "service_code": row["service_code"],
                "billed_hours": row["billed_hours"] or "",
                "comment": row["comment"] or "",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("jobs.csv", f"job_id={job_id}"),
        )
        jobs.append(
            {
                "job_id": job_id,
                "job": f"job:{job_id}",
                "vessel_id": row["vessel_id"],
                "berth": row["berth"],
                "start": row["start"],
                "end": row["end"],
                "service_code": row["service_code"],
                "billed_hours": row["billed_hours"] or "",
                "comment": row["comment"] or "",
            }
        )

    world.assert_tuple(
        "berth_restriction",
        {
            "berth": "B12",
            "restriction": (
                "Commercial towing is not permitted after 18:00 local time "
                "except a documented emergency."
            ),
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("berth_notice.txt", "berth=B12"),
    )

    vessel_day_hours: dict[tuple[str, str], float] = defaultdict(float)
    for job in jobs:
        if not looks_numeric(job["billed_hours"]):
            continue
        day = job["start"].split()[0]
        vessel_day_hours[(job["vessel_id"], day)] += float(job["billed_hours"])

    def effective_rate_for(job):
        code = job["service_code"]
        if code == "ASST":
            escort = rates["ESCORT"]
            return (
                "ESCORT",
                escort["rate_per_hour"],
                "ASST jobs bill using the ESCORT rate_card row (service_conditions §4).",
            )
        if code == "STBY":
            base = rates["STBY"]["rate_per_hour"]
            return (
                "STBY",
                base * 0.5,
                "STBY is billed at 50% of the rate_card STBY rate (service_conditions §3).",
            )
        if code in rates:
            entry = rates[code]
            return (
                code,
                entry["rate_per_hour"],
                f"Named rate_card rate for {code} (service_conditions §1).",
            )
        return None

    def after_hours_at_b12(job):
        if job["berth"] != "B12":
            return False
        start = datetime.strptime(job["start"], "%Y-%m-%d %H:%M")
        return start.hour >= 18 or (start.hour == 17 and start.minute > 0)

    for job in jobs:
        job_ref = job["job"]
        job_id = job["job_id"]

        if not looks_numeric(job["billed_hours"]):
            purpose.unresolved(
                "blank_billed_hours",
                subject={"job": job_id},
                relation="tow_job",
                reason=(
                    "Blank billed_hours: clock time between start and end is not "
                    "an established billable quantity (service_conditions §5)."
                ),
                grounding_ref=f"jobs.csv:job_id={job_id}",
            )
            world.assert_tuple(
                "billing_outcome",
                {
                    "job": job_ref,
                    "status": "insufficient_evidence",
                    "reason": "billed_hours is blank",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )
            continue

        if after_hours_at_b12(job):
            purpose.unresolved(
                "berth_b12_after_hours",
                subject={"job": job_id, "berth": job["berth"]},
                relation="berth_restriction",
                reason=(
                    "B12 commercial towing after 18:00 requires a documented emergency; "
                    "no emergency log is attached (berth_notice.txt)."
                ),
                grounding_ref=f"berth_notice.txt:job_id={job_id}",
            )
            world.assert_tuple(
                "billing_outcome",
                {
                    "job": job_ref,
                    "status": "insufficient_evidence",
                    "reason": "B12 after-hours towing without emergency documentation",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )
            continue

        rate_info = effective_rate_for(job)
        if rate_info is None:
            purpose.unresolved(
                "unknown_service_code",
                subject={"job": job_id, "service_code": job["service_code"]},
                relation="rate_card",
                reason=f"No rate_card row for service code {job['service_code']}.",
            )
            world.assert_tuple(
                "billing_outcome",
                {
                    "job": job_ref,
                    "status": "insufficient_evidence",
                    "reason": f"unknown service code {job['service_code']}",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )
            continue

        rate_code, hourly, rate_basis = rate_info
        hours = float(job["billed_hours"])
        day = job["start"].split()[0]
        vessel_day_total = vessel_day_hours[(job["vessel_id"], day)]

        world.assert_tuple(
            "effective_rate",
            {
                "job": job_ref,
                "rate_service_code": rate_code,
                "rate_per_hour": hourly,
                "basis": rate_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )
        world.assert_tuple(
            "billable_hours",
            {
                "job": job_ref,
                "hours": hours,
                "basis": f"billed_hours from jobs.csv for {job_id}",
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

        if vessel_day_total > 8:
            regular_pool = 8.0
            prior_hours = 0.0
            for other in jobs:
                if other["vessel_id"] != job["vessel_id"]:
                    continue
                if other["start"].split()[0] != day:
                    continue
                if not looks_numeric(other["billed_hours"]):
                    continue
                if other["job_id"] == job_id:
                    break
                prior_hours += float(other["billed_hours"])

            regular_for_job = max(0.0, min(hours, regular_pool - prior_hours))
            overtime_for_job = hours - regular_for_job
            charge = regular_for_job * hourly + overtime_for_job * hourly * 1.5
            charge_basis = (
                f"{regular_for_job:g}h at {hourly:g}/hr + "
                f"{overtime_for_job:g}h overtime at 1.5x "
                f"(vessel {job['vessel_id']} day total {vessel_day_total:g}h > 8; "
                "service_conditions §2)"
            )
        else:
            charge = hours * hourly
            charge_basis = f"{hours:g}h at {hourly:g}/hr"

        world.assert_tuple(
            "job_charge",
            {
                "job": job_ref,
                "charge": round(charge, 2),
                "basis": charge_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )
        world.assert_tuple(
            "billing_outcome",
            {
                "job": job_ref,
                "status": "billable",
                "reason": charge_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

    purpose.require_materializable("tow_jobs_loaded", relation="tow_job")
    purpose.require_materializable("rates_loaded", relation="rate_card")
    purpose.require_unique(
        "one_outcome_per_job",
        per="job",
        candidates="billing_outcome",
        cardinality="ONE",
    )
    purpose.require_interpreted(
        "billing_status_known",
        relation="billing_outcome",
        field="status",
        known=["billable", "insufficient_evidence", "not_billable"],
        per="job",
    )
    purpose.require_numeric("charge_amount_numeric", relation="job_charge", field="charge", per="job")
