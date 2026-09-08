"""Local read-only World API and bundled inspection page."""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import re
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable

from .explorer import WorldExplorerAdapter

SELECT_ONLY = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class WorldSession:
    """Keep the SQLite connection on the one thread that created it."""

    def __init__(self, world: Path | str) -> None:
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="world")
        self._adapter = self._pool.submit(WorldExplorerAdapter, world).result()

    async def call(self, work: Callable[[WorldExplorerAdapter], Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._pool, work, self._adapter)

    def close(self) -> None:
        self._pool.submit(self._adapter.close).result()
        self._pool.shutdown(wait=True)


def _asset(name: str) -> str:
    return files("ontology_author.world").joinpath("static", name).read_text(encoding="utf-8")


def build_app(world: Path | str, *, token: str | None = None):
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
    from starlette.routing import Route

    session = WorldSession(world)

    def authorized(request: Request) -> bool:
        if not token:
            return True
        supplied = request.headers.get("authorization", "")
        return supplied.startswith("Bearer ") and hmac.compare_digest(
            supplied[7:], token
        )

    def guard(handler: Callable[[Request], Any]):
        async def wrapped(request: Request):
            if not authorized(request):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            try:
                return JSONResponse(await handler(request))
            except (KeyError, ValueError) as error:
                return JSONResponse({"error": str(error)}, status_code=400)

        return wrapped

    def required(request: Request, name: str) -> str:
        value = request.query_params.get(name)
        if not value:
            raise ValueError(f"{name} is required")
        return value

    def integer(request: Request, name: str, default: int) -> int:
        value = request.query_params.get(name)
        return default if value in (None, "") else int(value)

    async def overview(_request):
        return await session.call(lambda adapter: adapter.overview())

    async def schema(_request):
        return {"relations": await session.call(lambda adapter: adapter.schema())}

    async def referents(_request):
        return {"referents": await session.call(lambda adapter: adapter.referents())}

    async def search(request):
        return {"results": await session.call(lambda adapter: adapter.search(
            request.query_params.get("q", ""), limit=integer(request, "limit", 30)
        ))}

    async def referent(request):
        return await session.call(lambda adapter: adapter.referent(required(request, "id")))

    async def expand(request):
        return await session.call(lambda adapter: adapter.expand(
            required(request, "id"), required(request, "relation"),
            limit=integer(request, "limit", 200),
        ))

    async def rows(request):
        return await session.call(lambda adapter: adapter.rows(
            required(request, "relation"),
            limit=integer(request, "limit", 200),
            offset=integer(request, "offset", 0),
            order=request.query_params.get("order") or None,
            descending=request.query_params.get("desc") in ("1", "true", "yes"),
            subject=request.query_params.get("subject") or None,
        ))

    async def assertion(request):
        return await session.call(lambda adapter: adapter.assertion(required(request, "id")))

    async def derivation(request):
        return await session.call(lambda adapter: adapter.derivation(required(request, "relation")))

    async def support(request):
        return await session.call(lambda adapter: adapter.derivation_support(required(request, "id")))

    async def demand(_request):
        return {"demand": await session.call(lambda adapter: adapter.demand())}

    async def query(request):
        body = await request.json()
        sql = str(body.get("sql") or "").strip()
        if not SELECT_ONLY.match(sql):
            return JSONResponse({"error": "World queries must be one SELECT or WITH statement"}, status_code=400)
        rows_out = await session.call(lambda adapter: adapter.query_semantic(
            sql, tuple(body.get("parameters") or ())
        ))
        return JSONResponse({"rows": rows_out})

    async def index(_request):
        return HTMLResponse(_asset("index.html"))

    async def app_js(_request):
        return PlainTextResponse(_asset("app.js"), media_type="text/javascript")

    async def style_css(_request):
        return PlainTextResponse(_asset("style.css"), media_type="text/css")

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            session.close()

    routes = [
        Route("/", index),
        Route("/world-static/app.js", app_js),
        Route("/world-static/style.css", style_css),
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
    ]
    return Starlette(lifespan=lifespan, routes=routes)


def serve(world: Path | str, *, host: str = "127.0.0.1", port: int = 0, token: str | None = None) -> None:
    import uvicorn

    uvicorn.run(build_app(world, token=token), host=host, port=port, log_level="warning")


def open_world(world: Path | str, *, host: str = "127.0.0.1", port: int = 0, token: str | None = None) -> str:
    """Serve a sealed World and open the bundled inspection page."""

    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config(build_app(world, token=token), host=host, port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, name="ontology-author-world", daemon=True)
    thread.start()
    while not server.started:
        if not thread.is_alive():
            raise RuntimeError("World server stopped before it was ready")
        threading.Event().wait(0.01)
    actual_port = server.servers[0].sockets[0].getsockname()[1]
    url = f"http://{host}:{actual_port}/"
    print(f"World inspector: {url}", flush=True)
    webbrowser.open(url)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(timeout=2)
    return url


__all__ = ["WorldSession", "build_app", "open_world", "serve"]
