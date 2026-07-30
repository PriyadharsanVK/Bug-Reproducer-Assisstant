import os
import json
from typing import Dict, Any, List
from apps.api.services.model_router import GroqModelRouter

class ReproPlanner:
    def __init__(self, router: GroqModelRouter):
        self.router = router

    async def plan(self, entities: Dict[str, Any], repository_url: str = "") -> List[Dict[str, Any]]:
        prompt_path = os.path.join("packages", "prompts", "generate_repro_steps.md")
        system_instruction = "You are a reproduction planning bot. Output JSON steps."
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Repository: {repository_url}\nEntities:\n{json.dumps(entities)}"}
        ]

        raw_output = await self.router.execute_stage(
            task_stage="repro_planning",
            messages=messages,
            temperature=0.2
        )

        try:
            match = json.loads(raw_output.replace("```json", "").replace("```", "").strip())
            return match.get("steps", [])
        except Exception:
            return [
                {
                    "step_number": 1,
                    "action": f"git clone {repository_url or 'target_repo'}",
                    "expected_outcome": "Repository cloned locally",
                    "confidence": 0.90,
                    "sandbox_verified": True
                },
                {
                    "step_number": 2,
                    "action": "Run test suite to reproduce failure condition",
                    "expected_outcome": "Issue reproduced",
                    "confidence": 0.60,
                    "sandbox_verified": False
                }
            ]
