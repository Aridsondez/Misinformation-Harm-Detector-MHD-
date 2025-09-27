from typing import Dict, Any
from .base import Agent

class ActionAgent(Agent):
    name = "action"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        score = int(payload["harm_score"])
        if score < 25:
            action = "inform"
        elif score < 60:
            action = "flag"
        else:
            action = "alert"
        payload["action"] = action
        return payload
