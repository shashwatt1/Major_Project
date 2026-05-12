"""
automator.py — Natural-language command executor.

Handles voice commands like:
  "open chrome"
  "please open Safari for me"
  "launch WhatsApp"
  "open https://youtube.com"
"""
from __future__ import annotations

import platform
import re
import subprocess
import webbrowser


# ── Known app aliases (all keys must be lowercase) ───────────────────────────
_APP_ALIASES: dict[str, str] = {
    "music": "Music",
    "apple music": "Music",
    "itunes": "Music",
    "safari": "Safari",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "whatsapp": "WhatsApp",
    "notes": "Notes",
    "calendar": "Calendar",
    "terminal": "Terminal",
    "finder": "Finder",
    "settings": "System Settings",
    "system settings": "System Settings",
    "system preferences": "System Settings",
    "vscode": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "slack": "Slack",
    "zoom": "Zoom",
    "spotify": "Spotify",
    "vlc": "VLC",
    "mail": "Mail",
    "maps": "Maps",
    "photos": "Photos",
    "messages": "Messages",
    "facetime": "FaceTime",
}


def _normalize(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove trailing punctuation."""
    text = text.lower().strip()
    text = " ".join(text.split())
    text = re.sub(r"[.!?,;]+$", "", text).strip()
    return text


def _open_app_macos(app_name: str) -> dict:
    try:
        subprocess.run(["open", "-a", app_name], check=True, timeout=10)
        return {"status": "ok", "info": f"Opened {app_name}."}
    except subprocess.CalledProcessError:
        return {"status": "error", "info": f"Could not find app '{app_name}'. Is it installed?"}
    except FileNotFoundError:
        return {"status": "error", "info": "The 'open' command is not available on this system."}


def execute_command(command_text: str) -> dict:
    """
    Execute a natural-language voice command. Handles:
      - Any URL starting with http:// or https://
      - Known app names even inside longer sentences
      - Graceful fallback when no command is recognized
    """
    normalized = _normalize(command_text)

    # ── 1. URL anywhere in the utterance ─────────────────────────────────────
    url_match = re.search(r"https?://[^\s]+", command_text)
    if url_match:
        url = url_match.group()
        webbrowser.open(url)
        return {"status": "ok", "info": f"Opened URL: {url}"}

    # ── 2. Scan for any known alias ANYWHERE in the normalized text ───────────
    # Sort by length descending so "google chrome" matches before "chrome"
    for alias in sorted(_APP_ALIASES, key=len, reverse=True):
        if alias in normalized:
            app_name = _APP_ALIASES[alias]
            if platform.system() == "Darwin":
                return _open_app_macos(app_name)
            return {"status": "error", "info": "App launch is only supported on macOS."}

    # ── 3. Generic "open <something>" fallback ────────────────────────────────
    generic_match = re.search(
        r"\b(?:open|launch|start)\b\s+(.+)", normalized
    )
    if generic_match:
        raw_target = generic_match.group(1).strip()
        # Drop trailing filler words like "please", "for me", "now"
        raw_target = re.split(r"\b(?:please|for|now|on my|me)\b", raw_target)[0].strip()
        if raw_target:
            app_name = raw_target.title()
            if platform.system() == "Darwin":
                return _open_app_macos(app_name)

    return {
        "status": "unknown",
        "info": (
            "I didn't recognize that command. "
            "Try saying: 'open Chrome', 'open Safari', or 'open https://youtube.com'."
        ),
    }
