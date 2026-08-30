"""FastAPI entrypoint.

The landing page is a cozy top-down RPG village (canvas tile engine in rpg.js);
each building opens a quest-log panel. Content is served from the database; a
server-rendered text version is the no-JS / SEO fallback.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import repo
from app.config import BASE_DIR, IS_PROD, SITE
from app.dashboard import build_dashboard
from app.db import SessionLocal, engine, get_session
from app.ml.classify import predict as ml_predict
from app.models import Base
from app.rag import gemini
from app.rag.chat import answer as rag_answer
from app.rag.store import reindex, search
from app.seed import seed
from app.world import build_world

_STARTED = time.time()
_view_buffer: dict[str, int] = {}


def _flush_views() -> None:
    if not _view_buffer:
        return
    pending = dict(_view_buffer)
    _view_buffer.clear()
    with SessionLocal() as db:
        try:
            repo.flush_views(db, pending)
        except Exception:  # never let analytics break a request cycle
            for k, v in pending.items():
                _view_buffer[k] = _view_buffer.get(k, 0) + v


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
        with contextlib.suppress(Exception):  # embeddings down → search uses keywords
            reindex(db)

    async def flusher() -> None:
        while True:
            await asyncio.sleep(30)
            _flush_views()

    task = asyncio.create_task(flusher())
    try:
        yield
    finally:
        task.cancel()
        _flush_views()


app = FastAPI(
    title="Pradyumna Prasad — Portfolio", docs_url="/api", redoc_url=None, lifespan=lifespan
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def count_views(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    counted = request.method == "GET" and not path.startswith(("/static", "/healthz", "/api"))
    if counted and path not in ("/favicon.ico", "/robots.txt"):
        _view_buffer[path] = _view_buffer.get(path, 0) + 1
    return response


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "site": SITE,
            "is_prod": IS_PROD,
            "world_json": json.dumps(build_world(db)),
            "experience": repo.experience(db),
            "projects": repo.projects(db),
            "achievements": repo.achievements(db),
            "education": repo.education(db),
        },
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "dashboard.html", {"site": SITE, "d": build_dashboard(db)}
    )


@app.get("/workshop", response_class=HTMLResponse)
async def workshop(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "workshop.html", {"site": SITE, "chat_enabled": gemini.enabled()}
    )


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Classify(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


_ASK_HITS: dict[str, list[float]] = {}


def _rate_ok(ip: str, limit: int = 10, window: float = 60.0) -> bool:
    now = time.time()
    hits = [t for t in _ASK_HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        _ASK_HITS[ip] = hits
        return False
    hits.append(now)
    _ASK_HITS[ip] = hits
    return True


@app.get("/api/search")
async def api_search(q: str = "", db: Session = Depends(get_session)) -> JSONResponse:
    return JSONResponse({"query": q, "results": search(db, q, k=6)})


@app.post("/api/ask")
async def api_ask(body: Ask, request: Request, db: Session = Depends(get_session)) -> JSONResponse:
    ip = request.client.host if request.client else "?"
    if not _rate_ok(ip):
        return JSONResponse({"error": "Too many questions — give it a minute."}, status_code=429)
    return JSONResponse(rag_answer(db, body.question))


@app.post("/api/ml/classify")
async def api_classify(body: Classify) -> JSONResponse:
    return JSONResponse({"text": body.text, "predictions": ml_predict(body.text)})


@app.get("/api/world")
async def api_world(db: Session = Depends(get_session)) -> JSONResponse:
    return JSONResponse(build_world(db))


@app.get("/api/dashboard")
async def api_dashboard(db: Session = Depends(get_session)) -> JSONResponse:
    return JSONResponse(build_dashboard(db))


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "uptime_seconds": round(time.time() - _STARTED, 1)})


@app.get("/stats", response_class=JSONResponse)
async def stats(db: Session = Depends(get_session)) -> JSONResponse:
    totals = repo.view_totals(db)
    for path, pending in _view_buffer.items():
        totals["views"][path] = totals["views"].get(path, 0) + pending
    totals["total"] = sum(totals["views"].values())
    return JSONResponse(totals)


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nAllow: /\n")
