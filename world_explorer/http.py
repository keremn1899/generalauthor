"""`/world` — the read plane the explorer canvas reads.

Deliberately a separate app from `mcp_server`. That server governs a Ladybug
graph: it holds a write path, proposals, a ledger and an owner lock. This one
opens a compiled World IR file and answers questions about it. Nothing here can
change a world, and keeping it out of the operator plane is what makes that
checkable rather than asserted.

Read-only is enforced, not documented: every route calls the adapter, and the
one route that takes SQL from the caller refuses anything that is not a single
`SELECT` or `WITH`. Binding is loopback and a bearer token gates the app when
one is configured, matching the local product's existing `devtoken` habit so the
front end's `?apiToken=` still works.

**One thread owns the world.** A TaskView holds an ordinary `sqlite3`
connection, and `sqlite3` refuses to be used from a thread other than the one
that created it. An ASGI server hands sync handlers to a threadpool, so an
adapter opened on the main thread and called from a route fails with
`SQLite objects created in a thread can only be used in that same thread` — not
occasionally, but on the first request. `WorldSession` therefore owns a
single-worker executor, opens the world *inside* it, and runs every call there.
That also serialises reads, which matches the repository's existing rule that
one process owns a graph file at a time.

`/construction` is the same app's second plane: one frozen constructor run,
read. It shares the bearer guard, and it is a separate module
(`construction.py`) for the same reason this app is separate from
`mcp_server` — nothing in the reader can write, and that is checkable by
reading its imports rather than by trusting a route. It needs no thread of its
own: it holds no long-lived connection; P2's SQLite coverage account opens in
URI read-only mode and closes in the same call.

Four routes on that plane do write, and they are the only four in this app:
`/construction/verdict`, `/construction/admission`, `/construction/revert`
and `/construction/withdrawal` append to a ledger
(`verdicts.py`) held outside both the run and any world. The read-only
guarantee this app makes is about *worlds*, and it is unchanged — a verdict is
an input to the next build, and the only path from one to a world tuple is a
rebuild.

Identifiers travel as query parameters rather than path segments because they
contain colons — `part:X160`, `assertion:0489b6…` — and a path that has to be
escaped and unescaped correctly at both ends is a bug waiting for the first id
with a slash in it.

    uv run --extra all python scripts/run_world_explorer.py --world data/worlds/bomS1.sqlite
"""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from world_explorer.adapter import WorldExplorerAdapter
from world_explorer.construction import ConstructionReader
from world_explorer.verdicts import VerdictLedger, citable

