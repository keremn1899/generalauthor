"""Grounded World for municipal seed grant award analysis."""

from __future__ import annotations

from collections import defaultdict

from research.semantic_integration.core.origins import ConstructionOrigin


def construct(source, world, purpose):
    # --- Referents ---
    for org in source.rows("orgs.json"):
        org_id = org["org_id"]
        world.add_referent(
            org_id,
            label=org.get("legal_name", org_id),
            observations=[source.observation("orgs.json", f"org_id={org_id}")],
        )

    for row in source.rows("awards.csv"):
        award_id = row["award_id"]
        world.add_referent(
            award_id,
            label=f"award {award_id}",
            observations=[source.observation("awards.csv", f"award_id={award_id}")],
        )

    # --- Relations ---
    world.declare_relation(
        "organization",
        [
            Role("org_id", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
            Role("ein", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "award",
        [
            Role("award_id", RoleType.TEXT),
            Role("org_id", RoleType.TEXT),
            Role("program", RoleType.TEXT),
            Role("amount", RoleType.TEXT),
            Role("start", RoleType.TEXT),
            Role("end", RoleType.TEXT),
            Role("status_code", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "disbursement",
        [
            Role("award_id", RoleType.TEXT),
            Role("date", RoleType.TEXT),
            Role("amount", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "status_legend",
        [
            Role("status_code", RoleType.TEXT),
            Role("meaning", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "program_cash_match",
        [
            Role("program", RoleType.TEXT),
            Role("match_required", RoleType.TEXT),
            Role("match_rate", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "award_cash_match_rule",
        [
            Role("award_id", RoleType.TEXT),
            Role("program", RoleType.TEXT),
            Role("match_required", RoleType.TEXT),
            Role("match_rate", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "remaining_balance",
        [
            Role("award_id", RoleType.TEXT),
            Role("award_amount", RoleType.TEXT),
            Role("disbursed_total", RoleType.TEXT),
            Role("remaining", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "status_interpretation",
        [
            Role("award_id", RoleType.TEXT),
            Role("status_code", RoleType.TEXT),
            Role("meaning", RoleType.TEXT),
        ],
        scope="WORLD",
    )

    origin = ConstructionOrigin.MECHANICAL

    # --- Organizations ---
    for org in source.rows("orgs.json"):
        org_id = org["org_id"]
        world.assert_tuple(
            "organization",
            {
                "org_id": org_id,
                "legal_name": org["legal_name"],
                "ein": org["ein"],
            },
            origin=origin,
            grounding=source.grounding("orgs.json", f"org_id={org_id}"),
        )

    # --- Awards ---
    awards = source.rows("awards.csv")
    for row in awards:
        award_id = row["award_id"]
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
            origin=origin,
            grounding=source.grounding("awards.csv", f"award_id={award_id}"),
        )

    # --- Disbursements ---
    disbursements = source.rows("disbursements.csv")
    for idx, row in enumerate(disbursements, start=1):
        loc = f"award_id={row['award_id']},date={row['date']}"
        world.assert_tuple(
            "disbursement",
            {
                "award_id": row["award_id"],
                "date": row["date"],
                "amount": row["amount"],
            },
            origin=origin,
            grounding=source.grounding("disbursements.csv", loc),
        )

    # --- Status legend (partial, from status_fragment.txt) ---
    legend_entries = [
        ("A", "Active"),
        ("C", "Closed"),
    ]
    for code, meaning in legend_entries:
        world.assert_tuple(
            "status_legend",
            {"status_code": code, "meaning": meaning},
            origin=origin,
            grounding=source.grounding("status_fragment.txt", f"status_code={code}"),
        )

    # --- Program cash-match rules (from program_rules.txt) ---
    program_rules = [
        ("SEED-CORE", "yes", "0.20"),
        ("SEED-FAST", "no", "0"),
    ]
    for program, required, rate in program_rules:
        world.assert_tuple(
            "program_cash_match",
            {
                "program": program,
                "match_required": required,
                "match_rate": rate,
            },
            origin=origin,
            grounding=source.grounding("program_rules.txt", f"program={program}"),
        )

    # --- Per-award cash-match rule application ---
    program_match = {p: (r, rate) for p, r, rate in program_rules}
    for row in awards:
        award_id = row["award_id"]
        program = row["program"]
        required, rate = program_match.get(program, ("unknown", ""))
        world.assert_tuple(
            "award_cash_match_rule",
            {
                "award_id": award_id,
                "program": program,
                "match_required": required,
                "match_rate": rate,
            },
            origin=origin,
            grounding=source.grounding("awards.csv", f"award_id={award_id}"),
        )

    # --- Remaining balances (award amount minus sum of disbursements) ---
    disbursed_by_award: dict[str, float] = defaultdict(float)
    for row in disbursements:
        disbursed_by_award[row["award_id"]] += float(row["amount"])

    for row in awards:
        award_id = row["award_id"]
        award_amount = float(row["amount"])
        disbursed_total = disbursed_by_award.get(award_id, 0.0)
        remaining = award_amount - disbursed_total
        world.assert_tuple(
            "remaining_balance",
            {
                "award_id": award_id,
                "award_amount": str(int(award_amount)),
                "disbursed_total": str(int(disbursed_total)),
                "remaining": str(int(remaining)),
            },
            origin=origin,
            grounding=source.grounding("awards.csv", f"award_id={award_id}"),
        )

    # --- Status interpretations where legend provides meaning ---
    legend_map = {code: meaning for code, meaning in legend_entries}
    for row in awards:
        award_id = row["award_id"]
        status_code = row["status_code"]
        if status_code not in legend_map:
            continue
        world.assert_tuple(
            "status_interpretation",
            {
                "award_id": award_id,
                "status_code": status_code,
                "meaning": legend_map[status_code],
            },
            origin=origin,
            grounding=source.grounding(
                "status_fragment.txt", f"status_code={status_code}"
            ),
        )

    # --- Purpose: insufficiency for unlisted status codes ---
    known_status_codes = list(legend_map.keys())
    purpose.require_interpreted(
        "award_status_from_legend",
        relation="award",
        field="status_code",
        known=known_status_codes,
        per="award_id",
    )

    # --- Purpose: numeric remaining balances ---
    purpose.require_numeric(
        "remaining_balance_amount",
        relation="remaining_balance",
        field="remaining",
        per="award_id",
    )
    purpose.require_numeric(
        "remaining_balance_award_amount",
        relation="remaining_balance",
        field="award_amount",
        per="award_id",
    )
    purpose.require_numeric(
        "remaining_balance_disbursed_total",
        relation="remaining_balance",
        field="disbursed_total",
        per="award_id",
    )

    # --- Purpose: explicit unresolved cases ---
    for row in awards:
        award_id = row["award_id"]
        status_code = row["status_code"]
        if status_code not in legend_map:
            purpose.unresolved(
                "status_not_in_legend",
                relation="award",
                subject={"award_id": award_id, "status_code": status_code},
                reason=(
                    "Office status legend is partial; this code is used by finance "
                    "and is not listed in the packet excerpt."
                ),
                grounding_ref=f"status_fragment.txt:status_code={status_code}",
            )

    for row in awards:
        award_id = row["award_id"]
        program = row["program"]
        if program != "SEED-CORE":
            continue
        purpose.unresolved(
            "cash_match_waiver_unknown",
            relation="award_cash_match_rule",
            subject={"award_id": award_id, "program": program},
            reason=(
                "SEED-CORE requires a 20% cash match unless a written waiver is on "
                "file; this packet does not attach waiver letters and absence here "
                "is not a denial that a waiver exists elsewhere."
            ),
            grounding_ref="program_rules.txt:program=SEED-CORE",
        )
