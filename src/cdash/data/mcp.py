"""MCP server discovery and status from ~/.claude/settings.json."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MCPServerType(Enum):
    """Type of MCP server transport."""

    STDIO = "stdio"
    HTTP = "http"


class MCPServerStatus(Enum):
    """Status of an MCP server."""

    UNKNOWN = "unknown"  # Can't determine status
    CONFIGURED = "configured"  # Config exists but status unknown


@dataclass
class MCPServer:
    """Represents an MCP server configuration."""

    name: str
    server_type: MCPServerType
    command: str | None  # For stdio servers
    args: list[str] | None  # For stdio servers
    url: str | None  # For http servers
    status: MCPServerStatus


def get_settings_path() -> Path:
    """Get the path to the Claude settings file."""
    return Path.home() / ".claude" / "settings.json"


def load_mcp_servers(
    settings_path: Path | None = None,
    plugins_dir: Path | None = None,
) -> list[MCPServer]:
    """Load MCP servers from settings.json.

    Also searches for .mcp.json files in plugin directories.

    Args:
        settings_path: Path to settings.json. Defaults to ~/.claude/settings.json.
        plugins_dir: Path to plugins directory. Defaults to ~/.claude/plugins.
                     Pass a nonexistent path to skip plugin scanning.
    """
    servers: list[MCPServer] = []

    # Load from main settings.json
    if settings_path is None:
        settings_path = get_settings_path()

    servers.extend(_load_from_settings_file(settings_path))

    # Also scan plugin directories for .mcp.json files
    if plugins_dir is None:
        plugins_dir = Path.home() / ".claude" / "plugins"

    if plugins_dir.exists():
        for mcp_file in plugins_dir.rglob(".mcp.json"):
            servers.extend(_load_from_settings_file(mcp_file))

    # Sort by name for consistent display
    return sorted(servers, key=lambda s: s.name.lower())


def _load_from_settings_file(path: Path) -> list[MCPServer]:
    """Load MCP servers from a settings/mcp JSON file."""
    if not path.exists():
        return []

    try:
        with path.open() as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    mcp_servers = data.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        return []

    servers: list[MCPServer] = []
    for name, config in mcp_servers.items():
        if not isinstance(config, dict):
            continue

        server_type_str = config.get("type", "stdio")
        try:
            server_type = MCPServerType(server_type_str)
        except ValueError:
            server_type = MCPServerType.STDIO

        server = MCPServer(
            name=name,
            server_type=server_type,
            command=config.get("command"),
            args=config.get("args"),
            url=config.get("url"),
            status=MCPServerStatus.CONFIGURED,
        )
        servers.append(server)

    return servers
