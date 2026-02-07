import platform
import subprocess
import webbrowser


_APP_ALIASES = {
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
}


def _open_app_macos(app_name: str) -> None:
    subprocess.run(["open", "-a", app_name], check=True)


def _open_url(url: str) -> None:
    webbrowser.open(url)


def _normalize_command(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_open_target(text: str) -> str | None:
    for prefix in ("open ", "launch ", "start "):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return None


def execute_command(command_text: str) -> dict:
    """
    Execute a simple natural-language command like:
    - "open apple music"
    - "open whatsapp"
    - "open https://youtube.com"
    Returns status + info.
    """
    normalized = _normalize_command(command_text)
    target = _extract_open_target(normalized)

    if not target:
        return {"status": "unknown", "info": "Unsupported command."}

    if target.startswith("http://") or target.startswith("https://"):
        _open_url(target)
        return {"status": "ok", "info": f"Opened URL: {target}"}

    app_name = _APP_ALIASES.get(target, target.title())
    if platform.system() == "Darwin":
        try:
            _open_app_macos(app_name)
            return {"status": "ok", "info": f"Opened app: {app_name}"}
        except subprocess.CalledProcessError as exc:
            return {"status": "error", "info": f"Failed to open app: {app_name}", "detail": str(exc)}

    return {"status": "error", "info": "Unsupported OS for app launch."}
