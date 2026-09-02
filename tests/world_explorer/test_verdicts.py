"""Human verdicts: what may be recorded, and what may not.

The refusals carry the weight here. The measured failure this surface exists
to correct is under-closure — the constructor declining where the evidence was
sufficient — and the obvious way to build a surface that fixes it is to build
one that makes closing easy. That would trade an honest machine for a
credulous one. So the burdens are tested harder than the happy path: §6.1 says
they do not relax for a human, and a burden enforced only in a form is a
burden until someone uses curl.
"""

from __future__ import annotations

import json

import pytest

from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
)
from world_explorer.http import build_app
from world_explorer.verdicts import BurdenNotMet, VerdictLedger, citable

from .test_construction import build_run

TOKEN = "test-token"

PACKET = {
    "selected_observations": [
        {"source_path": "crm.csv", "location": "L14", "excerpt": "Northbridge…"},
        {"source_path": "registry.csv", "location": "L3", "excerpt": "Northbridge…"},
    ]
}
ALLOWED = citable(PACKET)
CITE = [{"source_path": "crm.csv", "location": "L14"}]


@pytest.fixture
def ledger(tmp_path) -> VerdictLedger:
    return VerdictLedger(tmp_path / "verdicts" / "T1.jsonl")


def close(ledger, **overrides):
    """A well-formed closing verdict, so each test can break exactly one thing."""
    arguments = {
        "obligation_id": "alpha",
        "disposition": "SAME_ENTITY",
        "allowed_citations": ALLOWED,
        "supporting_evidence": CITE,
        "support_claim": "Both records name one company at one address.",
        "actor": "kerem",
    }
    arguments.update(overrides)
    return ledger.record(
        arguments.pop("obligation_id"), arguments.pop("disposition"), **arguments
    )


# -- the burdens ------------------------------------------------------------


def test_closing_without_a_citation_is_refused(ledger):
    with pytest.raises(BurdenNotMet, match="at least one cited location"):
        close(ledger, supporting_evidence=[])
    assert ledger.entries() == []


def test_closing_without_a_support_claim_is_refused(ledger):
    with pytest.raises(BurdenNotMet, match="support_claim"):
        close(ledger, support_claim="   ")


def test_upholding_a_decline_needs_neither(ledger):
    """§15, under-closure upheld: a packet that genuinely preserves multiple
    live candidates. `UNRESOLVED` is a decision and is recorded as one."""
    record = ledger.record(
        "alpha",
        "UNRESOLVED",
        allowed_citations=ALLOWED,
        actor="kerem",
    )
    assert record["disposition"] == "UNRESOLVED"
    assert record["supporting_evidence"] == []


def test_evidence_the_constructor_never_saw_is_refused(ledger):
    """Citation is by selection (§8.2). A location outside the packet is not a
    weak verdict, it is a different intervention — an amendment (§6.3)."""
    with pytest.raises(BurdenNotMet, match="not in this obligation's packet"):
        close(ledger, supporting_evidence=[{"source_path": "notes.md", "location": "p9"}])


def test_a_citation_needs_both_halves(ledger):
    with pytest.raises(BurdenNotMet, match="both a source_path and a location"):
        close(ledger, supporting_evidence=[{"source_path": "crm.csv"}])


def test_a_verdict_outside_the_vocabulary_is_refused(ledger):
    with pytest.raises(ValueError, match="not a verdict"):
        close(ledger, disposition="PROBABLY")


def test_a_verdict_belongs_to_someone(ledger):
    with pytest.raises(ValueError, match="actor is required"):
        close(ledger, actor="")


def test_citable_reads_the_packet_and_nothing_else():
    assert ALLOWED == {("crm.csv", "L14"), ("registry.csv", "L3")}
    assert citable(None) == set()
    assert citable({"selected_observations": [{"source_path": "x"}]}) == set()


# -- append-only ------------------------------------------------------------


def test_the_machines_judgment_is_superseded_not_overwritten(ledger):
    record = close(ledger, supersedes="UNRESOLVED")
    assert record["supersedes"] == "UNRESOLVED"
    assert ledger.current()["alpha"]["disposition"] == "SAME_ENTITY"


def test_a_second_verdict_keeps_the_first(ledger):
    close(ledger)
    close(ledger, disposition="DISTINCT", support_claim="Different registrations.")
    assert [entry["disposition"] for entry in ledger.history("alpha")] == [
        "SAME_ENTITY",
        "DISTINCT",
    ]
    assert ledger.current()["alpha"]["disposition"] == "DISTINCT"


