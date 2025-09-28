# backend/agents/claim_extractor.py
import re
from typing import Dict, Any, List
from .base import Agent

ADVICE_PATTERNS = [
    r"\b(you should|you must|you need to|try to|i recommend|we recommend)\b",
    r"\b(take|drink|apply|inject|consume|use|swallow|inhale|rub|drop|dose)\b\s+\b([a-zA-Z0-9\-]+)\b",
    r"\b(cures?|prevents?|treats?|detox(es)?|heals?)\b",
    r"\b(dosage|dose|mg|ml|pills?|capsules?|drops?)\b",
]

class ClaimExtractor(Agent):
    name = "claim_extractor"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript: List[Dict[str, Any]] = payload.get("transcript", [])
        claims: List[Dict[str, Any]] = []
        for seg in transcript:
            text = (seg.get("text") or "").strip()
            low = text.lower()
            if not low:
                continue
            for pat in ADVICE_PATTERNS:
                if re.search(pat, low):
                    claims.append({"claim_text": text, "start": float(seg.get("start", 0.0))})
                    break
        return {"claim_candidates": claims}
