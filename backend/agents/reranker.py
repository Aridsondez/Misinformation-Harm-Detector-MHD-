# backend/agents/reranker.py
from typing import Dict, Any, List
from .base import Agent
from app.settings import SETTINGS

class RerankerAgent(Agent):
    name = "reranker"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = (payload.get("claim_text") or "").strip()
        ev: List[Dict[str, Any]] = payload.get("evidence", []) or []
        if not claim or not ev:
            payload["evidence"] = []
            payload["evidence_relevance"] = 0.0
            return payload

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        docs = [claim] + [(e.get("title", "") + " " + (e.get("snippet") or "")) for e in ev]
        vec = TfidfVectorizer(max_features=SETTINGS.tfidf_max_features, ngram_range=(SETTINGS.tfidf_ngram_lo, SETTINGS.tfidf_ngram_hi))
        X = vec.fit_transform(docs)
        sims = cosine_similarity(X[0:1], X[1:]).ravel()

        for s, e in zip(sims, ev):
            e["score"] = float(s)

        # filter & sort
        filtered = [e for e in ev if e["score"] >= SETTINGS.min_cosine]
        filtered.sort(key=lambda x: x["score"], reverse=True)
        kept = filtered[: SETTINGS.max_evidence]

        # relevance metric
        if kept:
            rel = sum(e["score"] for e in kept) / len(kept)
        else:
            rel = float(max(sims) if len(sims) else 0.0)

        payload["evidence"] = kept
        payload["evidence_relevance"] = rel
        return payload