#: The read substrate stays open (§13), but only as a read.
SELECT_ONLY = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class WorldSession:
    """One open world, owned by one thread for the life of the process."""

    def __init__(self, world: Path | str) -> None:
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="world")
        self._adapter: WorldExplorerAdapter = self._pool.submit(
            WorldExplorerAdapter, world
        ).result()

    async def call(self, work: Callable[[WorldExplorerAdapter], Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._pool, work, self._adapter)

    def close(self) -> None:
        self._pool.submit(self._adapter.close).result()
        self._pool.shutdown(wait=True)


def build_app(
    world: Path | str,
    *,
    token: str | None = None,
    construction: Path | str | None = None,
    verdicts: Path | str | None = None,
    scores: Path | str | None = None,
    scores_at: str | None = None,
):
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    session = WorldSession(world)
    # Opened once so a bad path fails at startup rather than on the first
    # request, then read through on every call — it caches nothing, so holding
    # it open costs nothing and changes nothing.
    run = ConstructionReader(construction) if construction else None
    # The ledger sits beside the *server's* data, not inside the campaign. A
    # run directory is user-owned and often mid-flight; a surface that appends
    # to it writes into someone's evidence. Default rather than required so the
    # docket is never read-only by accident of configuration.
    ledger = (
        VerdictLedger(verdicts)
        if verdicts
        else VerdictLedger(Path("data/verdicts") / f"{run.path.name}.jsonl")
        if run
        else None
    )

    def scored() -> dict[str, Any]:
        """The scorers' word on this run's passes, re-read per request.

        A path rather than a loaded map, for the reason the reader gives: a
        score file is written by a scorer that may run again while this server
        is up, and a copy held in memory would be a second opinion with its own
        staleness. `scores_at` walks into a campaign report — the shape of that
        report is the campaign's business, so it is named on the command line
        rather than guessed at here.
        """
        if not scores:
            return {}
        try:
            document = json.loads(Path(scores).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # An unreadable score file must not take the docket down with it.
            # Every pass reads as unscored, which is the true statement.
            return {}
        for step in (scores_at or "").split(".") if scores_at else ():
            if not isinstance(document, dict) or step not in document:
                return {}
            document = document[step]
        return document if isinstance(document, dict) else {}

    def opened() -> ConstructionReader:
        if run is None:
            raise KeyError(
                "no construction is open — start the server with --construction"
            )
        return run

    def authorized(request: Request) -> bool:
        if not token:
            return True
        supplied = request.headers.get("authorization", "")
        prefix = "Bearer "
        if not supplied.startswith(prefix):
            return False
        return hmac.compare_digest(supplied[len(prefix) :], token)

    def guard(handler: Callable[[Request], Any]):
        """One place where every failure becomes a status code.

        A missing referent is a 404 rather than a 500 because the canvas asks
        for things a person typed, and an unknown relation is an answer, not a
        fault. `KeyError` is the adapter's word for both.
        """

        async def wrapped(request: Request) -> JSONResponse:
            if not authorized(request):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            try:
                return JSONResponse(await handler(request))
            except KeyError as error:
                return JSONResponse({"error": str(error)}, status_code=404)
            except ValueError as error:
                return JSONResponse({"error": str(error)}, status_code=400)

        return wrapped

    def _int(request: Request, name: str, default: int) -> int:
        raw = request.query_params.get(name)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except ValueError as error:
            raise ValueError(f"{name} must be an integer") from error

    def _required(request: Request, name: str) -> str:
        value = request.query_params.get(name)
        if not value:
            raise ValueError(f"{name} is required")
        return value

    async def overview(request):
        return await session.call(lambda adapter: adapter.overview())

    async def schema(request):
        return {"relations": await session.call(lambda adapter: adapter.schema())}

    async def referents(request):
        return {"referents": await session.call(lambda adapter: adapter.referents())}

    async def search(request):
        query_text = request.query_params.get("q", "")
        limit = _int(request, "limit", 30)
        return {
            "results": await session.call(
                lambda adapter: adapter.search(query_text, limit=limit)
            )
        }

    async def referent(request):
        referent_id = _required(request, "id")
        return await session.call(lambda adapter: adapter.referent(referent_id))

    async def expand(request):
        referent_id = _required(request, "id")
        relation = _required(request, "relation")
        limit = _int(request, "limit", 200)
        return await session.call(
            lambda adapter: adapter.expand(referent_id, relation, limit=limit)
        )

    async def rows(request):
        relation = _required(request, "relation")
        limit = _int(request, "limit", 200)
        offset = _int(request, "offset", 0)
        order = request.query_params.get("order") or None
        descending = request.query_params.get("desc") in ("1", "true", "yes")
        subject = request.query_params.get("subject") or None
        return await session.call(
            lambda adapter: adapter.rows(
                relation,
                limit=limit,
                offset=offset,
                order=order,
                descending=descending,
                subject=subject,
            )
        )

    async def assertion(request):
        assertion_id = _required(request, "id")
        return await session.call(lambda adapter: adapter.assertion(assertion_id))

    async def derivation(request):
        relation = _required(request, "relation")
        return await session.call(lambda adapter: adapter.derivation(relation))

    async def support(request):
        assertion_id = _required(request, "id")
        return await session.call(
            lambda adapter: adapter.derivation_support(assertion_id)
        )

    async def demand(request):
        # `null` rather than an empty frontier. A canvas told "no obligations"
        # would draw a world with no open questions; told "no purpose loaded",
        # it can say so — which is the true statement.
        return {"demand": await session.call(lambda adapter: adapter.demand())}

    async def construction_overview(request):
        return opened().overview(
            standing().current(), scored(), standing().current_admissions()
        )

    async def construction_cost(request):
        """§5 — what an intervention here costs, before it is made."""
        return opened().cost(
            _required(request, "at"),
            standing().current(),
            standing().current_admissions(),
        )

    async def construction_pass(request):
        return opened().pass_artifact(_required(request, "id"))

    def standing() -> VerdictLedger:
        opened()
        assert ledger is not None
        return ledger

    async def construction_docket(request):
        return opened().docket(standing().current())

    async def construction_obligation(request):
        obligation_id = _required(request, "id")
        return opened().obligation(
            obligation_id, standing().current().get(obligation_id)
        )

    async def construction_history(request):
        """Every verdict ever recorded on one obligation, oldest first.

        The reverted ones too. §6.4 — there are no silent edits, so the file
        is the record and this route is the file."""
        return {"history": standing().history(_required(request, "id"))}

    async def construction_admissions(request):
        return {"admissions": standing().current_admissions()}

    async def construction_admission(request):
        """§6.2 — stage an admission proposal; never mutate the World."""
        body = await request.json()
        relation = str(body.get("relation") or "")
        artifact = opened().pass_artifact("p6").get("document") or {}
        records = artifact.get("relations") if isinstance(artifact, dict) else []
        current = next(
            (
                item
                for item in records or []
                if isinstance(item, dict) and str(item.get("name")) == relation
            ),
            None,
        )
        if current is None:
            raise KeyError(f"no relation {relation!r} in P6 admission")
        proposal = standing().current_admissions().get(relation)
        supersedes = (proposal or current).get("admission")
        return standing().admit(
            relation,
            str(body.get("admission") or ""),
            reason=str(body.get("reason") or ""),
            purpose_independence_test=str(
                body.get("purpose_independence_test") or ""
            ),
            supersedes=str(supersedes) if supersedes else None,
            actor=str(body.get("actor") or ""),
        )

    async def construction_withdrawal(request):
        """§6.4 — withdraw an admission proposal, the backward path for §6.2."""
        body = await request.json()
        relation = str(body.get("relation") or "")
        if not relation:
            raise ValueError("relation is required")
        return standing().withdraw(relation, actor=str(body.get("actor") or ""))

    async def construction_verdict(request):
        """§6.1 — record one adjudication, or refuse it.

        The packet is read here and its locations handed to the ledger as the
        only citable set. That is the enforcement point for
        citation-by-selection: the front end offers checkboxes, but the reason
        a location cannot be invented is this line, not the checkbox.
        """
        reader = opened()
        body = await request.json()
        obligation_id = str(body.get("obligation_id") or "")
        if not obligation_id:
            raise ValueError("obligation_id is required")
        # Raises KeyError → 404 for an obligation this run does not have, so a
        # verdict can never be filed against nothing.
        item = reader.obligation(obligation_id)
        machine = (item.get("judgment") or {}).get("disposition")
        return standing().record(
            obligation_id,
            str(body.get("disposition") or ""),
            allowed_citations=citable(item.get("packet")),
            supporting_evidence=body.get("supporting_evidence") or (),
            support_claim=str(body.get("support_claim") or ""),
            supersedes=machine,
            actor=str(body.get("actor") or ""),
        )

    async def construction_revert(request):
        body = await request.json()
        obligation_id = str(body.get("obligation_id") or "")
        if not obligation_id:
            raise ValueError("obligation_id is required")
        return standing().revert(obligation_id, actor=str(body.get("actor") or ""))

    async def query(request):
        if not authorized(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        body = await request.json()
        sql = str(body.get("sql", ""))
        if not SELECT_ONLY.match(sql):
            return JSONResponse(
                {"error": "only a single SELECT or WITH query is accepted"},
                status_code=400,
            )
        if ";" in sql.strip().rstrip(";"):
            return JSONResponse(
                {"error": "only one statement is accepted"}, status_code=400
            )
        parameters = tuple(body.get("parameters") or ())
        rows_out = await session.call(lambda adapter: adapter.query(sql, parameters))
        return JSONResponse({"rows": rows_out})

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        # The world stays open for the life of the server and is closed once,
        # here. Closing is also what flushes the origins sidecar, so a process
        # that exits without it leaves a world the next reader cannot account
        # for.
        try:
            yield
        finally:
            session.close()

    return Starlette(
        lifespan=lifespan,
        routes=[
            Route("/world/overview", guard(overview)),
            Route("/world/schema", guard(schema)),
            Route("/world/referents", guard(referents)),
            Route("/world/search", guard(search)),
            Route("/world/referent", guard(referent)),
            Route("/world/expand", guard(expand)),
            Route("/world/rows", guard(rows)),
            Route("/world/assertion", guard(assertion)),
            Route("/world/derivation", guard(derivation)),
            Route("/world/support", guard(support)),
            Route("/world/demand", guard(demand)),
            Route("/world/query", query, methods=["POST"]),
            Route("/construction", guard(construction_overview)),
            Route("/construction/cost", guard(construction_cost)),
            Route("/construction/pass", guard(construction_pass)),
            Route("/construction/docket", guard(construction_docket)),
            Route("/construction/obligation", guard(construction_obligation)),
            Route("/construction/history", guard(construction_history)),
            Route("/construction/admissions", guard(construction_admissions)),
            # The only routes in this app that write, and they write to a
            # ledger — no compiled world, no pass artifact. A verdict is an
            # input to the next build.
            Route(
                "/construction/verdict",
                guard(construction_verdict),
                methods=["POST"],
            ),
            Route(
                "/construction/admission",
                guard(construction_admission),
                methods=["POST"],
            ),
            Route("/construction/revert", guard(construction_revert), methods=["POST"]),
            Route(
                "/construction/withdrawal",
                guard(construction_withdrawal),
                methods=["POST"],
            ),
        ],
    )


def serve(
    world: Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 8139,
    token: str | None = None,
    construction: Path | str | None = None,
    verdicts: Path | str | None = None,
    scores: Path | str | None = None,
    scores_at: str | None = None,
) -> None:
    import uvicorn

    uvicorn.run(
        build_app(
            world,
            token=token,
            construction=construction,
            verdicts=verdicts,
            scores=scores,
            scores_at=scores_at,
        ),
        host=host,
        port=port,
        log_level="warning",
    )
