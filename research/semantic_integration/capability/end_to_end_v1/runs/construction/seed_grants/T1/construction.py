"""Grounded World for municipal seed grant award balances and obligations."""

from __future__ import annotations

from collections import defaultdict

from taskview import RelationMode, Role, RoleType


def construct(source, world, purpose):
    ref = RoleType.REFERENT
    text = RoleType.TEXT

    world.declare_relation(
        "organization",
        [Role("org_id", text), Role("legal_name", text), Role("ein", text)],
        scope="WORLD",
    )
    world.declare_relation(
        "award",
        [
            Role("award_id", text),
            Role("org_id", text),
            Role("program", text),
            Role("amount", text),
            Role("start", text),
            Role("end", text),
            Role("status_code", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "disbursement",
        [Role("award_id", text), Role("date", text), Role("amount", text)],
        scope="WORLD",
    )
    world.declare_relation(
        "status_legend_entry",
        [Role("code", text), Role("meaning", text)],
        scope="WORLD",
    )
    world.declare_relation(
        "program_match_rule",
        [
            Role("program", text),
            Role("match_required", text),
            Role("match_rate", text),
            Role("waiver_possible", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "award_remaining_balance",
        [
            Role("award_id", text),
            Role("award_amount", text),
            Role("disbursed_total", text),
            Role("remaining_balance", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "award_match_obligation",
        [
            Role("award_id", text),
            Role("program", text),
            Role("match_required", text),
            Role("match_rate", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "award_status_label",
        [Role("award_id", text), Role("status_code", text), Role("status_label", text)],
        scope="WORLD",
    )

    for row in source.rows("orgs.json"):
        org_id = row["org_id"]
        world.add_referent(org_id, label=row.get("legal_name", org_id))
        loc = f"org_id={org_id}"
        world.assert_tuple(
            "organization",
            {
                "org_id": org_id,
                "legal_name": row["legal_name"],
                "ein": row["ein"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("orgs.json", loc),
        )

    for row in source.rows("awards.csv"):
        award_id = row["award_id"]
        world.add_referent(award_id, label=award_id)
        loc = f"award_id={award_id}"
        world.assert_tuple(
            "award",
            {
                "award_id": award_id,
                "org_id": row["org_id"],
                "program": row["program"],
                "amount": row["amount"],
                "start": row["start"],
                "end": row["end"],
                "status_code": row["status_code"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("awards.csv", loc),
        )

    for row in source.rows("disbursements.csv"):
        award_id = row["award_id"]
        date = row["date"]
        loc = f"award_id={award_id},date={date}"
        world.assert_tuple(
            "disbursement",
            {
                "award_id": award_id,
                "date": date,
                "amount": row["amount"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("disbursements.csv", loc),
        )

    legend_entries = [
        ("A", "Active"),
        ("C", "Closed"),
    ]
    for code, meaning in legend_entries:
        world.assert_tuple(
            "status_legend_entry",
            {"code": code, "meaning": meaning},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("status_fragment.txt", f"code={code}"),
        )

    match_rules = [
        ("SEED-CORE", "yes", "0.20", "yes"),
        ("SEED-FAST", "no", "0", "no"),
    ]
    for program, required, rate, waiver in match_rules:
        world.assert_tuple(
            "program_match_rule",
            {
                "program": program,
                "match_required": required,
                "match_rate": rate,
                "waiver_possible": waiver,
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("program_rules.txt", f"program={program}"),
        )

    disbursed_by_award: dict[str, float] = defaultdict(float)
    for row in source.rows("disbursements.csv"):
        disbursed_by_award[row["award_id"]] += float(row["amount"])

    rule_by_program = {program: (required, rate) for program, required, rate, _ in match_rules}

    for row in source.rows("awards.csv"):
        award_id = row["award_id"]
        program = row["program"]
        award_amount = float(row["amount"])
        disbursed_total = disbursed_by_award.get(award_id, 0.0)
        remaining = award_amount - disbursed_total
        world.assert_tuple(
            "award_remaining_balance",
            {
                "award_id": award_id,
                "award_amount": str(int(award_amount) if award_amount == int(award_amount) else award_amount),
                "disbursed_total": str(int(disbursed_total) if disbursed_total == int(disbursed_total) else disbursed_total),
                "remaining_balance": str(int(remaining) if remaining == int(remaining) else remaining),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("awards.csv", f"award_id={award_id}"),
        )

        match_required, match_rate = rule_by_program.get(program, ("unknown", "unknown"))
        world.assert_tuple(
            "award_match_obligation",
            {
                "award_id": award_id,
                "program": program,
                "match_required": match_required,
                "match_rate": match_rate,
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("program_rules.txt", f"program={program}"),
        )

        status_code = row["status_code"]
        legend = {code: meaning for code, meaning in legend_entries}
        if status_code in legend:
            world.assert_tuple(
                "award_status_label",
                {
                    "award_id": award_id,
                    "status_code": status_code,
                    "status_label": legend[status_code],
                },
                origin=ConstructionOrigin.MECHANICAL,
                grounding=source.grounding("status_fragment.txt", f"code={status_code}"),
            )

    purpose.require_numeric(
        "remaining_balance_numeric",
        relation="award_remaining_balance",
        field="remaining_balance",
        per="award_id",
    )
    purpose.require_numeric(
        "award_amount_numeric",
        relation="award_remaining_balance",
        field="award_amount",
        per="award_id",
    )
    purpose.require_interpreted(
        "award_status_interpretable",
        relation="award",
        field="status_code",
        known=["A", "C"],
        per="award_id",
    )

    for row in source.rows("awards.csv"):
        if row["program"] == "SEED-CORE":
            purpose.unresolved(
                "seed_core_waiver_unknown",
                relation="award_match_obligation",
                subject={"award_id": row["award_id"], "program": row["program"]},
                reason=(
                    "SEED-CORE requires cash match unless a written waiver is on file; "
                    "this packet does not attach waiver letters."
                ),
            )

    for row in source.rows("awards.csv"):
        if row["status_code"] not in {"A", "C"}:
            purpose.unresolved(
                "status_code_not_in_legend",
                relation="award",
                subject={"award_id": row["award_id"], "status_code": row["status_code"]},
                reason="Office status legend is partial; this code is not listed.",
            )
