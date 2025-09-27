from typing import Dict, Any
from .ingestor import IngestorAgent
from .retriever import RetrieverAgent
from .verifier import VerifierAgent
from .harm_scorer import HarmScorerAgent
from .action import ActionAgent

class Orchestrator:
    def __init__(self):
        self.ingestor = IngestorAgent()
        self.retriever = RetrieverAgent()
        self.verifier = VerifierAgent()
        self.scorer = HarmScorerAgent()
        self.action = ActionAgent()
    
    def run_pipeline(self, text: str) -> Dict[str, Any]:
        step1 = self.ingestor.run({"text": text})
        step2 = self.retriever.run(step1)
        step3 = self.verifier.run(step2)
        step4 = self.scorer.run(step3)
        step5 = self.action.run(step4)
        return step5
