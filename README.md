# pradyumnaprasad.dev

My portfolio, built as a live application rather than a static page. The
landing is a small top-down RPG village (hand-written canvas tile engine);
each building opens a "quest log" with that section's content. A plain
server-rendered text version is the no-JS / SEO fallback.

## Stack

| Layer      | Choice |
|------------|--------|
| Backend    | FastAPI (Python 3.12) |
| Frontend   | Jinja + hand-written CSS + a canvas tile engine, VT323 / Press Start 2P |
| Database   | SQLite locally · Postgres (Neon) in prod · SQLAlchemy 2.0 + Alembic |
| Queue/cache| Upstash Redis *(Phase 3+)* |
| LLM        | Google Gemini API — free tier *(Phase 4)* |
| Embeddings | sentence-transformers + pgvector *(Phase 4)* |
| Hosting    | Render free web service, via `render.yaml` blueprint |
| CI         | GitHub Actions — ruff + pytest |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head          # creates portfolio.db (SQLite)
python -m app.etl             # pulls GitHub activity for the /dashboard page
uvicorn app.main:app --reload # seeds content from app/content.py on startup
# http://127.0.0.1:8000  ·  /dashboard  ·  API docs at /api
```

```bash
ruff check . && ruff format --check . && pytest
```

## Content

`app/content.py` is the human-editable source of truth. On every startup
`app/seed.py` upserts it into the database; the app reads from the DB via
`app/repo.py`. Schema changes go through Alembic:

```bash
alembic revision --autogenerate -m "what changed"
alembic upgrade head
```

## Deploy

1. Create a free Postgres database at [neon.tech], copy its connection string.
2. In Render: **New → Blueprint → select this repo**.
3. Set `DATABASE_URL` (the Neon string) in the service's Environment tab.

`render.yaml` runs `alembic upgrade head` before each deploy; `autoDeploy`
ships every push to `main`.

## Roadmap

- [x] **Phase 1** — live skeleton: home page, health check, CI, Render blueprint
- [x] **Phase 2** — database layer: SQLAlchemy models, Alembic migrations,
      content served from the DB, persistent page-view analytics
- [x] **Phase 3** — activity ETL (`python -m app.etl`, nightly cron): LeetCode
      (submission calendar, solves by difficulty/language, contest rating) +
      GitHub (languages, repo cadence, timeline). The Observatory building →
      `/dashboard`, plus this site's own traffic.
- [x] **Phase 4** — the Workshop building → `/workshop`: semantic search over
      portfolio content (Gemini embeddings, keyword fallback), a RAG
      "ask my portfolio" chatbot (Gemini free tier), and a small scikit-learn
      domain classifier. All degrade gracefully without `GEMINI_API_KEY`.
- [ ] **Phase 5** — SEO, sitemap, custom domain, architecture diagram
