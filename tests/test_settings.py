"""Tests for cdash settings management."""

from pathlib import Path
import json

import pytest

from cdash.data.settings import (
    CdashSettings,
    load_settings,
    save_settings,
    get_settings_path,
)


class TestLoadSettings:
    """Tests for loading settings."""

    def test_returns_defaults_when_file_missing(self, tmp_path: Path):
        """Returns default settings when file doesn't exist."""
        settings_path = tmp_path / "cdash-settings.json"
        result = load_settings(settings_path)
        assert result.discovered_repos == []
        assert result.hidden_repos == []

    def test_loads_existing_settings(self, tmp_path: Path):
        """Loads settings from existing file."""
        settings_path = tmp_path / "cdash-settings.json"
        settings_path.write_text(json.dumps({
            "github_actions": {
                "discovered_repos": ["owner/repo1", "owner/repo2"],
                "hidden_repos": ["owner/hidden"],
                "last_discovery": "2026-01-17T10:00:00Z"
            }
        }))
        result = load_settings(settings_path)
        assert result.discovered_repos == ["owner/repo1", "owner/repo2"]
        assert result.hidden_repos == ["owner/hidden"]


class TestSaveSettings:
    """Tests for saving settings."""

    def test_saves_settings_to_file(self, tmp_path: Path):
        """Saves settings to JSON file."""
        settings_path = tmp_path / "cdash-settings.json"
        settings = CdashSettings(
            discovered_repos=["owner/repo"],
            hidden_repos=["owner/hidden"],
            last_discovery="2026-01-17T12:00:00Z"
        )
        save_settings(settings, settings_path)

        data = json.loads(settings_path.read_text())
        assert data["github_actions"]["discovered_repos"] == ["owner/repo"]
        assert data["github_actions"]["hidden_repos"] == ["owner/hidden"]
