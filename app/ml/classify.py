"""A small TF-IDF + logistic-regression classifier: which software area is
this text about? Trained in-process on first use (see app/ml/data.py).

sklearn is imported lazily so it never touches the request path unless the
classify endpoint is actually used.
"""

from __future__ import annotations

from functools import lru_cache

from app.ml.data import SAMPLES


@lru_cache(maxsize=1)
def _model():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    x, y = zip(*SAMPLES, strict=True)
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1000, C=4.0, solver="liblinear")),
        ]
    )
    pipe.fit(x, y)
    return pipe


def predict(text: str) -> list[dict]:
    text = (text or "").strip()
    if not text:
        return []
    pipe = _model()
    probs = pipe.predict_proba([text])[0]
    ranked = sorted(zip(pipe.classes_, probs, strict=True), key=lambda t: -t[1])
    return [{"label": label, "prob": round(float(p), 3)} for label, p in ranked]
