"""Tests for Claude Code settings.json handling."""

import json
from pathlib import Path

from cdash.data.claude_settings import (
    get_plugin_id,
    load_enabled_plugins,
    set_plugin_enabled,
)


class TestLoadEnabledPlugins:
    """Tests for load_enabled_plugins."""

    def test_missing_file_returns_empty(self, tmp_path: Path):
        """Missing settings.json returns empty dict."""
        settings_path = tmp_path / "settings.json"
        result = load_enabled_plugins(settings_path)
        assert result == {}

    def test_empty_file_returns_empty(self, tmp_path: Path):
        """Empty JSON object returns empty dict."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{}")
        result = load_enabled_plugins(settings_path)
        assert result == {}

    def test_no_enabled_plugins_key(self, tmp_path: Path):
        """Settings without enabledPlugins returns empty dict."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"otherKey": "value"}))
        result = load_enabled_plugins(settings_path)
        assert result == {}

    def test_loads_enabled_plugins(self, tmp_path: Path):
        """Loads enabledPlugins from settings."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "enabledPlugins": {
                "plugin1@source1": True,
                "plugin2@source2": False,
            }
        }))
        result = load_enabled_plugins(settings_path)
        assert result == {
            "plugin1@source1": True,
            "plugin2@source2": False,
        }

    def test_invalid_json_returns_empty(self, tmp_path: Path):
        """Invalid JSON returns empty dict."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("not valid json")
        result = load_enabled_plugins(settings_path)
        assert result == {}


class TestSetPluginEnabled:
    """Tests for set_plugin_enabled."""

    def test_creates_file_if_missing(self, tmp_path: Path):
        """Creates settings.json if it doesn't exist."""
        settings_path = tmp_path / "settings.json"
        set_plugin_enabled("plugin@source", True, settings_path)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text())
        assert data == {"enabledPlugins": {"plugin@source": True}}

    def test_creates_parent_dirs(self, tmp_path: Path):
        """Creates parent directories if they don't exist."""
        settings_path = tmp_path / "subdir" / "settings.json"
        set_plugin_enabled("plugin@source", False, settings_path)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text())
        assert data["enabledPlugins"]["plugin@source"] is False

    def test_preserves_other_keys(self, tmp_path: Path):
        """Preserves other settings keys when writing."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "apiKey": "secret",
            "theme": "dark",
            "enabledPlugins": {"existing@src": True},
        }))

        set_plugin_enabled("new@source", False, settings_path)

        data = json.loads(settings_path.read_text())
        assert data["apiKey"] == "secret"
        assert data["theme"] == "dark"
        assert data["enabledPlugins"]["existing@src"] is True
        assert data["enabledPlugins"]["new@source"] is False

    def test_updates_existing_plugin(self, tmp_path: Path):
        """Updates existing plugin state."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "enabledPlugins": {"plugin@source": True},
        }))

        set_plugin_enabled("plugin@source", False, settings_path)

        data = json.loads(settings_path.read_text())
        assert data["enabledPlugins"]["plugin@source"] is False

    def test_toggle_multiple_times(self, tmp_path: Path):
        """Can toggle plugin state multiple times."""
        settings_path = tmp_path / "settings.json"

        set_plugin_enabled("plugin@source", True, settings_path)
        data = json.loads(settings_path.read_text())
        assert data["enabledPlugins"]["plugin@source"] is True

        set_plugin_enabled("plugin@source", False, settings_path)
        data = json.loads(settings_path.read_text())
        assert data["enabledPlugins"]["plugin@source"] is False

        set_plugin_enabled("plugin@source", True, settings_path)
        data = json.loads(settings_path.read_text())
        assert data["enabledPlugins"]["plugin@source"] is True


class TestGetPluginId:
    """Tests for get_plugin_id."""

    def test_formats_plugin_id(self):
        """Formats plugin ID as name@source."""
        assert get_plugin_id("my-plugin", "my-source") == "my-plugin@my-source"

    def test_handles_special_chars(self):
        """Handles special characters in name and source."""
        assert get_plugin_id("plugin-123", "src_abc") == "plugin-123@src_abc"
