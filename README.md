# pradyumnaprasad.dev

My portfolio, built as a live application rather than a static page. It is a
FastAPI service that server-renders its own content and will grow a data
dashboard, semantic project search, and a RAG "ask my portfolio" chatbot.

## Stack

| Layer      | Choice |
|------------|--------|
| Backend    | FastAPI (Python 3.12) |
| Frontend   | Jinja templates + hand-written CSS (dark-first), HTMX for live bits |
| Database   | Neon Postgres + pgvector *(Phase 2+)* |
| Queue/cache| Upstash Redis *(Phase 3+)* |
| LLM        | Google Gemini API — free tier *(Phase 4)* |
| Embeddings | sentence-transformers, run locally *(Phase 4)* |
| Hosting    | Render free web service, via `render.yaml` blueprint |
| CI         | GitHub Actions — ruff + pytest |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
# http://127.0.0.1:8000  ·  API docs at /api
```

```bash
ruff check . && ruff format --check . && pytest
```

## Deploy

Push to GitHub, then in Render: **New → Blueprint → select this repo**.
`render.yaml` provisions the web service; `autoDeploy` ships every push to `main`.

## Roadmap

- [x] **Phase 1** — live skeleton: home page, health check, CI, Render blueprint
- [ ] **Phase 2** — Postgres-backed content; project detail pages
- [ ] **Phase 3** — GitHub-activity ETL + dashboard; site analytics panel
- [ ] **Phase 4** — pgvector semantic search + Gemini RAG chatbot + scikit-learn demo
- [ ] **Phase 5** — SEO, sitemap, custom domain, architecture diagram
