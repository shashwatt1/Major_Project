from __future__ import annotations


COMMAND_KEYWORDS = (
    "open",
    "launch",
    "start",
    "play",
    "close",
)


def classify_intent(text: str) -> str:
    normalized = text.lower().strip()
    if any(keyword in normalized for keyword in COMMAND_KEYWORDS):
        return "command"
    return "query"
