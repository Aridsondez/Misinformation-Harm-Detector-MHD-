from typing import Dict, Any
from .base import Agent

class ActionAgent(Agent):
    name = "action"
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        s = int(payload["harm_score"])
        action = "inform" if s < 25 else "flag" if s < 60 else "alert"
        payload["action"] = action
        return payload
