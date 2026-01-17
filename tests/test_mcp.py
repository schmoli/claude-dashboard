"""Tests for MCP server discovery and display."""

import json
from pathlib import Path

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.mcp import MCPServersTab
from cdash.data.mcp import (
    MCPServer,
    MCPServerStatus,
    MCPServerType,
    load_mcp_servers,
)


class TestMCPServerType:
    """Tests for MCP server type enum."""

    def test_stdio_type(self):
        """stdio type is valid."""
        assert MCPServerType.STDIO.value == "stdio"

    def test_http_type(self):
        """http type is valid."""
        assert MCPServerType.HTTP.value == "http"


class TestLoadMCPServers:
    """Tests for MCP server loading."""

    def test_nonexistent_file(self, tmp_path: Path):
        """Nonexistent file returns empty list."""
        settings = tmp_path / "settings.json"
        plugins = tmp_path / "plugins"  # nonexistent
        servers = load_mcp_servers(settings, plugins)
        assert servers == []

    def test_empty_file(self, tmp_path: Path):
        """Empty JSON returns empty list."""
        settings = tmp_path / "settings.json"
        settings.write_text("{}")
        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert servers == []

    def test_no_mcp_servers_key(self, tmp_path: Path):
        """Missing mcpServers key returns empty list."""
        settings = tmp_path / "settings.json"
        settings.write_text('{"model": "opus"}')
        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert servers == []

    def test_parses_stdio_server(self, tmp_path: Path):
        """Parses stdio MCP server."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "filesystem": {
                    "type": "stdio",
                    "command": "/usr/local/bin/mcp-fs",
                    "args": ["--read-only"]
                }
            }
        }))

        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert len(servers) == 1
        s = servers[0]
        assert s.name == "filesystem"
        assert s.server_type == MCPServerType.STDIO
        assert s.command == "/usr/local/bin/mcp-fs"
        assert s.args == ["--read-only"]
        assert s.status == MCPServerStatus.CONFIGURED

    def test_parses_http_server(self, tmp_path: Path):
        """Parses HTTP MCP server."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "stripe": {
                    "type": "http",
                    "url": "https://mcp.stripe.com"
                }
            }
        }))

        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert len(servers) == 1
        s = servers[0]
        assert s.name == "stripe"
        assert s.server_type == MCPServerType.HTTP
        assert s.url == "https://mcp.stripe.com"

    def test_multiple_servers(self, tmp_path: Path):
        """Parses multiple servers."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "server1": {"type": "stdio", "command": "cmd1"},
                "server2": {"type": "http", "url": "https://example.com"},
            }
        }))

        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert len(servers) == 2

    def test_sorted_by_name(self, tmp_path: Path):
        """Servers are sorted by name."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "zeta": {"type": "stdio", "command": "z"},
                "alpha": {"type": "stdio", "command": "a"},
                "beta": {"type": "stdio", "command": "b"},
            }
        }))

        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert [s.name for s in servers] == ["alpha", "beta", "zeta"]

    def test_handles_invalid_json(self, tmp_path: Path):
        """Invalid JSON returns empty list."""
        settings = tmp_path / "settings.json"
        settings.write_text("not json")
        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert servers == []

    def test_defaults_to_stdio(self, tmp_path: Path):
        """Missing type defaults to stdio."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {
                "server": {"command": "cmd"}
            }
        }))

        plugins = tmp_path / "plugins"
        servers = load_mcp_servers(settings, plugins)
        assert len(servers) == 1
        assert servers[0].server_type == MCPServerType.STDIO


class TestMCPServersTab:
    """Tests for MCPServersTab UI component."""

    @pytest.mark.asyncio
    async def test_mcp_tab_present(self):
        """MCP Servers tab exists in app."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")  # Switch to MCP Servers tab
            mcp_tab = app.query_one(MCPServersTab)
            assert mcp_tab is not None

    @pytest.mark.asyncio
    async def test_mcp_tab_has_title(self):
        """MCP Servers tab has title."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")
            mcp_tab = app.query_one(MCPServersTab)
            title = mcp_tab.query_one("#mcp-title")
            assert "MCP SERVERS" in title.render().plain
