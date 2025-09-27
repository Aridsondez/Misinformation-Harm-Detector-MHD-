import requests
from typing import Dict, Any, List
from ..base import Agent

class WikipediaRetriever(Agent):
    name = "wikipedia"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        out: List[Dict[str, Any]] = []
        try:
            r = requests.get(
                "https://en.wikipedia.org/w/rest.php/v1/search/title",
                params={"q": claim, "limit": 3},
                timeout=5
            )
            r.raise_for_status()
            items = (r.json().get("pages") or [])[:3]
            for it in items:
                title = it.get("title")
                if not title: 
                    continue
                s = requests.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                    timeout=5
                )
                if s.ok:
                    j = s.json()
                    url = j.get("content_urls",{}).get("desktop",{}).get("page")
                    extract = (j.get("extract") or "")[:400]
                    if extract:
                        out.append({
                            "source":"Wikipedia",
                            "confidence": 0.65,  # baseline; refined by LLM
                            "snippet": extract,
                            "url": url
                        })
        except Exception:
            pass

        return {"claim_text": claim, "evidence": out}