def test_revert_restores_the_machine_and_keeps_the_record(ledger):
    """§15, revert: the machine disposition is current again — and both the
    verdict and its withdrawal stay in the file."""
    close(ledger)
    ledger.revert("alpha", actor="kerem")
    assert ledger.current() == {}
    assert [entry["kind"] for entry in ledger.history("alpha")] == [
        "ADJUDICATION",
        "REVERT",
    ]


def test_reverting_nothing_is_a_miss(ledger):
    with pytest.raises(KeyError):
        ledger.revert("alpha", actor="kerem")


def test_one_bad_line_does_not_cost_the_trail(ledger):
    close(ledger)
    with ledger.path.open("a", encoding="utf-8") as handle:
        handle.write("{ half-written\n")
    close(ledger, disposition="DISTINCT", support_claim="Different registrations.")
    assert len(ledger.entries()) == 2


def test_the_ledger_is_lines_of_json(ledger):
    close(ledger)
    close(ledger, obligation_id="beta", disposition="UNRESOLVED", supporting_evidence=[])
    lines = ledger.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["actor"] == "kerem" for line in lines)


def test_an_admission_change_is_append_only_and_separate(ledger):
    proposal = ledger.admit(
        "identity_judgment",
        "PURPOSE",
        reason="This relation encodes the active purpose's threshold.",
        purpose_independence_test="Withdraw the purpose and the threshold disappears.",
        supersedes="WORLD",
        actor="kerem",
    )
    assert proposal["kind"] == "ADMISSION"
    assert ledger.current() == {}
    assert ledger.current_admissions()["identity_judgment"] == proposal


def test_an_admission_change_needs_its_test(ledger):
    with pytest.raises(ValueError, match="purpose_independence_test"):
        ledger.admit(
            "identity_judgment",
            "PURPOSE",
            reason="Purpose-bound.",
            purpose_independence_test="",
            supersedes="WORLD",
            actor="kerem",
        )


# -- through the app --------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    starlette_testclient = pytest.importorskip("starlette.testclient")
    run = build_run(tmp_path / "T1")
    world = tmp_path / "world.sqlite"
    construct_experimental_world(world).world.close()
    app = build_app(
        world,
        token=TOKEN,
        construction=run,
        verdicts=tmp_path / "verdicts" / "T1.jsonl",
    )
    with starlette_testclient.TestClient(app) as opened:
        yield opened


def get(client, url: str):
    return client.get(url, headers={"Authorization": f"Bearer {TOKEN}"})


def post(client, url: str, body: dict):
    return client.post(url, json=body, headers={"Authorization": f"Bearer {TOKEN}"})


def adjudicate(client, **overrides):
    body = {
        "obligation_id": "alpha",
        "disposition": "SAME_ENTITY",
        "supporting_evidence": [{"source_path": "notes.md", "location": "p1"}],
        "support_claim": "The note establishes one entity.",
        "actor": "kerem",
    }
    body.update(overrides)
    return post(client, "/construction/verdict", body)


def test_a_verdict_closes_the_obligation_and_drops_it_down_the_docket(client):
    """§15, under-closure corrected. `alpha` is the only purpose-blocking row;
    once it is decided the docket is a shorter list, and the row that was
    second is first."""
    before = get(client, "/construction/docket").json()
    assert [row["obligation_id"] for row in before["obligations"]][0] == "alpha"
    assert before["counts"]["blocking"] == 1

    assert adjudicate(client).status_code == 200

    after = get(client, "/construction/docket").json()
    assert [row["obligation_id"] for row in after["obligations"]][0] == "beta"
    assert after["counts"]["blocking"] == 0
    alpha = next(r for r in after["obligations"] if r["obligation_id"] == "alpha")
    assert alpha["open"] is False
    # The machine's decline is still on the row, beneath the verdict.
    assert alpha["disposition"] == "UNRESOLVED"
    assert alpha["verdict"]["disposition"] == "SAME_ENTITY"


def test_the_verdict_records_what_it_supersedes(client):
    recorded = adjudicate(client).json()
    assert recorded["supersedes"] == "UNRESOLVED"
    assert recorded["actor"] == "kerem"
    assert recorded["at"].endswith("+00:00")


def test_an_invented_citation_is_a_400(client):
    response = adjudicate(
        client, supporting_evidence=[{"source_path": "invented.csv", "location": "L1"}]
    )
    assert response.status_code == 400
    assert "not in this obligation's packet" in response.json()["error"]


def test_a_verdict_against_no_obligation_is_a_404(client):
    assert adjudicate(client, obligation_id="nobody").status_code == 404


