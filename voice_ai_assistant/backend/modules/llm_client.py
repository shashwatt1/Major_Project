"""
LLM client — uses Ollama local API (no OpenAI key required).
Model: llama3.2 (already pulled).

Ollama must be running:  ollama serve
"""
from __future__ import annotations

import os

import httpx

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT = (
    "You are a helpful voice assistant. "
    "Give concise, accurate answers suitable for voice output. "
    "Avoid markdown, bullet points, or special characters — plain text only."
)


def get_response(prompt: str, user_id: str | None = None) -> str:  # noqa: ARG001
    """
    Send a prompt to the local Ollama API and return the generated text.
    Raises RuntimeError on failure.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"System: {SYSTEM_PROMPT}\n\nUser: {prompt}\n\nAssistant:",
        "stream": False,
    }

    try:
        response = httpx.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        text = (data.get("response") or "").strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response.")
        return text
    except httpx.ConnectError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure it is running: run 'ollama serve' in a terminal."
        )
    except httpx.TimeoutException:
        raise RuntimeError("Ollama request timed out (>60 s). The model may still be loading.")
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Ollama API error {exc.response.status_code}: {exc.response.text}") from exc
