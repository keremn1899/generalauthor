"""Compile makerspace checkout authorization and fee world from sources."""

from __future__ import annotations

from datetime import datetime, time


def construct(source, world, purpose):
    ref = RoleType.REFERENT
    text = RoleType.TEXT

    world.declare_relation(
        "member_record",
        [Role("member", ref), Role("name", text), Role("certs", text)],
        scope="WORLD",
    )
    world.declare_relation(
        "tool_record",
        [
            Role("tool", ref),
            Role("name", text),
            Role("cert_required", text),
            Role("hourly_fee", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "checkout_record",
        [
            Role("checkout", ref),
            Role("member", ref),
            Role("tool_id", text),
            Role("out_time", text),
            Role("in_time", text),
            Role("note", text),
            Role("hours_marked", text),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "tool_identity_remap",
        [Role("from_tool_id", text), Role("to_tool", ref)],
        scope="WORLD",
    )
    world.declare_relation(
        "checkout_authorization",
        [Role("checkout", ref), Role("status", text), Role("basis", text)],
        scope="PURPOSE",
    )
    world.declare_relation(
        "checkout_fee",
        [
            Role("checkout", ref),
            Role("resolved_tool", ref),
            Role("hourly_rate", text),
            Role("hours", text),
            Role("after_hours_multiplier", text),
            Role("total_fee", text),
        ],
        scope="PURPOSE",
    )

    for row in source.rows("members.csv"):
        member_id = row["member_id"]
        world.add_referent(
            f"member:{member_id}",
            label=row.get("name") or member_id,
            observations=(source.observation("members.csv", f"member_id={member_id}"),),
        )
        world.assert_tuple(
            "member_record",
            {
                "member": f"member:{member_id}",
                "name": row.get("name") or "",
                "certs": row.get("certs") or "",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("members.csv", f"member_id={member_id}"),
        )

    tools_by_id: dict[str, dict] = {}
    for row in source.rows("tools.csv"):
        tool_id = row["tool_id"]
        tools_by_id[tool_id] = row
        world.add_referent(
            f"tool:{tool_id}",
            label=row.get("name") or tool_id,
            observations=(source.observation("tools.csv", f"tool_id={tool_id}"),),
        )
        world.assert_tuple(
            "tool_record",
            {
                "tool": f"tool:{tool_id}",
                "name": row.get("name") or "",
                "cert_required": row.get("cert_required") or "",
                "hourly_fee": row.get("hourly_fee") or "",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("tools.csv", f"tool_id={tool_id}"),
        )

    world.assert_tuple(
        "tool_identity_remap",
        {"from_tool_id": "L1", "to_tool": "tool:LASER-A"},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("adr.txt", "L1=LASER-A"),
    )

    members_by_id = {row["member_id"]: row for row in source.rows("members.csv")}
    checkouts: list[dict] = []
    for row in source.rows("checkouts.csv"):
        checkout_id = row["checkout_id"]
        member_id = row["member_id"]
        world.add_referent(
            f"checkout:{checkout_id}",
            label=checkout_id,
            observations=(source.observation("checkouts.csv", f"checkout_id={checkout_id}"),),
        )
        world.assert_tuple(
            "checkout_record",
            {
                "checkout": f"checkout:{checkout_id}",
                "member": f"member:{member_id}",
                "tool_id": row.get("tool_id") or "",
                "out_time": row.get("out") or "",
                "in_time": row.get("in") or "",
                "note": row.get("note") or "",
                "hours_marked": row.get("hours_marked") or "",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("checkouts.csv", f"checkout_id={checkout_id}"),
        )
        checkouts.append(row)

    def resolve_tool_id(raw_tool_id: str) -> str:
        if raw_tool_id == "L1":
            return "LASER-A"
        return raw_tool_id

    def member_has_cert(member_id: str, cert_required: str) -> bool:
        if not cert_required:
            return True
        certs = (members_by_id.get(member_id, {}).get("certs") or "").split(",")
        return cert_required in {item.strip() for item in certs if item.strip()}

    def after_hours_multiplier(out_time: str) -> str:
        if not out_time.strip():
            return "1"
        dt = datetime.strptime(out_time.strip(), "%Y-%m-%d %H:%M")
        if dt.time() >= time(21, 0):
            return "1.5"
        return "1"

    for row in checkouts:
        checkout_id = row["checkout_id"]
        member_id = row["member_id"]
        raw_tool_id = row.get("tool_id") or ""
        resolved = resolve_tool_id(raw_tool_id)
        tool_row = tools_by_id.get(resolved)
        cert_required = (tool_row or {}).get("cert_required") or ""

        if tool_row is None:
            purpose.unresolved(
                "checkout_tool_identity",
                relation="checkout_record",
                subject={"checkout": checkout_id, "tool_id": raw_tool_id},
                reason="No tool record or identity remap for checkout tool_id",
            )
            continue

        authorized = member_has_cert(member_id, cert_required)
        if authorized:
            status = "authorized"
            basis = "member holds required certification or none required"
        else:
            status = "unauthorized"
            basis = f"missing required certification {cert_required}"

        world.assert_tuple(
            "checkout_authorization",
            {
                "checkout": f"checkout:{checkout_id}",
                "status": status,
                "basis": basis,
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

        hours = row.get("hours_marked") or "0"
        hourly_fee = tool_row.get("hourly_fee") or "0"
        multiplier = after_hours_multiplier(row.get("out") or "")
        total = float(hourly_fee) * float(hours) * float(multiplier)
        world.assert_tuple(
            "checkout_fee",
            {
                "checkout": f"checkout:{checkout_id}",
                "resolved_tool": f"tool:{resolved}",
                "hourly_rate": hourly_fee,
                "hours": hours,
                "after_hours_multiplier": multiplier,
                "total_fee": str(total),
            },
            origin=ConstructionOrigin.ADJUDICATED,
        )

        note = (row.get("note") or "").strip()
        if note == "PENDING":
            purpose.unresolved(
                "checkout_note_meaning",
                relation="checkout_record",
                subject={"checkout": checkout_id, "note": note},
                reason="shop_rules.txt does not define PENDING",
                grounding_ref=source.grounding(
                    "checkouts.csv", f"checkout_id={checkout_id}"
                ).observations[0].native_location,
            )

    purpose.require(
        "authorized_checkouts",
        relation="checkout_authorization",
        note="Determine which tool checkouts are authorized",
    )
    purpose.require(
        "checkout_fees",
        relation="checkout_fee",
        note="Fees under shop rules including identity changes and after-hours",
    )
    purpose.require_numeric(
        "fee_totals_numeric",
        relation="checkout_fee",
        field="total_fee",
        per="checkout",
        requires_established_world=False,
    )
    purpose.require_interpreted(
        "authorization_status",
        relation="checkout_authorization",
        field="status",
        known=["authorized", "unauthorized"],
        per="checkout",
        requires_established_world=False,
    )
