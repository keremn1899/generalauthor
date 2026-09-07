"""Compile makerspace checkout evidence into a grounded World."""

from __future__ import annotations

from datetime import datetime

AFTER_HOURS_START = 21
AFTER_HOURS_MULTIPLIER = 1.5


def construct(source, world, purpose):
    # --- WORLD: members ---
    world.declare_relation(
        "member",
        [Role("member_id", RoleType.TEXT), Role("name", RoleType.TEXT)],
        scope="WORLD",
    )
    for row in source.rows("members.csv"):
        mid = row["member_id"]
        world.add_referent(f"member:{mid}", label=row.get("name", ""))
        world.assert_tuple(
            "member",
            {"member_id": mid, "name": row.get("name", "")},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("members.csv", f"member_id={mid}"),
        )

    # --- WORLD: tools ---
    world.declare_relation(
        "tool",
        [
            Role("tool_id", RoleType.TEXT),
            Role("name", RoleType.TEXT),
            Role("cert_required", RoleType.TEXT),
            Role("hourly_fee", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    for row in source.rows("tools.csv"):
        tid = row["tool_id"]
        world.add_referent(f"tool:{tid}", label=row.get("name", ""))
        world.assert_tuple(
            "tool",
            {
                "tool_id": tid,
                "name": row.get("name", ""),
                "cert_required": row.get("cert_required") or "",
                "hourly_fee": row.get("hourly_fee", ""),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("tools.csv", f"tool_id={tid}"),
        )

    # --- WORLD: checkouts ---
    world.declare_relation(
        "checkout",
        [
            Role("checkout_id", RoleType.TEXT),
            Role("member_id", RoleType.TEXT),
            Role("tool_id", RoleType.TEXT),
            Role("out", RoleType.TEXT),
            Role("in", RoleType.TEXT),
            Role("note", RoleType.TEXT),
            Role("hours_marked", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    for row in source.rows("checkouts.csv"):
        cid = row["checkout_id"]
        world.add_referent(f"checkout:{cid}", label=cid)
        world.assert_tuple(
            "checkout",
            {
                "checkout_id": cid,
                "member_id": row.get("member_id", ""),
                "tool_id": row.get("tool_id", ""),
                "out": row.get("out", ""),
                "in": row.get("in", ""),
                "note": row.get("note") or "",
                "hours_marked": row.get("hours_marked", ""),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("checkouts.csv", f"checkout_id={cid}"),
        )

    # --- WORLD: member certifications (split from comma-separated certs field) ---
    world.declare_relation(
        "member_cert",
        [Role("member_id", RoleType.TEXT), Role("cert", RoleType.TEXT)],
        scope="WORLD",
    )
    for row in source.rows("members.csv"):
        mid = row["member_id"]
        certs_raw = (row.get("certs") or "").strip()
        if not certs_raw:
            continue
        for cert in certs_raw.split(","):
            cert = cert.strip()
            if not cert:
                continue
            world.assert_tuple(
                "member_cert",
                {"member_id": mid, "cert": cert},
                origin=ConstructionOrigin.MECHANICAL,
                grounding=source.grounding("members.csv", f"member_id={mid}"),
            )

    # --- WORLD: tool identity remap (ADR) ---
    world.declare_relation(
        "tool_identity_remap",
        [Role("from_tool_id", RoleType.TEXT), Role("to_tool_id", RoleType.TEXT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "tool_identity_remap",
        {"from_tool_id": "L1", "to_tool_id": "LASER-A"},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("adr.txt", "L1=LASER-A"),
    )

    # --- PURPOSE: shop policy (from shop_rules.txt) ---
    world.declare_relation(
        "after_hours_rule",
        [Role("start_hour", RoleType.TEXT), Role("multiplier", RoleType.TEXT)],
        scope="PURPOSE",
    )
    world.assert_tuple(
        "after_hours_rule",
        {"start_hour": str(AFTER_HOURS_START), "multiplier": str(AFTER_HOURS_MULTIPLIER)},
        origin=ConstructionOrigin.ADJUDICATED,
    )

    world.declare_relation(
        "note_interpretation",
        [Role("note", RoleType.TEXT), Role("meaning", RoleType.TEXT)],
        scope="PURPOSE",
    )
    world.assert_tuple(
        "note_interpretation",
        {
            "note": "HOLD",
            "meaning": "tool parked in bay; not an extra billed day",
        },
        origin=ConstructionOrigin.ADJUDICATED,
    )

    # --- PURPOSE: resolved tool id per checkout ---
    world.declare_relation(
        "checkout_resolved_tool",
        [Role("checkout_id", RoleType.TEXT), Role("resolved_tool_id", RoleType.TEXT)],
        scope="PURPOSE",
    )

    tools = {row["tool_id"]: row for row in source.rows("tools.csv")}
    remaps = {row["from_tool_id"]: row["to_tool_id"] for row in _remap_rows(world)}
    member_certs = _member_certs(source)

    for row in source.rows("checkouts.csv"):
        cid = row["checkout_id"]
        raw_tool = row.get("tool_id", "")
        resolved = remaps.get(raw_tool, raw_tool)
        world.assert_tuple(
            "checkout_resolved_tool",
            {"checkout_id": cid, "resolved_tool_id": resolved},
            origin=ConstructionOrigin.MECHANICAL,
        )

    # --- PURPOSE: authorization ---
    world.declare_relation(
        "checkout_authorization",
        [
            Role("checkout_id", RoleType.TEXT),
            Role("authorized", RoleType.TEXT),
            Role("basis", RoleType.TEXT),
        ],
        scope="PURPOSE",
    )
    for row in source.rows("checkouts.csv"):
        cid = row["checkout_id"]
        mid = row.get("member_id", "")
        raw_tool = row.get("tool_id", "")
        resolved = remaps.get(raw_tool, raw_tool)
        tool_row = tools.get(resolved)
        if tool_row is None:
            world.assert_tuple(
                "checkout_authorization",
                {
                    "checkout_id": cid,
                    "authorized": "no",
                    "basis": f"resolved tool {resolved} not in tools inventory",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )
            continue
        cert_required = (tool_row.get("cert_required") or "").strip()
        if not cert_required:
            world.assert_tuple(
                "checkout_authorization",
                {
                    "checkout_id": cid,
                    "authorized": "yes",
                    "basis": "no certification required for tool",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )
            continue
        held = member_certs.get(mid, set())
        if cert_required in held:
            basis = f"member holds required certification {cert_required}"
            if raw_tool != resolved:
                basis += f"; tool_id {raw_tool} remapped to {resolved}"
            world.assert_tuple(
                "checkout_authorization",
                {"checkout_id": cid, "authorized": "yes", "basis": basis},
                origin=ConstructionOrigin.ADJUDICATED,
            )
        else:
            world.assert_tuple(
                "checkout_authorization",
                {
                    "checkout_id": cid,
                    "authorized": "no",
                    "basis": f"missing required certification {cert_required}",
                },
                origin=ConstructionOrigin.ADJUDICATED,
            )

    # --- PURPOSE: fees ---
    world.declare_relation(
        "checkout_fee",
        [
            Role("checkout_id", RoleType.TEXT),
            Role("hourly_fee", RoleType.TEXT),
            Role("hours", RoleType.TEXT),
            Role("after_hours_multiplier", RoleType.TEXT),
            Role("total_fee", RoleType.TEXT),
        ],
        scope="PURPOSE",
    )
    for row in source.rows("checkouts.csv"):
        cid = row["checkout_id"]
        raw_tool = row.get("tool_id", "")
        resolved = remaps.get(raw_tool, raw_tool)
        tool_row = tools.get(resolved)
        if tool_row is None:
            continue
        hourly = float(tool_row["hourly_fee"])
        hours = float(row.get("hours_marked") or 0)
        out_text = row.get("out", "")
        multiplier = 1.0
        try:
            out_dt = datetime.strptime(out_text.strip(), "%Y-%m-%d %H:%M")
            if out_dt.hour >= AFTER_HOURS_START:
                multiplier = AFTER_HOURS_MULTIPLIER
        except ValueError:
            pass
        total = hourly * hours * multiplier
        world.assert_tuple(
            "checkout_fee",
            {
                "checkout_id": cid,
                "hourly_fee": str(hourly),
                "hours": str(hours),
                "after_hours_multiplier": str(multiplier),
                "total_fee": str(total),
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

    # --- PURPOSE: unresolved note / coverage gaps ---
    for row in source.rows("checkouts.csv"):
        note = (row.get("note") or "").strip()
        if note == "PENDING":
            purpose.unresolved(
                "pending_note_meaning",
                relation="checkout",
                subject={"checkout_id": row["checkout_id"], "note": note},
                reason="shop_rules.txt does not define checkout note PENDING",
            )

    purpose.require_materializable("checkout_authorization_populated", relation="checkout_authorization")
    purpose.require_materializable("checkout_fee_populated", relation="checkout_fee")
    purpose.require_numeric("fee_total_numeric", relation="checkout_fee", field="total_fee", per="checkout_id")
    purpose.require_interpreted(
        "checkout_note_interpreted",
        relation="checkout",
        field="note",
        known=["", "HOLD"],
        per="checkout_id",
    )


def _member_certs(source) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for row in source.rows("members.csv"):
        mid = row["member_id"]
        certs_raw = (row.get("certs") or "").strip()
        if not certs_raw:
            out[mid] = set()
            continue
        out[mid] = {c.strip() for c in certs_raw.split(",") if c.strip()}
    return out


def _remap_rows(world):
    return world.relation_rows("tool_identity_remap")
