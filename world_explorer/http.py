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
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from world_explorer.adapter import WorldExplorerAdapter

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


def build_app(world: Path | str, *, token: str | None = None):
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    session = WorldSession(world)

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

    async def demand(request):
        # `null` rather than an empty frontier. A canvas told "no obligations"
        # would draw a world with no open questions; told "no purpose loaded",
        # it can say so — which is the true statement.
        return {"demand": await session.call(lambda adapter: adapter.demand())}

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
            Route("/world/demand", guard(demand)),
            Route("/world/query", query, methods=["POST"]),
        ],
    )


def serve(
    world: Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 8139,
    token: str | None = None,
) -> None:
    import uvicorn

    uvicorn.run(
        build_app(world, token=token), host=host, port=port, log_level="warning"
    )
