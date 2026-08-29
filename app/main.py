"""FastAPI entrypoint.

Phase 1: the landing page is a hand-written force-directed knowledge graph
(canvas + a small physics sim in graph.js) with an accessible list view as a
fallback. Later phases add the dashboard and the RAG chatbot behind this app.
"""

from __future__ import annotations

import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import content
from app.config import BASE_DIR, IS_PROD, SITE
from app.graph import build_graph

app = FastAPI(title="Pradyumna Prasad — Portfolio", docs_url="/api", redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

_VIEWS: dict[str, int] = {}
_STARTED = time.time()


@app.middleware("http")
async def count_views(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if request.method == "GET" and not path.startswith(("/static", "/healthz", "/api")):
        _VIEWS[path] = _VIEWS.get(path, 0) + 1
    return response


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    graph = build_graph()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "site": SITE,
            "is_prod": IS_PROD,
            "graph_json": json.dumps(graph),
            "experience": content.EXPERIENCE,
            "projects": content.PROJECTS,
            "achievements": content.ACHIEVEMENTS,
            "education": content.EDUCATION,
        },
    )


@app.get("/api/graph")
async def api_graph() -> JSONResponse:
    return JSONResponse(build_graph())


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "uptime_seconds": round(time.time() - _STARTED, 1)})


@app.get("/stats", response_class=JSONResponse)
async def stats() -> JSONResponse:
    return JSONResponse({"views": _VIEWS, "total": sum(_VIEWS.values())})


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nAllow: /\n")
