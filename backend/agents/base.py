from typing import Any, Dict

class Agent:
    name: str = "agent"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
