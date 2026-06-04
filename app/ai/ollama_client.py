from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel
from tenacity import retry, wait_exponential, stop_after_attempt

from app.core.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(4))
    async def generate_json(self, prompt: str, response_schema: str) -> dict[str, Any]:
        # OLLAMA /api/generate returns text; we rely on prompt to output JSON.
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()

        text = data.get("response") or ""
        text = text.strip()

        # Extract JSON (in case model wraps it)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # best-effort: locate first { ... last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
            raise

