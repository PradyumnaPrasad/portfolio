import pytest

from app.ml.classify import predict
from app.rag import gemini
from app.rag.chat import answer
from app.rag.corpus import build_documents
from app.rag.store import reindex, search


def test_corpus_has_project_and_experience_docs(client, db):
    docs = build_documents(db)
    kinds = {d["kind"] for d in docs}
    assert {"project", "experience", "achievement", "about"} <= kinds
    assert any("Dual Insight Engine" in d["text"] for d in docs)


def test_reindex_and_keyword_search(client, db, monkeypatch):
    monkeypatch.setattr(gemini, "enabled", lambda: False)
    stats = reindex(db)
    assert stats["documents"] > 10 and stats["embeddings"] is False

    hits = search(db, "reinforcement learning adaptive tutoring", k=3)
    assert hits and hits[0]["mode"] == "keyword"
    assert any("NeuroMentor" in h["title"] for h in hits)


def test_semantic_search_with_fake_embeddings(client, db, monkeypatch):
    monkeypatch.setattr(gemini, "enabled", lambda: True)

    def fake_embed(texts):
        # 1-D "embedding": longer text → larger value, so cosine is trivially 1.0
        return [[float(len(t))] for t in texts]

    monkeypatch.setattr(gemini, "embed", fake_embed)
    reindex(db)
    hits = search(db, "anything", k=2)
    assert hits and hits[0]["mode"] == "semantic"


def test_chat_disabled_without_key(client, db, monkeypatch):
    monkeypatch.setattr(gemini, "enabled", lambda: False)
    reindex(db)
    res = answer(db, "Has he done ETL work?")
    assert res["disabled"] is True
    assert res["answer"] is None
    assert res["sources"]


def test_chat_answers_with_mocked_gemini(client, db, monkeypatch):
    monkeypatch.setattr(gemini, "enabled", lambda: True)
    monkeypatch.setattr(gemini, "embed", lambda texts: [[1.0] for _ in texts])

    seen = {}

    def fake_generate(system, user, **kw):
        seen["user"] = user
        return "Yes — he migrated a SQL Server database and built ETL pipelines at Hexango."

    monkeypatch.setattr(gemini, "generate", fake_generate)
    reindex(db)
    res = answer(db, "Has he done ETL work?")
    assert "ETL" in res["answer"]
    assert "Context:" in seen["user"] and "Question:" in seen["user"]
    assert res["sources"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("build a FastAPI service with a Redis job queue", "backend"),
        ("clean a messy CSV and load it into a warehouse", "data"),
        ("train a transformer for text classification", "machine-learning"),
        ("Kubernetes deploy with automatic rollback", "infrastructure"),
    ],
)
def test_classifier_predictions(text, expected):
    preds = predict(text)
    assert preds[0]["label"] == expected
    assert abs(sum(p["prob"] for p in preds) - 1.0) < 0.01


def test_workshop_routes(client):
    assert client.get("/workshop").status_code == 200
    r = client.get("/api/search", params={"q": "RAG chatbot"})
    assert r.status_code == 200 and "results" in r.json()
    r = client.post("/api/ml/classify", json={"text": "container image and CI pipeline"})
    assert r.status_code == 200 and r.json()["predictions"]
    r = client.post("/api/ask", json={"question": "what did he do at Hexango?"})
    assert r.status_code == 200


def test_ask_rate_limit(client):
    codes = [client.post("/api/ask", json={"question": f"q{i}"}).status_code for i in range(14)]
    assert 429 in codes
