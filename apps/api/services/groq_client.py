import os
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.timeout = float(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))
        self.max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if response_format:
            payload["response_format"] = response_format

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.warning(f"Groq API call attempt {attempt}/{self.max_retries} for model '{model}' failed: {e}")
                last_exception = e
                # 400 errors are client-side (bad model ID, invalid params) — no point retrying
                if e.response.status_code == 400:
                    logger.error(
                        f"Groq returned 400 Bad Request for model '{model}'. "
                        "The model may be decommissioned or the request is malformed. Skipping retries."
                    )
                    break
            except Exception as e:
                logger.warning(f"Groq API call attempt {attempt}/{self.max_retries} for model '{model}' failed: {e}")
                last_exception = e

        raise RuntimeError(f"Groq API call failed after {self.max_retries} attempts: {last_exception}")
