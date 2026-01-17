"""Cdash settings management."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CdashSettings:
    """Settings for cdash application."""

    discovered_repos: list[str] = field(default_factory=list)
    hidden_repos: list[str] = field(default_factory=list)
    last_discovery: str | None = None


def get_settings_path() -> Path:
    """Get path to cdash settings file."""
    return Path.home() / ".claude" / "cdash-settings.json"


def load_settings(settings_path: Path | None = None) -> CdashSettings:
    """Load settings from file, returning defaults if missing."""
    if settings_path is None:
        settings_path = get_settings_path()

    if not settings_path.exists():
        return CdashSettings()

    try:
        with settings_path.open() as f:
            data = json.load(f)
        gh = data.get("github_actions", {})
        return CdashSettings(
            discovered_repos=gh.get("discovered_repos", []),
            hidden_repos=gh.get("hidden_repos", []),
            last_discovery=gh.get("last_discovery"),
        )
    except (json.JSONDecodeError, OSError):
        return CdashSettings()


def save_settings(settings: CdashSettings, settings_path: Path | None = None) -> None:
    """Save settings to file."""
    if settings_path is None:
        settings_path = get_settings_path()

    data = {
        "github_actions": {
            "discovered_repos": settings.discovered_repos,
            "hidden_repos": settings.hidden_repos,
            "last_discovery": settings.last_discovery,
        }
    }

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w") as f:
        json.dump(data, f, indent=2)
