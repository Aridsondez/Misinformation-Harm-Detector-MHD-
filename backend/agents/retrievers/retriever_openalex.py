from typing import Dict, Any, List
import requests, html
from ..base import Agent

API = "https://api.openalex.org/works"

class OpenAlexRetriever(Agent):
    name = "openalex"

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text","")
        q = payload.get("query") or claim
        if not q:
            return {"claim_text": claim, "evidence": []}
        try:
            r = requests.get(API, params={"search": q, "per_page": 10, "sort": "relevance_score:desc"}, timeout=8)
            r.raise_for_status()
            data = r.json().get("results", [])
            ev: List[Dict[str,Any]] = []
            for w in data[: self.top_k]:
                title = w.get("title") or ""
                abs_ = w.get("abstract") or w.get("abstract_inverted_index") or ""
                # Flatten inverted index if needed
                if isinstance(abs_, dict):
                    tokens = []
                    inv = abs_
                    # reconstruct rough abstract
                    for word, positions in inv.items():
                        for _ in positions: tokens.append(word)
                    abs_ = " ".join(tokens)[:600]
                url = (w.get("primary_location",{}) or {}).get("landing_page_url") or w.get("open_access",{}).get("oa_url") or ""
                ev.append({
                    "source": "openalex",
                    "title": title,
                    "url": url,
                    "snippet": html.unescape(str(abs_))[:500],
                    "confidence": 0.9
                })
            return {"claim_text": claim, "evidence": ev}
        except Exception:
            return {"claim_text": claim, "evidence": []}
