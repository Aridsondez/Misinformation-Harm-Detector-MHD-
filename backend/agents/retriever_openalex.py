# backend/agents/retrievers/retriever_openalex.py
from typing import Dict, Any, List
import requests, html
from ..base import Agent

API = "https://api.openalex.org/works"

class OpenAlexRetriever(Agent):
    name = "openalex"

    def __init__(self, top_k: int = 8):
        self.top_k = top_k

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text","")
        q = payload.get("query") or claim
        if not q:
            return {"claim_text": claim, "evidence": []}
        try:
            r = requests.get(API, params={"search": q, "per_page": self.top_k, "sort": "relevance_score:desc"}, timeout=8)
            r.raise_for_status()
            data = r.json().get("results", [])
            ev: List[Dict[str,Any]] = []
            for w in data[: self.top_k]:
                title = w.get("title") or ""
                abs_ = w.get("abstract") or w.get("abstract_inverted_index") or ""
                if isinstance(abs_, dict):
                    # reconstruct a rough abstract
                    tokens = []
                    inv = abs_
                    for tok, poss in inv.items():
                        tokens.extend([tok] * len(poss))
                    abs_ = " ".join(tokens)
                url = (w.get("primary_location",{}) or {}).get("landing_page_url") \
                      or (w.get("open_access",{}) or {}).get("oa_url") or ""
                ev.append({
                    "source": "openalex",
                    "title": title[:300],
                    "url": url,
                    "snippet": html.unescape(str(abs_))[:500],
                    "confidence": 0.7
                })
            return {"claim_text": claim, "evidence": ev}
        except Exception:
            return {"claim_text": claim, "evidence": []}
