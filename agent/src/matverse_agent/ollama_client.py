from __future__ import annotations

from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 600) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "think": True,
            "options": {"temperature": 0.2},
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc
        data = response.json()
        message = data.get("message")
        if not isinstance(message, dict):
            raise OllamaError("Ollama returned no message object")
        return message

    def models(self) -> list[str]:
        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama health check failed: {exc}") from exc
        data = response.json()
        models = data.get("models", [])
        return [str(item.get("name")) for item in models if isinstance(item, dict)]

    def doctor(self) -> dict[str, Any]:
        models = self.models()
        return {
            "status": "PASS" if self.model in models else "HOLD",
            "ollama_url": self.base_url,
            "configured_model": self.model,
            "installed_models": models,
            "model_installed": self.model in models,
        }
