import os
import json
from typing import Any, Dict, List
from apps.api.services.model_router import GroqModelRouter
from apps.api.services.guardrails import HallucinationGuard

class HypothesisEngine:
    def __init__(self, router: GroqModelRouter):
        self.router = router

    async def analyze(
        self,
        entities: Dict[str, Any],
        issue_body: str = "",
        raw_logs: str = ""
    ) -> List[Dict[str, Any]]:
        prompt_path = os.path.join("packages", "prompts", "generate_hypotheses.md")
        system_instruction = "You are a root cause hypothesis engine. Return JSON hypotheses."
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extracted Entities:\n{json.dumps(entities)}"}
        ]

        raw_output = await self.router.execute_stage(
            task_stage="hypotheses",
            messages=messages,
            temperature=0.2
        )

        facts = entities.get("facts", {})

        try:
            match = json.loads(raw_output.replace("```json", "").replace("```", "").strip())
            hypotheses = match.get("hypotheses", [])
        except Exception:
            # Fallback hypothesis — still subject to grounding validation below.
            hypotheses = [
                {
                    "category": "Configuration / Missing Parameter",
                    "title": "Uninitialized default configuration key",
                    "evidence": [facts.get("error_message")] if facts.get("error_message") else [],
                    "probability": 0.75
                }
            ]

        # Validate every hypothesis's evidence against the raw source material.
        # Hypotheses with null/empty/unverifiable evidence are capped at 0.30.
        return HallucinationGuard.validate_hypotheses(
            hypotheses=hypotheses,
            facts=facts,
            issue_body=issue_body,
            raw_logs=raw_logs
        )

