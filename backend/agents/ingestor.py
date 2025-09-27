from typing import Dict, Any
from .base import Agent

class IngestorAgent(Agent):
    name = "ingestor"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text: str = payload.get("text", "")
        norm = " ".join(text.split()).strip().lower()
        return {"claim_text": norm}
