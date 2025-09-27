# agents/query_expander_agent.py
from typing import Dict, Any, List
from .base import Agent
import os

class QueryExpanderAgent(Agent):
    name = "query_expander"

    def _expand_llm(self, claim: str) -> List[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            prompt = f"Generate 3 concise search queries to fact-check this claim:\n\n{claim}\n"
            resp = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
            lines = [l.strip("-• ").strip() for l in resp.text.splitlines() if l.strip()]
            return [q for q in lines[:3] if len(q) >= 3]
        except Exception:
            return []

    def _fallback(self, claim: str) -> List[str]:
        import re
        toks = re.findall(r"[a-zA-Z0-9']+", claim.lower())
        stop = {"the","and","a","of","to","in","for","on","with","is","it","this","that","are","be","an","as","by","from"}
        kw = " ".join([t for t in toks if t not in stop][:6])
        return [kw] if kw else [claim]

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        queries = self._expand_llm(claim) or self._fallback(claim)
        return {"claim_text": claim, "queries": queries}
