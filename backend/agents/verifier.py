import os, json
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, List
from .base import Agent
from app.utils import safe_json_extract

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class VerifierAgent(Agent):
    name = "verifier"
    def __init__(self, model_name: str = "gemini-2.0-flash-lite"):
        self.model = genai.GenerativeModel(model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type(Exception)
    )
    def _ask(self, claim: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        print("VerifierAgent: calling LLM")
        prompt = (
            "You are a claim verification assistant. "
            "Given a claim and short evidence snippets with sources, "
            "return STRICT JSON: {\"factual_confidence\": 0..1, \"rationale\": \"...\"}.\n"
            f"Claim: {claim}\n"
            f"Evidence: {json.dumps(evidence)}\n"
            "Rules: Respond ONLY with JSON. No prose."
        )
        resp = self.model.generate_content(prompt)
        return safe_json_extract(resp.text or "{}", {"factual_confidence":0.5,"rationale":"fallback"})

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload["claim_text"]
        evidence = payload.get("evidence", [])[:6]

        if not evidence:
            payload["factual_confidence"] = 0.5  # unknown, not false
            payload["verifier_rationale"] = "No suitable evidence retrieved quickly; abstaining (unknown)."
            payload["verifier_used_llm"] = False
            return payload

        try:
            data = self._ask(claim, evidence)
            payload["factual_confidence"] = float(data.get("factual_confidence", 0.5))
            payload["verifier_rationale"] = data.get("rationale", "")
        except Exception:
            payload["factual_confidence"] = 0.4
            payload["verifier_rationale"] = "LLM unavailable; used fallback."
        return payload
