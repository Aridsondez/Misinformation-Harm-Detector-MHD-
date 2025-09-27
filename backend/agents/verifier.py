from typing import Dict, Any, List
from .base import Agent

class VerifierAgent(Agent):
    name = "verifier"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        evidence: List[Dict[str, Any]] = payload.get("evidence", [])
        # Simple heuristic: factual confidence = max confidence in evidence
        factual_conf = max((e.get("confidence", 0.0) for e in evidence), default=0.0)
        return {
            "claim_text": payload["claim_text"],
            "evidence": evidence,
            "factual_confidence": float(factual_conf)
        }
