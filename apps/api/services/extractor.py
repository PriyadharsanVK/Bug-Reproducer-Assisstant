import os
import json
from typing import Dict, Any
from apps.api.services.model_router import GroqModelRouter
from apps.api.services.guardrails import HallucinationGuard

class EntityExtractor:
    def __init__(self, router: GroqModelRouter):
        self.router = router

    async def extract(self, title: str, body: str, raw_logs: str = "") -> Dict[str, Any]:
        prompt_path = os.path.join("packages", "prompts", "extract_entities.md")
        system_instruction = "You are a software triage assistant. Return JSON conforming to the schema."
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Issue Title: {title}\nIssue Body:\n{body}\nRaw Logs:\n{raw_logs or 'None'}"}
        ]

        raw_output = await self.router.execute_stage(
            task_stage="entity_extraction",
            messages=messages,
            temperature=0.1
        )
        
        parsed_data, ok = HallucinationGuard.enforce_schema_and_tripartition(
            raw_output, issue_body=body, raw_logs=raw_logs or ""
        )
        if not ok:
            return {
                "facts": {"error_message": title, "stack_trace": raw_logs, "file_paths": [], "explicit_versions": {}},
                "inferred_assumptions": [],
                "unknowns": ["runtime_environment"],
                "overall_confidence": 0.40
            }
        return parsed_data
