# backend/agents/retrievers/retriever_trusted_web.py
from typing import Dict, Any, List
import os, requests, html
from ..base import Agent
from app.settings import SETTINGS

API = "https://api.search.brave.com/res/v1/web/search"  # or your provider
def _hdr(k: str) -> Dict[str, str]:
    return {"Accept": "application/json", "X-Subscription-Token": k, "User-Agent": "YT-HMD/1.0"}

def _snippet(item) -> str:
    return html.unescape(item.get("snippet") or item.get("description") or "")[:500]

class TrustedWebRetriever(Agent):
    name = "trusted_web"

    def __init__(self, top_k: int = 8):
        self.top_k = top_k
        self.key = os.getenv("BRAVE_SEARCH_API_KEY")  # set in .env

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text","")
        q = payload.get("query") or claim
        if not q or not self.key:
            return {"claim_text": claim, "evidence": []}

        # Add site limits to query
        sites = " OR ".join([f"site:{d}" for d in SETTINGS.trusted_domains])
        fullq = f"{q} ({sites})"

        try:
            r = requests.get(API, params={"q": fullq, "count": self.top_k}, headers=_hdr(self.key), timeout=8)
            r.raise_for_status()
            results = (r.json().get("web") or {}).get("results", [])[: self.top_k]
            ev: List[Dict[str, Any]] = []
            for it in results:
                url = it.get("url") or ""
                host = (it.get("meta", {}) or {}).get("site", "") or url
                ev.append({
                    "source": "trusted_web",
                    "title": it.get("title") or host,
                    "url": url,
                    "snippet": _snippet(it),
                    "confidence": 0.9
                })
            return {"claim_text": claim, "evidence": ev}
        except Exception:
            return {"claim_text": claim, "evidence": []}
