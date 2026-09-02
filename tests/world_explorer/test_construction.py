"""The `/construction` plane: the docket's order, and what it will not claim.

The order is the product. A docket that lists by arrival is a list; a docket
that lists by what a decision unblocks is a queue someone can work from the
top of, and every case here is about that ordering being earned from the
artifacts rather than guessed.

The run is synthesised rather than borrowed from `research/`. A real campaign
is often mid-flight in this checkout, and a test that reads one measures
whatever the constructor happened to have written that morning.
"""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from research.semantic_integration.domains.bom.world_programming.construct import (
    construct_experimental_world,
)
from world_explorer.construction import PASS_ARTIFACTS, ConstructionReader
from world_explorer.http import build_app

TOKEN = "test-token"


def _write(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def build_run(root: Path) -> Path:
    """A three-obligation run, complete through P8.

    `alpha` is open and blocks purpose A. `beta` is open and blocks nothing a
    purpose waits on. `gamma` is decided, and its relation *would* block
    purpose A if it were open — which is the case the ordering has to get
    right.
    """
    obligations = [
        {
            "obligation_id": "gamma",
            "relation": "identity_judgment",
            "values": {"left": "billing:Helion", "right": "contract:MSA"},
            "why_demanded": "Join billing to contract.",
            "required_by": ["A", "commercial_dependency"],
            "current_epistemic_state": "UNRESOLVED",
        },
        {
            "obligation_id": "beta",
            "relation": "clause_judgment",
            "values": {"contract": "contract:MSA", "kind": "rolling_term"},
            "why_demanded": "Adjudicate clause presence.",
            "required_by": ["B"],
            "current_epistemic_state": "UNRESOLVED",
        },
        {
            "obligation_id": "alpha",
            "relation": "identity_judgment",
            "values": {"left": "billing:Meridian", "right": "contract:MER"},
            "why_demanded": "Join billing to contract.",
            "required_by": ["A", "commercial_dependency"],
            "current_epistemic_state": "UNRESOLVED",
        },
    ]
    dispositions = [
        {
            "obligation_id": "gamma",
            "relation": "identity_judgment",
            "disposition": "SAME_ENTITY",
            "supporting_evidence": [{"source_path": "notes.md", "location": "p1"}],
            "support_claim": "The note states they are one entity.",
            "rationale": "Establishing evidence present.",
            "original_disposition": "SAME_ENTITY",
            "verification_result": "SUPPORTED",
        },
        {
            "obligation_id": "beta",
            "relation": "clause_judgment",
            "disposition": "UNRESOLVED",
            "supporting_evidence": [],
            "rationale": "Packet preserves multiple readings.",
            "original_disposition": "ACCEPT",
            "verification_result": "NOT_SUPPORTED",
        },
        {
            "obligation_id": "alpha",
            "relation": "identity_judgment",
            "disposition": "UNRESOLVED",
            "supporting_evidence": [],
            "rationale": "Name similarity alone does not establish identity.",
            "original_disposition": "SAME_ENTITY",
            "verification_result": "NOT_SUPPORTED",
        },
    ]
    derivations = {
        "pass": "P7",
        "derivations": [
            {
                "output_relation": "purpose_ir/a/output.json",
                "blocking_unresolved_state": [
                    "identity_judgment UNRESOLVED forces status unresolved"
                ],
                "non_blocking_unresolved_state": [],
            },
            {
                "output_relation": "commercial_dependency_row",
                "blocking_unresolved_state": [
                    "clause_judgment UNRESOLVED withholds the row"
                ],
                "non_blocking_unresolved_state": [],
            },
        ],
    }
    documents = {
        "p0": {"purposes": ["A", "B"]},
        "p1": {"relations": []},
        "p2": {"referents": 3},
        "p3": obligations,
        "p5": dispositions,
        "p6": {"admission": []},
        "p7": derivations,
    }
    for index, (pass_id, artifact) in enumerate(PASS_ARTIFACTS.items()):
        snapshot = root / "passes" / pass_id / "workspace_snapshot"
        _write(
            root / "passes" / pass_id / "agent.json",
            {
                "pass_id": pass_id,
                "model": "test-model",
                "reported_model": "Test Model",
                "returncode": 0,
                "timed_out": False,
                # A minute apiece. The passes run in sequence and record only
                # when they finished, so the gap is the pass.
                "finished_at": f"2026-09-02T08:{index:02d}:00+00:00",
                "isolation_preflight": {"leaks": 0},
            },
        )
        if pass_id in documents:
            _write(snapshot / artifact, documents[pass_id])
        elif pass_id == "p4":
            for obligation in obligations:
                _write(
                    snapshot / artifact / f"{obligation['obligation_id']}.json",
                    {
                        "obligation_id": obligation["obligation_id"],
                        "selected_observations": [
                            {
                                "source_path": "notes.md",
                                "location": "p1",
                                "excerpt": "…",
                            }
                        ],
                        "selection_rationale": "Pairwise packet.",
                        "known_missing_information": "No company number.",
                    },
                )
        elif pass_id == "p8":
            _write(snapshot / artifact / "a.json", {"rows": []})
    return root


@pytest.fixture
def run(tmp_path) -> Path:
    return build_run(tmp_path / "T1")


@pytest.fixture
def reader(run) -> ConstructionReader:
    return ConstructionReader(run)


# -- the run itself ---------------------------------------------------------


def test_a_directory_without_passes_is_refused(tmp_path):
    with pytest.raises(ValueError, match="no passes"):
        ConstructionReader(tmp_path)


def test_a_campaign_says_to_name_a_trial(tmp_path):
    (tmp_path / "trials").mkdir()
    with pytest.raises(ValueError, match="name a trial"):
        ConstructionReader(tmp_path)


def test_overview_reports_artifacts_and_counts(reader):
    overview = reader.overview()
    assert overview["run"] == "T1"
    assert [entry["pass"] for entry in overview["passes"]] == list(PASS_ARTIFACTS)
    assert all(entry["present"] for entry in overview["passes"])
    packets = next(e for e in overview["passes"] if e["pass"] == "p4")
    assert packets["items"] == 3
    assert overview["counts"]["obligations"] == 3
    assert overview["counts"]["open"] == 2
    assert overview["counts"]["decided"] == 1
    assert overview["unreadable"] == []


def test_no_pass_is_certified_without_a_scorer(reader):
    """§5: certification comes from the scorers, and the front end reports
    state rather than conferring it. With no score handed in, every clean pass
    reads unscored — never certified."""
    passes = reader.overview()["passes"]
    assert all(entry["state"] is None for entry in passes)
    assert all(entry["scored"] is None for entry in passes)
    assert all(entry["because"] == ["no scorer has spoken"] for entry in passes)
    assert "CERTIFIED" not in json.dumps(reader.overview())


def test_a_scorer_certifies_and_a_bad_score_does_not_fail(reader):
    """A scorer's `pass: false` is not §5's FAILED — that word is about the
    artifact, and a pass can produce a perfectly valid artifact full of wrong
    judgments. T1's P5 is exactly that, and it is why the docket exists."""
    overview = reader.overview(None, {"p0": {"pass": True}, "p5": {"pass": False}})
    by_id = {entry["pass"]: entry for entry in overview["passes"]}
    assert by_id["p0"]["state"] == "CERTIFIED"
    assert by_id["p5"]["state"] is None
    assert by_id["p5"]["scored"] is False
    assert by_id["p5"]["because"] == ["the scorers did not pass it"]


def test_a_verdict_makes_the_downstream_passes_stale(reader):
    """§10: verdict recorded → passes P6–P8 go stale on the spine. Upstream of
    the intervention is untouched, which is the whole reason adjudication is
    the cheap intervention."""
    overview = reader.overview({"alpha": {"disposition": "SAME_ENTITY"}})
    by_id = {entry["pass"]: entry for entry in overview["passes"]}
    assert [name for name, entry in by_id.items() if entry["state"] == "STALE"] == [
        "p6",
        "p7",
        "p8",
    ]
    assert by_id["p5"]["state"] is None
    assert by_id["p6"]["because"] == ["intervened in upstream: p5"]


def test_a_pass_that_wrote_nothing_is_failed(reader, tmp_path):
    """§5's FAILED: ran and did not produce a valid artifact."""
    (reader.path / "passes" / "p7" / "workspace_snapshot" / "07_derivations.json").unlink()
    by_id = {entry["pass"]: entry for entry in reader.overview()["passes"]}
    assert by_id["p7"]["state"] == "FAILED"
    assert by_id["p7"]["because"] == ["wrote no readable artifact"]


def test_a_moved_input_makes_a_pass_provisional(reader):
    """§5's reused machinery: each snapshot is cumulative, so p6 holds the copy
    of P5's artifact that p6 actually read. Diverge them and P6 ran against an
    input that has since moved."""
    seen = reader.path / "passes" / "p6" / "workspace_snapshot" / "05_dispositions.json"
    seen.write_text("[]", encoding="utf-8")
    by_id = {entry["pass"]: entry for entry in reader.overview()["passes"]}
    assert by_id["p6"]["state"] == "PROVISIONAL"
    assert by_id["p6"]["because"] == ["input has moved since it ran: p5"]
    assert by_id["p5"]["state"] is None


def test_cost_is_positional_and_reproduces_the_table(reader):
    """§5's table, without a second copy of the chain: an intervention at pass
    N preserves P0–N and re-runs everything after it."""
    assert reader.cost("p5")["invalidates"] == ["p6", "p7", "p8"]
    assert reader.cost("p6")["invalidates"] == ["p7", "p8"]
    assert reader.cost("p1")["invalidates"] == ["p2", "p3", "p4", "p5", "p6", "p7", "p8"]
    adjudicate = reader.cost("p5")
    assert adjudicate["intervention"] == "adjudicate"
    assert adjudicate["preserves"] == ["p0", "p1", "p2", "p3", "p4", "p5"]
    # P7's derivation program is authored and survives; only its outputs move.
    assert adjudicate["preserves_program"] is True
    assert reader.cost("p1")["intervention"] == "amend"


def test_cost_is_measured_wall_clock_not_a_timeout(reader):
    """The honest answer to "what will this cost" is what it cost last time.
    A pass with no predecessor stamp is reported unmeasured, not guessed."""
    cost = reader.cost("p5")
    assert cost["seconds"] == 180.0
    assert cost["measured"] == 3
    assert cost["unmeasured"] == []
    assert reader.cost("p0")["measured"] == 8


def test_the_agent_record_carries_no_narration(reader):
    agent = next(e for e in reader.overview()["passes"] if e["pass"] == "p5")["agent"]
    assert agent == {
        "model": "Test Model",
        "returncode": 0,
        "timed_out": False,
        "finished_at": "2026-09-02T08:05:00+00:00",
    }


# -- the docket -------------------------------------------------------------


def test_docket_orders_by_what_a_decision_unblocks(reader):
    rows = reader.docket()["obligations"]
    assert [row["obligation_id"] for row in rows] == ["alpha", "beta", "gamma"]


def test_a_decided_obligation_blocks_nothing(reader):
    row = next(r for r in reader.docket()["obligations"] if r["obligation_id"] == "gamma")
    # Its relation is named in purpose A's blocking premise, and it is required
    # by A — but it is decided, and `blocking_unresolved_state` is about the
    # unresolved ones.
    assert row["blocks"]["purposes"] == ["A"]
    assert row["blocks"]["blocking"] is False
    assert row["open"] is False


def test_blocking_needs_both_the_premise_and_the_demand(reader):
    rows = {row["obligation_id"]: row for row in reader.docket()["obligations"]}
    # P7 names identity_judgment as blocking purpose A, and P3 says alpha is
    # required by A.
    assert rows["alpha"]["blocks"] == {
        "purposes": ["A"],
        "relations": [],
        "blocking": True,
    }
    # beta's relation blocks a derived relation, but no purpose demands it.
    assert rows["beta"]["blocks"] == {
        "purposes": [],
        "relations": ["commercial_dependency_row"],
        "blocking": False,
    }


def test_every_row_carries_the_machines_reason(reader):
    for row in reader.docket()["obligations"]:
        assert row["rationale"]
        assert row["observations"] == 1
        assert row["known_missing_information"]


def test_docket_counts_agree_with_its_rows(reader):
    docket = reader.docket()
    rows = docket["obligations"]
    assert docket["counts"] == {
        "total": len(rows),
        "open": sum(1 for row in rows if row["open"]),
        "decided": sum(1 for row in rows if not row["open"]),
        "blocking": sum(1 for row in rows if row["blocks"]["blocking"]),
    }


# -- one obligation ---------------------------------------------------------


def test_obligation_opens_three_panes(reader):
    opened = reader.obligation("alpha")
    assert opened["proposition"]["relation"] == "identity_judgment"
    assert opened["packet"]["selected_observations"][0]["location"] == "p1"
    assert opened["judgment"]["original_disposition"] == "SAME_ENTITY"
    assert opened["judgment"]["verification_result"] == "NOT_SUPPORTED"


def test_the_read_plane_never_supplies_a_verdict(reader):
    """A human verdict is recorded beside the run, not read out of it. The
    field is present so an adjudicated obligation has the same shape as one
    nobody has touched."""
    assert reader.obligation("alpha")["verdict"] is None


def test_an_unknown_obligation_is_a_miss_not_a_fault(reader):
    with pytest.raises(KeyError):
        reader.obligation("nobody")


# -- a run that is still being written --------------------------------------


def test_a_run_that_stopped_at_p4_is_read_not_refused(run):
    for pass_id in ("p5", "p6", "p7", "p8"):
        for path in sorted((run / "passes" / pass_id).rglob("*.json"), reverse=True):
            path.unlink()
    reader = ConstructionReader(run)
    rows = reader.docket()["obligations"]
    assert all(row["disposition"] is None for row in rows)
    # Undecided is open, and with no P7 nothing is known to be blocking.
    assert all(row["open"] for row in rows)
    assert reader.docket()["counts"]["blocking"] == 0


def test_a_half_written_artifact_is_reported_not_raised(run):
    dispositions = run / "passes" / "p5" / "workspace_snapshot" / PASS_ARTIFACTS["p5"]
    dispositions.write_text('[{"obligation_id": "alpha",', encoding="utf-8")
    overview = ConstructionReader(run).overview()
    assert any("05_dispositions.json" in note for note in overview["unreadable"])


def test_the_reader_cannot_write(reader):
    """The read-only guarantee is structural, so it is tested structurally: a
    write appearing in this module is the thing that would break it, and it
    should fail here before it reaches a review."""
    source = Path(inspect.getsourcefile(ConstructionReader)).read_text()
    # Word-bounded, because `_is_open` is a question and `open()` is a door.
    for forbidden in (r"\bopen\(", r"\bwrite_text\b", r"\bmkdir\b",
                      r"\bunlink\b", r"\brmtree\b", r"\bsqlite3\b"):
        assert re.search(forbidden, source) is None, forbidden


# -- over HTTP --------------------------------------------------------------


@pytest.fixture
def client(run):
    starlette_testclient = pytest.importorskip("starlette.testclient")
    world = _world(run.parent)
    with starlette_testclient.TestClient(
        build_app(world, token=TOKEN, construction=run)
    ) as opened:
        yield opened


def _world(directory: Path) -> Path:
    """A world for the app to open. `/construction` never touches it — it is
    here because the app opens one, which is itself the point: the two planes
    share a process and a bearer, and nothing else."""
    path = directory / "world.sqlite"
    experimental = construct_experimental_world(path)
    experimental.world.close()
    return path


def get(client, url: str):
    return client.get(url, headers={"Authorization": f"Bearer {TOKEN}"})


def test_construction_routes_are_gated(client):
    for url in (
        "/construction",
        "/construction/docket",
        "/construction/obligation?id=alpha",
        "/construction/pass?id=p3",
    ):
        assert client.get(url).status_code == 401
        assert get(client, url).status_code == 200


def test_docket_over_http_keeps_its_order(client):
    rows = get(client, "/construction/docket").json()["obligations"]
    assert [row["obligation_id"] for row in rows] == ["alpha", "beta", "gamma"]


def test_an_unknown_pass_is_a_404(client):
    assert get(client, "/construction/pass?id=p99").status_code == 404


def test_a_missing_id_is_a_400(client):
    assert get(client, "/construction/obligation").status_code == 400


def test_without_a_construction_the_routes_say_so(tmp_path):
    starlette_testclient = pytest.importorskip("starlette.testclient")
    world = _world(tmp_path)
    with starlette_testclient.TestClient(build_app(world, token=TOKEN)) as opened:
        response = get(opened, "/construction/docket")
    assert response.status_code == 404
    assert "no construction is open" in response.json()["error"]
