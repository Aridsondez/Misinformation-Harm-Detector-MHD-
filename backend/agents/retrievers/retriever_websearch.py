from typing import Dict, Any, List
import os, requests, html
from ..base import Agent

API = "https://api.search.brave.com/res/v1/web/search"
HDR = lambda k: {"Accept":"application/json","X-Subscription-Token":k, "User-Agent":"MHD/1.0"}

def _snippet(x):
    t = x.get("snippet") or x.get("description") or ""
    return html.unescape(t)[:500]

TRUSTED = {
    # science/policy
    "nature.com","science.org","arxiv.org","openalex.org","oecd.org","iea.org",
    "who.int","nih.gov","epa.gov","noaa.gov","un.org","unicef.org",
    # news (adjust as you like)
    "bbc.com","nytimes.com","apnews.com","reuters.com","theguardian.com",
}

class WebSearchRetriever(Agent):
    name = "websearch"

    def __init__(self, top_k: int = 6):
        self.top_k = top_k
        self.key = os.getenv("BRAVE_SEARCH_API_KEY")  # set this!

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text","")
        q = payload.get("query") or claim
        if not self.key or not q:
            return {"claim_text": claim, "evidence": []}

        try:
            r = requests.get(API, params={"q": q, "count": 8, "freshness":"month"},
                             headers=HDR(self.key), timeout=8)
            r.raise_for_status()
            j = r.json()
            items = (j.get("web",{}) or {}).get("results",[])[:12]
            ev: List[Dict[str,Any]] = []
            for it in items:
                url = it.get("url") or ""
                host = it.get("meta",{}).get("site","").lower()
                # light trust filter (optional): prefer trusted; still allow others if nothing else
                score = 1.0 if any(host.endswith(d) for d in TRUSTED) else 0.6
                ev.append({
                    "source": "web",
                    "title": it.get("title") or host or url,
                    "url": url,
                    "snippet": _snippet(it),
                    "confidence": score
                })
            # prefer trusted first
            ev.sort(key=lambda e: e.get("confidence",0.0), reverse=True)
            return {"claim_text": claim, "evidence": ev[:self.top_k]}
        except Exception:
            return {"claim_text": claim, "evidence": []}
