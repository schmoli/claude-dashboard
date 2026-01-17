"""Plugins tab UI component."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.plugins import Plugin, find_installed_plugins


class PluginRow(Static):
    """Single plugin row display."""

    DEFAULT_CSS = """
    PluginRow {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, plugin: Plugin) -> None:
        super().__init__()
        self._plugin = plugin

    def compose(self) -> ComposeResult:
        # Format: name  version  source
        #         └─ N skills, M agents
        p = self._plugin
        source_short = _shorten_source(p.source)

        main_line = f"[bold]{p.name}[/bold]  {p.version}  [dim]{source_short}[/dim]"
        yield Static(main_line, markup=True)

        # Details line with counts
        parts = []
        if p.skill_count > 0:
            parts.append(f"{p.skill_count} skill{'s' if p.skill_count != 1 else ''}")
        if p.agent_count > 0:
            parts.append(f"{p.agent_count} agent{'s' if p.agent_count != 1 else ''}")

        if parts:
            details = "  └─ " + ", ".join(parts)
            yield Static(details, classes="plugin-details")


def _shorten_source(source: str) -> str:
    """Shorten source name for display."""
    # Remove common suffixes
    if source.endswith("-marketplace"):
        return source[:-12]
    if source.endswith("-plugins"):
        return source[:-8]
    return source


class PluginsTab(Vertical):
    """Plugins tab showing installed plugins."""

    DEFAULT_CSS = """
    PluginsTab {
        height: auto;
        padding: 1;
    }

    PluginsTab > #plugins-title {
        text-style: bold;
        margin-bottom: 1;
    }

    PluginsTab > #plugins-list {
        height: auto;
    }

    PluginsTab > #no-plugins {
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }

    .plugin-details {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("INSTALLED PLUGINS", id="plugins-title")
        yield Vertical(id="plugins-list")

    def on_mount(self) -> None:
        """Load plugins when mounted."""
        self.refresh_plugins()

    def refresh_plugins(self) -> None:
        """Refresh the plugins list."""
        plugins = find_installed_plugins()
        plugins_list = self.query_one("#plugins-list", Vertical)

        # Clear existing content
        plugins_list.remove_children()

        if not plugins:
            plugins_list.mount(Static("No plugins installed", id="no-plugins"))
            return

        for plugin in plugins:
            plugins_list.mount(PluginRow(plugin))
