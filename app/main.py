"""FastAPI entrypoint.

Landing: a small top-down RPG world (canvas + a tile engine in rpg.js). Walk
into a building to open its quest log. A server-rendered text version holds the
same content for no-JS visitors and search engines.
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
from app.world import build_world

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
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "site": SITE,
            "is_prod": IS_PROD,
            "world_json": json.dumps(build_world()),
            "experience": content.EXPERIENCE,
            "projects": content.PROJECTS,
            "achievements": content.ACHIEVEMENTS,
            "education": content.EDUCATION,
        },
    )


@app.get("/api/world")
async def api_world() -> JSONResponse:
    return JSONResponse(build_world())


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "uptime_seconds": round(time.time() - _STARTED, 1)})


@app.get("/stats", response_class=JSONResponse)
async def stats() -> JSONResponse:
    return JSONResponse({"views": _VIEWS, "total": sum(_VIEWS.values())})


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nAllow: /\n")