def test_history_survives_the_revert(client):
    adjudicate(client)
    assert post(
        client, "/construction/revert", {"obligation_id": "alpha", "actor": "kerem"}
    ).status_code == 200
    opened = get(client, "/construction/obligation?id=alpha").json()
    assert opened["verdict"] is None
    assert opened["judgment"]["disposition"] == "UNRESOLVED"
    history = get(client, "/construction/history?id=alpha").json()["history"]
    assert [entry["kind"] for entry in history] == ["ADJUDICATION", "REVERT"]


def test_the_write_routes_are_gated(client):
    assert client.post("/construction/verdict", json={}).status_code == 401
    assert client.post("/construction/revert", json={}).status_code == 401
    assert client.post("/construction/admission", json={}).status_code == 401


def test_admission_is_a_proposal_and_stales_only_downstream(client):
    response = post(
        client,
        "/construction/admission",
        {
            "relation": "identity_judgment",
            "admission": "PURPOSE",
            "reason": "The active purpose supplies this threshold.",
            "purpose_independence_test": "Withdraw A and the threshold disappears.",
            "actor": "kerem",
        },
    )
    assert response.status_code == 200
    assert response.json()["supersedes"] == "WORLD"
    assert get(client, "/construction/admissions").json()["admissions"][
        "identity_judgment"
    ]["admission"] == "PURPOSE"
    passes = get(client, "/construction").json()["passes"]
    stale = [entry["pass"] for entry in passes if entry["state"] == "STALE"]
    assert stale == ["p7", "p8"]


def test_withdrawing_an_admission_leaves_nothing_standing(ledger):
    """§6.4 — every intervention has a backward path. Proposing the artifact's
    value back is a different act: it leaves a human proposal standing, and the
    spine is right to call that an intervention. Withdrawal removes it."""
    ledger.admit(
        "identity_judgment",
        "PURPOSE",
        reason="This relation encodes the active purpose's threshold.",
        purpose_independence_test="Withdraw the purpose and the threshold disappears.",
        supersedes="WORLD",
        actor="kerem",
    )
    withdrawal = ledger.withdraw("identity_judgment", actor="kerem")
    assert withdrawal["kind"] == "REVERT"
    assert withdrawal["reverts"] == "PURPOSE"
    assert ledger.current_admissions() == {}
    # Both records survive; §6.4 has no silent edits.
    assert len(ledger.entries()) == 2


def test_withdrawing_nothing_is_a_miss(ledger):
    with pytest.raises(KeyError):
        ledger.withdraw("identity_judgment", actor="kerem")


def test_a_withdrawal_belongs_to_someone(ledger):
    ledger.admit(
        "identity_judgment",
        "PURPOSE",
        reason="Purpose-bound.",
        purpose_independence_test="Withdraw A and it disappears.",
        supersedes="WORLD",
        actor="kerem",
    )
    with pytest.raises(ValueError, match="actor"):
        ledger.withdraw("identity_judgment", actor=" ")


def test_an_admission_withdrawal_does_not_touch_the_obligations(ledger):
    """The two folds share a file and not a namespace: a relation-addressed
    withdrawal must not withdraw an obligation-addressed verdict."""
    close(ledger, obligation_id="alpha", disposition="UNRESOLVED", supporting_evidence=[])
    ledger.admit(
        "identity_judgment",
        "PURPOSE",
        reason="Purpose-bound.",
        purpose_independence_test="Withdraw A and it disappears.",
        supersedes="WORLD",
        actor="kerem",
    )
    ledger.withdraw("identity_judgment", actor="kerem")
    assert set(ledger.current()) == {"alpha"}
    assert ledger.current_admissions() == {}


def test_withdrawal_over_http_returns_p7_and_p8_off_stale(client):
    """The whole point of the backward path: without it an admission was a
    one-way door and the run's last two passes stayed stale for its lifetime."""
    post(
        client,
        "/construction/admission",
        {
            "relation": "identity_judgment",
            "admission": "PURPOSE",
            "reason": "The active purpose supplies this threshold.",
            "purpose_independence_test": "Withdraw A and the threshold disappears.",
            "actor": "kerem",
        },
    )
    response = post(
        client,
        "/construction/withdrawal",
        {"relation": "identity_judgment", "actor": "kerem"},
    )
    assert response.status_code == 200
    assert get(client, "/construction/admissions").json()["admissions"] == {}
    passes = get(client, "/construction").json()["passes"]
    assert [entry["pass"] for entry in passes if entry["state"] == "STALE"] == []


def test_the_withdrawal_route_is_gated(client):
    assert client.post("/construction/withdrawal", json={}).status_code == 401
