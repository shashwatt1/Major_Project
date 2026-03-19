from __future__ import annotations

import os

def _get_client():
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def get_response(prompt: str, user_id: str | None = None) -> str:
    """
    Send a single prompt to OpenAI and return the generated text.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful voice assistant. Be concise and accurate.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        user=user_id,
    )

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return text
