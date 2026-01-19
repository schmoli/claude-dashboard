"""Plugins tab UI component with compact table rows and enable/disable support."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from cdash.data.claude_settings import (
    get_plugin_id,
    load_enabled_plugins,
    set_plugin_enabled,
)
from cdash.data.plugins import Plugin, find_installed_plugins
from cdash.theme import GREEN, RED


class PluginRow(Widget, can_focus=True):
    """A single-line row representing a plugin with inline toggle."""

    DEFAULT_CSS = """
    PluginRow {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    PluginRow:focus {
        background: $primary 20%;
    }

    PluginRow.enabled {
        /* default styling */
    }

    PluginRow.disabled {
        opacity: 0.6;
    }

    PluginRow > Horizontal {
        width: 100%;
        height: 1;
    }

    PluginRow .row-status {
        width: 3;
    }

    PluginRow .row-name {
        width: 22;
        text-style: bold;
    }

    PluginRow .row-version {
        width: 12;
        color: $text-muted;
    }

    PluginRow .row-source {
        width: 20;
        color: $text-muted;
    }

    PluginRow .row-counts {
        width: 1fr;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("enter", "toggle", "Toggle"),
        Binding("space", "toggle", "Toggle"),
    ]

    enabled = reactive(True)

    class Toggled(Message):
        """Posted when the plugin row is toggled."""

        def __init__(self, row: "PluginRow", new_state: bool) -> None:
            super().__init__()
            self.row = row
            self.new_state = new_state

    def __init__(self, plugin: Plugin) -> None:
        super().__init__()
        self.plugin = plugin
        self.enabled = plugin.enabled

    def compose(self) -> ComposeResult:
        status = f"[{GREEN}]●[/]" if self.enabled else f"[{RED}]○[/]"
        version = _truncate(f"v{self.plugin.version}", 10)
        source = _truncate(_shorten_source(self.plugin.source), 18)
        counts = _format_counts(self.plugin.skill_count, self.plugin.agent_count)

        with Horizontal():
            yield Static(status, classes="row-status")
            yield Static(self.plugin.name, classes="row-name")
            yield Static(version, classes="row-version")
            yield Static(source, classes="row-source")
            yield Static(counts, classes="row-counts")

    def on_mount(self) -> None:
        """Set initial CSS class based on enabled state."""
        self._update_classes()

    def watch_enabled(self, value: bool) -> None:
        """Update visual state when enabled changes."""
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on enabled state."""
        self.remove_class("enabled", "disabled")
        self.add_class("enabled" if self.enabled else "disabled")

    def on_click(self) -> None:
        """Handle click to toggle plugin state."""
        self.focus()
        self.action_toggle()

    def action_toggle(self) -> None:
        """Toggle the plugin's enabled state."""
        self.enabled = not self.enabled
        self.plugin = Plugin(
            name=self.plugin.name,
            version=self.plugin.version,
            description=self.plugin.description,
            source=self.plugin.source,
            repository=self.plugin.repository,
            skill_count=self.plugin.skill_count,
            agent_count=self.plugin.agent_count,
            path=self.plugin.path,
            enabled=self.enabled,
        )
        # Update status display
        status_widget = self.query_one(".row-status", Static)
        status = f"[{GREEN}]●[/]" if self.enabled else f"[{RED}]○[/]"
        status_widget.update(status)

        self.post_message(self.Toggled(self, self.enabled))


class PluginsTab(VerticalScroll):
    """Plugins tab showing installed plugins as compact table rows."""

    DEFAULT_CSS = """
    PluginsTab {
        height: auto;
        min-height: 10;
        padding: 1;
    }

    PluginsTab > #plugins-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 0;
    }

    PluginsTab > #plugins-hint {
        color: $text-muted;
        margin-bottom: 1;
    }

    PluginsTab > #no-plugins {
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._plugins: list[Plugin] = []

    def compose(self) -> ComposeResult:
        yield Static("INSTALLED PLUGINS", id="plugins-title")
        yield Static(
            "[space/enter] toggle  [arrows] navigate  [r] refresh", id="plugins-hint"
        )

    def on_mount(self) -> None:
        """Load plugins when mounted."""
        self.refresh_plugins()

    def refresh_plugins(self) -> None:
        """Refresh the plugins list."""
        enabled_plugins = load_enabled_plugins()
        self._plugins = find_installed_plugins(enabled_plugins=enabled_plugins)

        # Remove old rows (keep title and hint)
        for row in self.query(PluginRow):
            row.remove()

        # Remove no-plugins message if present
        try:
            no_plugins = self.query_one("#no-plugins")
            no_plugins.remove()
        except Exception:
            pass

        if not self._plugins:
            self.mount(Static("No plugins installed", id="no-plugins"))
            return

        # Mount rows for each plugin
        for plugin in self._plugins:
            row = PluginRow(plugin)
            self.mount(row)

    def on_plugin_row_toggled(self, event: PluginRow.Toggled) -> None:
        """Handle plugin toggle event."""
        plugin = event.row.plugin
        plugin_id = get_plugin_id(plugin.name, plugin.source)

        # Save to settings
        set_plugin_enabled(plugin_id, event.new_state)

        # Show notification
        state_text = "enabled" if event.new_state else "disabled"
        self.notify(f"{plugin.name} {state_text}")

    def action_refresh(self) -> None:
        """Refresh plugin list from disk."""
        self.refresh_plugins()
        self.notify("Plugins refreshed")


def _shorten_source(source: str) -> str:
    """Shorten source name for display."""
    if source.endswith("-marketplace"):
        return source[:-12]
    if source.endswith("-plugins"):
        return source[:-8]
    return source


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _format_counts(skills: int, agents: int) -> str:
    """Format skill/agent counts for display."""
    parts = []
    if skills > 0:
        parts.append(f"{skills}s")
    if agents > 0:
        parts.append(f"{agents}a")
    return ", ".join(parts) if parts else ""
