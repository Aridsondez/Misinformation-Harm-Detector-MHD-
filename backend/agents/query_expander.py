# backend/agents/query_expander.py
from typing import Dict, Any, List
from .base import Agent
import os, re

HEALTH_MECH = ("dose","dosage","safety","guidelines","side effects","risk","contraindications","poison","ingestion","efficacy")
HEALTH_ORGS = ("CDC","WHO","NIH","NHS")
STOP = {"the","and","a","of","to","in","for","on","with","is","it","this","that","are","be","an","as","by","from"}

class QueryExpanderAgent(Agent):
    name = "query_expander"

    def _expand_llm(self, claim: str) -> List[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            prompt = (
                "Generate up to 6 short web search queries to fact-check a health advice claim. "
                "Include mechanism words (safety/guidelines/dosage/side effects) and health org acronyms (CDC/WHO/NIH/NHS). "
                "Return queries each on its own line, no numbering.\n\n"
                f"Claim: {claim}"
            )
            resp = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
            lines = [l.strip("-• ").strip() for l in (resp.text or "").splitlines() if l.strip()]
            out, seen = [], set()
            for q in lines:
                ql = q.lower()
                if ql and ql not in seen:
                    out.append(q); seen.add(ql)
                if len(out) >= 6:
                    break
            return out
        except Exception:
            return []

    def _fallback(self, claim: str) -> List[str]:
        toks = re.findall(r"[a-zA-Z0-9']+", claim.lower())
        core = " ".join([t for t in toks if t not in STOP][:6]) or claim
        qs = [f"{core} {m}" for m in HEALTH_MECH]
        # prefer site-limited style words for retriever
        qs += [f"{core} {org}" for org in HEALTH_ORGS]
        # compact & dedupe
        out, seen = [], set()
        for q in qs:
            q = q.strip()
            if q and q.lower() not in seen:
                out.append(q); seen.add(q.lower())
            if len(out) >= 6:
                break
        return out or [claim]

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        queries = self._expand_llm(claim) or self._fallback(claim)
        return {"claim_text": claim, "queries": queries}
