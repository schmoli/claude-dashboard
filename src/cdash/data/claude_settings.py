"""Read/write Claude Code's settings.json for plugin enable/disable state."""

import json
from pathlib import Path


def get_claude_settings_path() -> Path:
    """Get path to Claude Code's settings.json."""
    return Path.home() / ".claude" / "settings.json"


def load_enabled_plugins(path: Path | None = None) -> dict[str, bool]:
    """Load enabled plugins dict from settings.json.

    Returns empty dict if file doesn't exist or has no enabledPlugins.
    """
    if path is None:
        path = get_claude_settings_path()

    if not path.exists():
        return {}

    try:
        with path.open() as f:
            data = json.load(f)
        return data.get("enabledPlugins", {})
    except (json.JSONDecodeError, OSError):
        return {}


def set_plugin_enabled(plugin_id: str, enabled: bool, path: Path | None = None) -> None:
    """Set a plugin's enabled state in settings.json.

    Creates the file if it doesn't exist. Preserves all other settings.
    """
    if path is None:
        path = get_claude_settings_path()

    # Load existing settings or start fresh
    if path.exists():
        try:
            with path.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
        path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure enabledPlugins exists
    if "enabledPlugins" not in data:
        data["enabledPlugins"] = {}

    # Set the plugin state
    data["enabledPlugins"][plugin_id] = enabled

    # Write back
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def get_plugin_id(name: str, source: str) -> str:
    """Generate plugin ID from name and source.

    Format: {name}@{source}
    """
    return f"{name}@{source}"
