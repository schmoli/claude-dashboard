"""MCP Servers tab UI component."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.mcp import MCPServer, MCPServerType, load_mcp_servers


class MCPServerRow(Static):
    """Single MCP server row display."""

    DEFAULT_CSS = """
    MCPServerRow {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, server: MCPServer) -> None:
        super().__init__()
        self._server = server

    def compose(self) -> ComposeResult:
        s = self._server

        # Status indicator
        status_icon = "○"  # configured/unknown

        # Type indicator
        type_str = s.server_type.value

        # Command/URL
        if s.server_type == MCPServerType.HTTP:
            target = s.url or ""
        else:
            # For stdio, show command and args
            parts = []
            if s.command:
                parts.append(s.command)
            if s.args:
                parts.extend(s.args)
            target = " ".join(parts) if parts else ""

        # Truncate target if too long
        if len(target) > 40:
            target = target[:37] + "..."

        line = f"{status_icon} [bold]{s.name}[/bold]  {type_str}  [dim]{target}[/dim]"
        yield Static(line, markup=True)


class MCPServersTab(Vertical):
    """MCP Servers tab showing configured MCP servers."""

    DEFAULT_CSS = """
    MCPServersTab {
        height: auto;
        padding: 1;
    }

    MCPServersTab > #mcp-title {
        text-style: bold;
        margin-bottom: 1;
    }

    MCPServersTab > #mcp-list {
        height: auto;
    }

    MCPServersTab > #no-servers {
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("MCP SERVERS", id="mcp-title")
        yield Vertical(id="mcp-list")

    def on_mount(self) -> None:
        """Load MCP servers when mounted."""
        self.refresh_servers()

    def refresh_servers(self) -> None:
        """Refresh the MCP servers list."""
        servers = load_mcp_servers()
        servers_list = self.query_one("#mcp-list", Vertical)

        # Clear existing content
        servers_list.remove_children()

        if not servers:
            servers_list.mount(Static("No MCP servers configured", id="no-servers"))
            return

        for server in servers:
            servers_list.mount(MCPServerRow(server))
