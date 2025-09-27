# agents/harm_scorer_agent.py
import math, re
from typing import Dict, Any
from .base import Agent

POLICY = {
  "categories": {
    "health": {"keywords": ["bleach","chlorine","sodium hypochlorite","detox","dosage","mg","ml","ingest","drink","poison","medicine","cure","vaccine","antibiotic","inject","skin"], "base": 0.40},
    "civic":  {"keywords": ["election","vote","voting","ballot","polling","poll","primary","general","registration","vote by mail"], "base": 0.25},
    "neutral":{"keywords": [], "base": 0.05}
  },
  "high_risk": [r"\b(drink|ingest)\s+bleach\b", r"\bself[- ]?harm\b", r"\bsuicide\b"],
  "weights": {"bias": -1.2, "wF": 2.0, "wC": 2.0, "wN": 1.0, "wS": 2.5},
  "novelty": 0.10,
  "floor_high_risk": 0.75,
  "thresholds": {"inform": 40, "alert": 70}
}

def _category(t: str) -> str:
    tl = t.lower()
    best, hits = "neutral", 0
    for k, spec in POLICY["categories"].items():
        score = sum(1 for kw in spec["keywords"] if kw in tl)
        if score > hits: best, hits = k, score
    return best

def _high_risk(t: str) -> bool:
    tl = t.lower()
    return any(re.search(p, tl) for p in POLICY["high_risk"])

class HarmScorerAgent(Agent):
    name = "harm_scorer"
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text","")
        F = float(payload.get("factual_confidence", 0.5))
        has_ev = bool(payload.get("evidence"))
        cat = _category(claim)
        C = POLICY["categories"][cat]["base"]
        N = POLICY["novelty"] if not has_ev else 0.0
        S = 0.40 if _high_risk(claim) else 0.0

        w = POLICY["weights"]
        z = w["bias"] + w["wF"]*(1.0 - F) + w["wC"]*C + w["wN"]*N + w["wS"]*S
        harm = int(round(100 * (1 / (1 + math.exp(-z)))))

        if _high_risk(claim):
            harm = max(harm, int(100*POLICY["floor_high_risk"]))

        thr = POLICY["thresholds"]
        action = "inform" if harm < thr["inform"] else ("alert" if harm > thr["alert"] else "flag")

        payload["harm_score"] = harm
        payload["action"] = action
        payload["category"] = cat
        payload["harm_breakdown"] = {"F": F, "C": C, "N": N, "S": S, "z": z}
        return payload
