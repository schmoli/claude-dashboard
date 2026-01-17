"""Tests for agents discovery and display."""

from pathlib import Path

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.agents import AgentsTab
from cdash.data.agents import (
    Agent,
    AgentSource,
    BUILTIN_AGENTS,
    find_all_agents,
    _parse_frontmatter,
)


class TestParseFrontmatter:
    """Tests for frontmatter parsing."""

    def test_parses_name_and_model(self):
        """Parses name and model from frontmatter."""
        content = '''---
name: test-agent
model: haiku
---
# Content'''
        result = _parse_frontmatter(content)
        assert result == {"name": "test-agent", "model": "haiku"}

    def test_handles_no_frontmatter(self):
        """Returns None when no frontmatter."""
        content = "# Just a heading\nSome content"
        result = _parse_frontmatter(content)
        assert result is None


class TestBuiltinAgents:
    """Tests for built-in agents list."""

    def test_builtin_agents_exist(self):
        """Built-in agents list is not empty."""
        assert len(BUILTIN_AGENTS) > 0

    def test_builtin_agents_have_names(self):
        """All built-in agents have names."""
        for agent in BUILTIN_AGENTS:
            assert agent.name
            assert agent.source == AgentSource.BUILTIN


class TestFindAllAgents:
    """Tests for agent discovery."""

    def test_finds_user_agent(self, tmp_path: Path):
        """Finds user agent from agents directory."""
        user_dir = tmp_path / "agents"
        user_dir.mkdir()

        (user_dir / "my-agent.md").write_text('''---
name: my-agent
model: sonnet
---
# My Agent''')

        plugins_dir = tmp_path / "plugins"  # nonexistent

        result = find_all_agents(user_dir, plugins_dir, include_builtin=False)
        assert len(result["user"]) == 1
        assert result["user"][0].name == "my-agent"
        assert result["user"][0].model == "sonnet"
        assert result["user"][0].source == AgentSource.USER

    def test_finds_plugin_agent(self, tmp_path: Path):
        """Finds plugin agent from plugins cache."""
        user_dir = tmp_path / "agents"  # nonexistent

        plugins_dir = tmp_path / "plugins"
        agent_file = plugins_dir / "source" / "plugin" / "1.0.0" / "agents" / "agent.md"
        agent_file.parent.mkdir(parents=True)
        agent_file.write_text('''---
name: plugin-agent
model: inherit
---''')

        result = find_all_agents(user_dir, plugins_dir, include_builtin=False)
        assert len(result["plugin"]) == 1
        assert result["plugin"][0].name == "plugin-agent"
        assert result["plugin"][0].plugin_name == "plugin"
        assert result["plugin"][0].source == AgentSource.PLUGIN

    def test_includes_builtin_agents(self, tmp_path: Path):
        """Includes built-in agents when requested."""
        user_dir = tmp_path / "agents"
        plugins_dir = tmp_path / "plugins"

        result = find_all_agents(user_dir, plugins_dir, include_builtin=True)
        assert len(result["builtin"]) == len(BUILTIN_AGENTS)

    def test_excludes_builtin_agents(self, tmp_path: Path):
        """Excludes built-in agents when requested."""
        user_dir = tmp_path / "agents"
        plugins_dir = tmp_path / "plugins"

        result = find_all_agents(user_dir, plugins_dir, include_builtin=False)
        assert len(result["builtin"]) == 0

    def test_agents_sorted_by_name(self, tmp_path: Path):
        """Agents within each category are sorted by name."""
        user_dir = tmp_path / "agents"
        user_dir.mkdir()

        for name in ["zeta", "alpha", "beta"]:
            (user_dir / f"{name}.md").write_text(f'''---
name: {name}
---''')

        plugins_dir = tmp_path / "plugins"

        result = find_all_agents(user_dir, plugins_dir, include_builtin=False)
        names = [a.name for a in result["user"]]
        assert names == ["alpha", "beta", "zeta"]


class TestAgentsTab:
    """Tests for AgentsTab UI component."""

    @pytest.mark.asyncio
    async def test_agents_tab_present(self):
        """Agents tab exists in app."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("5")  # Switch to Agents tab
            agents_tab = app.query_one(AgentsTab)
            assert agents_tab is not None

    @pytest.mark.asyncio
    async def test_agents_tab_has_title(self):
        """Agents tab has title."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("5")
            agents_tab = app.query_one(AgentsTab)
            title = agents_tab.query_one("#agents-title")
            assert "AGENTS" in title.render().plain
