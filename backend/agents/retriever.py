import json
from pathlib import Path
from typing import Dict, Any, List
from .base import Agent

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "evidence.json"


class RetrieverAgent(Agent):
    name = "retriever"

    def __init__(self, fixture_path: Path = FIXTURE_PATH):
        self.fixture_path = fixture_path
        with open(self.fixture_path, "r") as f:
            self._evidence = json.load(f)

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim_text = payload["claim_text"]
        matches: List[Dict[str, Any]] = []
        for row in self._evidence:
            if row["claim_text"] == claim_text:
                matches = row["evidence"]
                break
        return {"claim_text": claim_text, "evidence": matches}
