"""Compile harbor towing billing world from sources and purpose."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from research.semantic_integration.core.origins import ConstructionOrigin


def construct(source, world, purpose):
    text = RoleType.TEXT
    real = RoleType.REAL

    world.declare_relation(
        "job",
        [
            Role("job_id", text),
            Role("vessel_id", text),
            Role("berth", text),
            Role("start_time", text),
            Role("end_time", text),
            Role("service_code", text),
            Role("billed_hours", text),
            Role("comment", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "vessel",
        [
            Role("vessel_id", text),
            Role("vessel_class", text),
            Role("home_port", text),
            Role("display_name", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "service_rate",
        [
            Role("service_code", text),
            Role("name", text),
            Role("rate_per_hour", real),
            Role("minimum_hours", real),
        ],
        scope="WORLD",
    )

    world.declare_relation(
        "job_billing_rate",
        [
            Role("job_id", text),
            Role("billing_service_code", text),
            Role("rate_per_hour", real),
            Role("rate_basis", text),
        ],
        scope="PURPOSE",
    )
    world.declare_relation(
        "job_billable_hours",
        [
            Role("job_id", text),
            Role("hours", real),
            Role("hours_basis", text),
        ],
        scope="PURPOSE",
    )
    world.declare_relation(
        "job_charge",
        [
            Role("job_id", text),
            Role("charge_amount", real),
            Role("charge_basis", text),
        ],
        scope="PURPOSE",
    )

    rates: dict[str, dict] = {}
    for row in source.rows("rate_card.csv"):
        code = row["service_code"]
        rates[code] = row
        loc = f"service_code={code}"
        world.assert_tuple(
            "service_rate",
            {
                "service_code": code,
                "name": row["name"],
                "rate_per_hour": float(row["rate_per_hour"]),
                "minimum_hours": float(row["minimum_hours"]),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("rate_card.csv", loc),
        )

    for row in source.rows("vessels.csv"):
        vid = row["vessel_id"]
        loc = f"vessel_id={vid}"
        world.assert_tuple(
            "vessel",
            {
                "vessel_id": vid,
                "vessel_class": row["class"],
                "home_port": row["home_port"],
                "display_name": row["display_name"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("vessels.csv", loc),
        )

    jobs: list[dict] = []
    for row in source.rows("jobs.csv"):
        jid = row["job_id"]
        loc = f"job_id={jid}"
        world.assert_tuple(
            "job",
            {
                "job_id": jid,
                "vessel_id": row["vessel_id"],
                "berth": row["berth"],
                "start_time": row["start"],
                "end_time": row["end"],
                "service_code": row["service_code"],
                "billed_hours": row.get("billed_hours") or "",
                "comment": row.get("comment") or "",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("jobs.csv", loc),
        )
        jobs.append(row)

    def parse_dt(value: str) -> datetime:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")

    def applicable_rate(service_code: str) -> tuple[str, float, str]:
        if service_code == "ASST":
            escort = rates["ESCORT"]
            return (
                "ESCORT",
                float(escort["rate_per_hour"]),
                "service_conditions.txt §4: ASST billed using ESCORT rate_card row",
            )
        if service_code == "STBY":
            stby = rates["STBY"]
            return (
                "STBY",
                float(stby["rate_per_hour"]) * 0.5,
                "service_conditions.txt §3: STBY at 50% of rate_card STBY rate",
            )
        row = rates[service_code]
        return (
            service_code,
            float(row["rate_per_hour"]),
            f"rate_card.csv service_code={service_code}",
        )

    def minimum_hours(service_code: str) -> float:
        if service_code == "ASST":
            return float(rates["ESCORT"]["minimum_hours"])
        return float(rates[service_code]["minimum_hours"])

    vessel_day_hours: dict[tuple[str, str], float] = defaultdict(float)
    job_hours: dict[str, float] = {}
    for row in jobs:
        jid = row["job_id"]
        raw = (row.get("billed_hours") or "").strip()
        if not raw:
            continue
        hours = float(raw)
        job_hours[jid] = hours
        start = parse_dt(row["start"])
        vessel_day_hours[(row["vessel_id"], start.date().isoformat())] += hours

    vessel_day_ot: dict[tuple[str, str], float] = {}
    for key, total in vessel_day_hours.items():
        if total > 8:
            vessel_day_ot[key] = total - 8

    for row in jobs:
        jid = row["job_id"]
        service_code = row["service_code"]
        berth = row["berth"]
        start = parse_dt(row["start"])
        raw_hours = (row.get("billed_hours") or "").strip()

        if not raw_hours:
            purpose.unresolved(
                "blank_billed_hours",
                relation="job",
                subject={"job_id": jid},
                reason=(
                    "service_conditions.txt §5: blank billed_hours is not an "
                    "established billable quantity"
                ),
                grounding_ref="service_conditions.txt",
            )
            continue

        if berth == "B12" and start.hour >= 18:
            purpose.unresolved(
                "b12_after_hours_no_emergency_docs",
                relation="job",
                subject={"job_id": jid, "berth": berth, "start_time": row["start"]},
                reason=(
                    "berth_notice.txt: B12 commercial towing not permitted after "
                    "18:00 without documented emergency; no emergency log attached"
                ),
                grounding_ref="berth_notice.txt",
            )
            continue

        billing_code, rate, rate_basis = applicable_rate(service_code)
        world.assert_tuple(
            "job_billing_rate",
            {
                "job_id": jid,
                "billing_service_code": billing_code,
                "rate_per_hour": rate,
                "rate_basis": rate_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

        hours = float(raw_hours)
        min_h = minimum_hours(service_code)
        billable = max(hours, min_h)
        hours_basis = f"billed_hours={hours}"
        if billable > hours:
            hours_basis += f"; minimum_hours={min_h} from rate_card"

        world.assert_tuple(
            "job_billable_hours",
            {
                "job_id": jid,
                "hours": billable,
                "hours_basis": hours_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

        vessel_key = (row["vessel_id"], start.date().isoformat())
        day_total = vessel_day_hours[vessel_key]
        ot_pool = vessel_day_ot.get(vessel_key, 0.0)
        if ot_pool > 0 and day_total > 0:
            job_ot_share = ot_pool * (hours / day_total)
            regular_share = billable - job_ot_share
            charge = regular_share * rate + job_ot_share * rate * 1.5
            charge_basis = (
                f"service_conditions.txt §2: vessel {row['vessel_id']} day total "
                f"{day_total}h with {ot_pool}h overtime; job share "
                f"{regular_share:.4g}h regular + {job_ot_share:.4g}h at 1.5x "
                f"@ {rate}/hr"
            )
        else:
            charge = billable * rate
            charge_basis = f"{billable}h @ {rate}/hr ({rate_basis})"

        world.assert_tuple(
            "job_charge",
            {
                "job_id": jid,
                "charge_amount": round(charge, 2),
                "charge_basis": charge_basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

    purpose.require_numeric(
        "charge_amount_numeric",
        relation="job_charge",
        field="charge_amount",
        per="job_id",
    )
    purpose.require_unique(
        "one_charge_per_job",
        per="job_id",
        candidates="job_charge",
        cardinality="ZERO_OR_ONE",
    )
