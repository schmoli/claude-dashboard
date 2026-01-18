"""Tests for plugins discovery and display."""

import json
from pathlib import Path

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.plugins import PluginCard, PluginsTab
from cdash.data.plugins import Plugin, find_installed_plugins, _is_semver, _parse_semver


class TestSemver:
    """Tests for semver parsing."""

    def test_is_semver_valid(self):
        """Valid semver strings are detected."""
        assert _is_semver("1.0.0") is True
        assert _is_semver("4.0.3") is True
        assert _is_semver("0.1.0") is True
        assert _is_semver("10.20.30") is True

    def test_is_semver_invalid(self):
        """Invalid semver strings are rejected."""
        assert _is_semver("abc123") is False
        assert _is_semver("96276205880a") is False  # commit hash
        assert _is_semver("latest") is False
        assert _is_semver("1") is False  # needs at least major.minor

    def test_parse_semver(self):
        """Semver strings are parsed to tuples."""
        assert _parse_semver("1.0.0") == (1, 0, 0)
        assert _parse_semver("4.0.3") == (4, 0, 3)
        assert _parse_semver("10.20.30") == (10, 20, 30)

    def test_parse_semver_comparison(self):
        """Parsed semvers compare correctly."""
        assert _parse_semver("2.0.0") > _parse_semver("1.9.9")
        assert _parse_semver("1.1.0") > _parse_semver("1.0.9")
        assert _parse_semver("1.0.1") > _parse_semver("1.0.0")


class TestFindPlugins:
    """Tests for plugin discovery."""

    def test_empty_cache(self, tmp_path: Path):
        """Empty cache returns no plugins."""
        cache = tmp_path / "cache"
        cache.mkdir()
        plugins = find_installed_plugins(cache)
        assert plugins == []

    def test_nonexistent_cache(self, tmp_path: Path):
        """Nonexistent cache returns no plugins."""
        cache = tmp_path / "nonexistent"
        plugins = find_installed_plugins(cache)
        assert plugins == []

    def test_finds_plugin(self, tmp_path: Path):
        """Finds a valid plugin with plugin.json."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "my-source" / "my-plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        # Create plugin.json
        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({
                "name": "my-plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "repository": "https://github.com/test/my-plugin",
            })
        )

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].name == "my-plugin"
        assert plugins[0].version == "1.0.0"
        assert plugins[0].source == "my-source"
        assert plugins[0].description == "Test plugin"

    def test_counts_skills_in_skills_dir(self, tmp_path: Path):
        """Counts skill files in skills/ directory."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "source" / "plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        # Create plugin.json
        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "plugin", "version": "1.0.0"})
        )

        # Create skills in skills/ dir
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill1.md").write_text("# Skill 1")
        (skills_dir / "skill2.md").write_text("# Skill 2")
        (skills_dir / "skill3.md").write_text("# Skill 3")

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].skill_count == 3
        assert plugins[0].agent_count == 0

    def test_counts_skills_in_commands_dir(self, tmp_path: Path):
        """Counts skill files in commands/ directory."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "source" / "plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        # Create plugin.json
        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "plugin", "version": "1.0.0"})
        )

        # Create skills in commands/ dir
        commands_dir = plugin_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "cmd1.md").write_text("# Command 1")
        (commands_dir / "cmd2.md").write_text("# Command 2")

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].skill_count == 2

    def test_counts_agents(self, tmp_path: Path):
        """Counts agent files in plugin."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "source" / "plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        # Create plugin.json
        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "plugin", "version": "1.0.0"})
        )

        # Create agents
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "agent1.md").write_text("# Agent 1")
        (agents_dir / "agent2.md").write_text("# Agent 2")

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].skill_count == 0
        assert plugins[0].agent_count == 2

    def test_picks_highest_version(self, tmp_path: Path):
        """Picks highest semver when multiple versions exist."""
        cache = tmp_path / "cache"
        source = cache / "source" / "plugin"

        # Create multiple versions
        for version in ["1.0.0", "2.0.0", "1.5.0"]:
            plugin_dir = source / version
            plugin_dir.mkdir(parents=True)
            claude_plugin = plugin_dir / ".claude-plugin"
            claude_plugin.mkdir()
            (claude_plugin / "plugin.json").write_text(
                json.dumps({"name": "plugin", "version": version})
            )

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].version == "2.0.0"

    def test_sorted_by_name(self, tmp_path: Path):
        """Plugins are sorted alphabetically by name."""
        cache = tmp_path / "cache"

        for name in ["zeta", "alpha", "beta"]:
            plugin_dir = cache / "source" / name / "1.0.0"
            plugin_dir.mkdir(parents=True)
            claude_plugin = plugin_dir / ".claude-plugin"
            claude_plugin.mkdir()
            (claude_plugin / "plugin.json").write_text(
                json.dumps({"name": name, "version": "1.0.0"})
            )

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 3
        assert [p.name for p in plugins] == ["alpha", "beta", "zeta"]


