import os
import json
from typing import Dict, Any, List
from apps.api.services.model_router import GroqModelRouter

class TestGenerator:
    def __init__(self, router: GroqModelRouter):
        self.router = router

    async def generate(self, entities: Dict[str, Any], repro_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prompt_path = os.path.join("packages", "prompts", "generate_test_skeletons.md")
        system_instruction = "You are an expert test engineer. Output JSON with generated code."
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Entities:\n{json.dumps(entities)}\nRepro Steps:\n{json.dumps(repro_steps)}"}
        ]

        raw_output = await self.router.execute_stage(
            task_stage="test_generation",
            messages=messages,
            temperature=0.1
        )

        try:
            match = json.loads(raw_output.replace("```json", "").replace("```", "").strip())
            return match.get("test_artifacts", [])
        except Exception:
            return [
                {
                    "framework": "pytest",
                    "file_path": "tests/test_repro.py",
                    "code_content": "import pytest\n\ndef test_bug_reproduction():\n    # Auto-generated skeleton fallback\n    pass\n"
                }
            ]
