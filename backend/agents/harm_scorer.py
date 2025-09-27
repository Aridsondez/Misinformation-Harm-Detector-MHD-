from typing import Dict, Any, List
from .base import Agent

class HarmScorerAgent(Agent):
    name = "harm_scorer"

    def _reach_score(self, claim_text: str) -> float:
        # Heuristic: “hot topics” get higher reach. Tweak as you like.
        hot = ["covid", "election", "war", "5g", "bleach"]
        return 1.0 if any(w in claim_text for w in hot) else 0.2

    def _safety_risk(self, claim_text: str) -> float:
        # Heuristic: ingesting bleach etc = high safety risk
        danger = ["bleach", "poison", "self-harm"]
        return 1.0 if any(w in claim_text for w in danger) else 0.4

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim_text = payload["claim_text"]
        evidence: List[Dict[str, Any]] = payload["evidence"]
        factual_conf = payload.get("factual_confidence", 0.0)

        # Using the README formula idea:
        # Harm = 50*(1 - F) + 20*Reach + 20*Safety + T (we’ll set T=0 in MVP)
        reach = self._reach_score(claim_text)     # 0..1
        safety = self._safety_risk(claim_text)    # 0..1
        t_mod = 0.0

        harm = int(round(
            max(0, min(100, 50*(1.0 - factual_conf) + 20*reach + 20*safety + t_mod))
        ))

        return {
            "claim_text": claim_text,
            "evidence": evidence,
            "factual_confidence": float(factual_conf),
            "harm_score": harm
        }
