# agents/reranker_agent.py
from typing import Dict, Any, List
from .base import Agent

class RerankerAgent(Agent):
    name = "reranker"
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        ev: List[Dict[str, Any]] = payload.get("evidence", [])
        if not ev: return payload

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        docs = [claim] + [ (e.get("title","") + " " + e.get("snippet","")) for e in ev ]
        vec = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
        X = vec.fit_transform(docs)
        sims = cosine_similarity(X[0:1], X[1:]).ravel()

        for s, e in sorted(zip(sims, ev), key=lambda x: x[0], reverse=True):
            e["score"] = float(s)
        ev = sorted(ev, key=lambda e: e.get("score", 0.0), reverse=True)[:6]

        payload["evidence"] = ev
        return payload
