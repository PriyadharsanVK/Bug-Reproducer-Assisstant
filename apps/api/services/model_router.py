import os
import logging
from typing import List, Dict, Any, Optional
from apps.api.services.groq_client import GroqClient

logger = logging.getLogger(__name__)

class GroqModelRouter:
    def __init__(self, client: Optional[GroqClient] = None):
        self.client = client or GroqClient()
        self.primary_model = os.getenv("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile")
        self.fast_model = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
        self.code_model = os.getenv("GROQ_MODEL_CODE", "deepseek-r1-distill-llama-70b")

    def resolve_model_for_task(self, task_stage: str) -> str:
        """Route pipeline stages to specific Groq model targets."""
        mapping = {
            "entity_extraction": self.primary_model,
            "clarifications": self.fast_model,
            "repro_planning": self.primary_model,
            "env_matrix": self.primary_model,
            "test_generation": self.code_model,
            "hypotheses": self.primary_model,
            "report_synthesis": self.primary_model,
        }
        return mapping.get(task_stage, self.primary_model)

    async def execute_stage(
        self,
        task_stage: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        target_model = self.resolve_model_for_task(task_stage)
        logger.info(f"Executing pipeline stage '{task_stage}' on Groq model '{target_model}'")
        
        try:
            return await self.client.chat_completion(
                model=target_model,
                messages=messages,
                temperature=temperature,
                response_format=response_format
            )
        except Exception as e:
            # Fallback strategy: If code generation model fails, fallback to primary 70b versatile
            if target_model == self.code_model:
                logger.warning(
                    f"Code model '{self.code_model}' failed for stage '{task_stage}'. "
                    f"Executing fallback to primary model '{self.primary_model}'. Error: {e}"
                )
                return await self.client.chat_completion(
                    model=self.primary_model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format
                )
            raise e
