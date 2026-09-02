"""The `/world` plane: what it serves, and what it refuses.

The refusals are the point. This app exists beside a server that can write, and
the only thing keeping it read-only is that it never offers a way through — so
the SQL route's guard is tested harder than the routes that just format.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from research.semantic_integration.domains.bom.operational_frontier.generate import (
    freeze_operational_frontier,
)
from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
)
from world_explorer.http import build_app

TOKEN = "test-token"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    starlette_testclient = pytest.importorskip("starlette.testclient")
    path = tmp_path_factory.mktemp("world-http") / "bomS1.sqlite"
    experimental = construct_experimental_world(path)
    freeze_operational_frontier(
        experimental.world.taskview, path.with_suffix(".demand.json")
    )
    experimental.world.close()
    # Through the app rather than around it: the world is opened inside the
    # session's own thread, which is the thing that was broken when the adapter
    # was handed in from outside.
    with starlette_testclient.TestClient(build_app(path, token=TOKEN)) as opened:
        yield opened


def get(client, url: str):
    return client.get(url, headers={"Authorization": f"Bearer {TOKEN}"})


def test_bearer_gates_every_route(client):
    assert client.get("/world/schema").status_code == 401
    assert client.get(
        "/world/schema", headers={"Authorization": "Bearer wrong"}
    ).status_code == 401
    assert get(client, "/world/schema").status_code == 200


def test_schema_and_overview(client):
    overview = get(client, "/world/overview").json()
    assert overview["origins"]["SEMANTIC"] == 2

    relations = {r["name"]: r for r in get(client, "/world/schema").json()["relations"]}
    assert relations["acceptable_replacement"]["arity"] == 3
    assert relations["acceptable_replacement"]["origins"] == ["SEMANTIC"]
    assert relations["eligible_part"]["completeness"]["status"] == "COMPLETE"
    assert overview["incomplete"] == []


def test_referent_expand_and_assertion_round_trip(client):
    referent = get(client, "/world/referent?id=part:X160").json()
    assert any(item["name"] == "acceptable_replacement" for item in referent["relations"])

    expanded = get(
        client, "/world/expand?id=part:X160&relation=acceptable_replacement"
    ).json()
    assert len(expanded["tuples"]) == 1

    assertion_id = expanded["tuples"][0]["assertion_id"]
    detail = get(client, f"/world/assertion?id={assertion_id}").json()
    assert detail["origin"] == "SEMANTIC"
    assert detail["completeness"] is None
    assert len(detail["values"]) == 3


def test_derivation_and_support_are_served_and_gated(client):
    assert client.get("/world/derivation?relation=eligible_part").status_code == 401

    closure = get(client, "/world/derivation?relation=eligible_part").json()
    assert closure["run"]["state"] == "SUCCEEDED"
    assert "rated_voltage" in closure["nodes"]

    derived = get(client, "/world/rows?relation=eligible_part&limit=1").json()
    support = get(
        client, f"/world/support?id={derived['rows'][0]['assertion_id']}"
    ).json()
    assert support["derived"] is True
    assert len(support["inputs"]) == 3

    assert get(client, "/world/derivation?relation=nope").status_code == 404
    assert get(client, "/world/derivation").status_code == 400


def test_missing_things_are_404_and_bad_input_is_400(client):
    assert get(client, "/world/referent?id=part:nope").status_code == 404
    assert get(client, "/world/rows?relation=nope").status_code == 404
    assert get(client, "/world/referent").status_code == 400
    assert get(client, "/world/rows?relation=acceptable_replacement&limit=abc").status_code == 400


def test_demand_is_null_shaped_rather_than_empty(client):
    demand = get(client, "/world/demand").json()["demand"]
    assert demand["purpose"]["id"] == "viable_replacement"
    assert any(item["state"] == "UNRESOLVED" for item in demand["obligations"])


def test_sql_route_accepts_a_select_and_refuses_everything_else(client):
    def post(sql: str):
        return client.post(
            "/world/query",
            json={"sql": sql},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    ok = post("SELECT COUNT(*) AS c FROM acceptable_replacement")
    assert ok.status_code == 200
    assert ok.json()["rows"][0]["c"] == 2

    for refused in (
        "DELETE FROM acceptable_replacement",
        "UPDATE _tv_referents SET label = 'x'",
        "INSERT INTO _tv_referents(id, label) VALUES ('a', 'b')",
        "DROP TABLE acceptable_replacement",
        "PRAGMA writable_schema = 1",
        "SELECT 1; DELETE FROM acceptable_replacement",
    ):
        assert post(refused).status_code == 400, refused
