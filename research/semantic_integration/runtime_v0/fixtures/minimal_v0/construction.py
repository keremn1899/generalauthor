"""Frozen host-authored construction for the v0 spike. No model. No GM interpretation."""


def construct(source, world, purpose):
    source.tables()
    source.fields("orders.csv")
    source.profile("orders.csv", "amount")
    source.distinct_values("orders.csv", "amount")
    source.join("orders.csv", "accounts.csv", [("account_code", "account_code")])
    source.read_text("note.txt")

    world.declare_relation(
        "account",
        [
            Role("account", RoleType.REFERENT),
            Role("account_code", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "customer_order",
        [
            Role("order", RoleType.REFERENT),
            Role("account", RoleType.REFERENT),
            Role("amount_text", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "analysis_policy",
        [Role("statement", RoleType.TEXT)],
        scope="PURPOSE",
    )

    for row in source.rows("accounts.csv"):
        referent = f"account:{row['account_code']}"
        world.add_referent(referent, label=row["legal_name"])
        world.assert_tuple(
            "account",
            {
                "account": referent,
                "account_code": row["account_code"],
                "legal_name": row["legal_name"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "accounts.csv", f"account_code={row['account_code']}"
            ),
        )

    accounts = {row["account_code"]: row for row in source.rows("accounts.csv")}
    for row in source.rows("orders.csv"):
        account = accounts[row["account_code"]]
        order = f"order:{row['order_id']}"
        world.add_referent(order, label=row["order_id"])
        world.assert_tuple(
            "customer_order",
            {
                "order": order,
                "account": f"account:{account['account_code']}",
                "amount_text": row["amount"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding("orders.csv", f"order_id={row['order_id']}"),
        )

    world.assert_tuple(
        "analysis_policy",
        {
            "statement": "for this analysis, use legal_name from the accounts table",
        },
        origin=ConstructionOrigin.ADJUDICATED,
        grounding=None,
    )

    purpose.require_numeric(
        "order_amount_numeric",
        relation="customer_order",
        field="amount_text",
        per="order",
    )
    purpose.unresolved(
        "gm_token",
        relation="customer_order",
        subject={"order": "order:O2", "amount_text": "GM"},
        reason="GM is not established as numeric; the fixture note does not license an interpretation",
    )