class TestPluginEnabled:
    """Tests for Plugin enabled state."""

    def test_plugin_enabled_default_true(self, tmp_path: Path):
        """Plugin defaults to enabled when no settings provided."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "source" / "plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "plugin", "version": "1.0.0"})
        )

        plugins = find_installed_plugins(cache)
        assert len(plugins) == 1
        assert plugins[0].enabled is True

    def test_plugin_enabled_from_settings(self, tmp_path: Path):
        """Plugin enabled state from settings dict."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "my-source" / "my-plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "my-plugin", "version": "1.0.0"})
        )

        # Plugin explicitly enabled
        plugins = find_installed_plugins(cache, {"my-plugin@my-source": True})
        assert plugins[0].enabled is True

        # Plugin explicitly disabled
        plugins = find_installed_plugins(cache, {"my-plugin@my-source": False})
        assert plugins[0].enabled is False

    def test_plugin_not_in_settings_defaults_enabled(self, tmp_path: Path):
        """Plugin not in settings dict defaults to enabled."""
        cache = tmp_path / "cache"
        plugin_dir = cache / "source" / "plugin" / "1.0.0"
        plugin_dir.mkdir(parents=True)

        claude_plugin = plugin_dir / ".claude-plugin"
        claude_plugin.mkdir()
        (claude_plugin / "plugin.json").write_text(
            json.dumps({"name": "plugin", "version": "1.0.0"})
        )

        # Empty settings dict - plugin should default to enabled
        plugins = find_installed_plugins(cache, {})
        assert plugins[0].enabled is True

        # Settings with other plugins - this plugin should default to enabled
        plugins = find_installed_plugins(cache, {"other@other": False})
        assert plugins[0].enabled is True


class TestPluginsTab:
    """Tests for PluginsTab UI component."""

    @pytest.mark.asyncio
    async def test_plugins_tab_present(self):
        """Plugins tab exists in app."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")  # Switch to Plugins tab
            plugins_tab = app.query_one(PluginsTab)
            assert plugins_tab is not None

    @pytest.mark.asyncio
    async def test_plugins_tab_has_title(self):
        """Plugins tab has title."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")
            plugins_tab = app.query_one(PluginsTab)
            title = plugins_tab.query_one("#plugins-title")
            assert "INSTALLED PLUGINS" in title.render().plain

    @pytest.mark.asyncio
    async def test_plugins_tab_has_grid(self):
        """Plugins tab has grid container."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")
            plugins_tab = app.query_one(PluginsTab)
            grid = plugins_tab.query_one("#plugins-grid")
            assert grid is not None


class TestPluginCard:
    """Tests for PluginCard widget."""

    def test_card_creation(self, tmp_path: Path):
        """Card can be created from Plugin."""
        plugin = Plugin(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            source="test-source",
            repository=None,
            skill_count=2,
            agent_count=1,
            path=tmp_path,
            enabled=True,
        )
        card = PluginCard(plugin)
        assert card.plugin.name == "test-plugin"
        assert card.enabled is True

    def test_card_enabled_state(self, tmp_path: Path):
        """Card reflects plugin enabled state."""
        # Enabled plugin
        enabled_plugin = Plugin(
            name="enabled",
            version="1.0.0",
            description="",
            source="src",
            repository=None,
            skill_count=0,
            agent_count=0,
            path=tmp_path,
            enabled=True,
        )
        card = PluginCard(enabled_plugin)
        assert card.enabled is True

        # Disabled plugin
        disabled_plugin = Plugin(
            name="disabled",
            version="1.0.0",
            description="",
            source="src",
            repository=None,
            skill_count=0,
            agent_count=0,
            path=tmp_path,
            enabled=False,
        )
        card = PluginCard(disabled_plugin)
        assert card.enabled is False

    def test_card_initial_disabled_state(self, tmp_path: Path):
        """Card starts with disabled state from plugin."""
        plugin = Plugin(
            name="test",
            version="1.0.0",
            description="",
            source="src",
            repository=None,
            skill_count=0,
            agent_count=0,
            path=tmp_path,
            enabled=False,
        )
        card = PluginCard(plugin)
        assert card.enabled is False
        assert card.plugin.enabled is False
