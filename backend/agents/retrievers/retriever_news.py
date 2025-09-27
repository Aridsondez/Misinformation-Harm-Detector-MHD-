import os, requests
from typing import Dict, Any, List
from ..base import Agent

NEWSAPI = "https://newsapi.org/v2/everything"

class NewsRetriever(Agent):
    name = "news"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        key = os.getenv("NEWSAPI_KEY")
        out: List[Dict[str, Any]] = []
        if not key:
            return {"claim_text": claim, "evidence": out}  # gracefully skip

        try:
            r = requests.get(
                NEWSAPI,
                params={"q": claim, "pageSize": 3, "sortBy":"relevancy", "language":"en"},
                headers={"X-Api-Key": key},
                timeout=5
            )
            r.raise_for_status()
            arts = (r.json().get("articles") or [])[:3]
            for a in arts:
                snippet = ((a.get("title") or "") + ". " + (a.get("description") or ""))[:320]
                url = a.get("url")
                if snippet:
                    out.append({
                        "source":"News",
                        "confidence":0.55,
                        "snippet": snippet,
                        "url": url
                    })
        except Exception:
            pass

        return {"claim_text": claim, "evidence": out}
