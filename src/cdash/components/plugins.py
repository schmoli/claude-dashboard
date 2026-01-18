"""Plugins tab UI component with card-based grid and enable/disable support."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
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
from cdash.theme import GREEN, RED, CORAL, PANEL, SURFACE


class PluginCard(Widget, can_focus=True):
    """A focusable card widget representing a single plugin."""

    DEFAULT_CSS = """
    PluginCard {
        width: 1fr;
        height: auto;
        min-height: 5;
        padding: 1;
        border: round #333333;
        background: $panel;
    }

    PluginCard:focus {
        border: round $primary;
    }

    PluginCard.enabled {
        border: round $success;
        background: $panel;
    }

    PluginCard.enabled:focus {
        border: double $success;
    }

    PluginCard.disabled {
        border: round $error;
        background: $surface;
        opacity: 0.7;
    }

    PluginCard.disabled:focus {
        border: double $error;
    }

    PluginCard > .card-header {
        text-style: bold;
        margin-bottom: 0;
    }

    PluginCard > .card-version {
        color: $text-muted;
    }

    PluginCard > .card-source {
        color: $text-muted;
    }

    PluginCard > .card-details {
        color: $text-muted;
        margin-top: 1;
    }

    PluginCard > .card-status {
        text-align: right;
    }
    """

    BINDINGS = [
        Binding("enter", "toggle", "Toggle"),
        Binding("space", "toggle", "Toggle"),
    ]

    enabled = reactive(True)

    class Toggled(Message):
        """Posted when the plugin card is toggled."""

        def __init__(self, card: "PluginCard", new_state: bool) -> None:
            super().__init__()
            self.card = card
            self.new_state = new_state

    def __init__(self, plugin: Plugin) -> None:
        super().__init__()
        self.plugin = plugin
        self.enabled = plugin.enabled

    def compose(self) -> ComposeResult:
        # Status indicator
        status = f"[{GREEN}]● ENABLED[/]" if self.enabled else f"[{RED}]○ DISABLED[/]"
        yield Static(status, classes="card-status")

        # Plugin name
        yield Static(f"[bold]{self.plugin.name}[/]", classes="card-header")

        # Version and source
        source_short = _shorten_source(self.plugin.source)
        yield Static(f"v{self.plugin.version}", classes="card-version")
        yield Static(source_short, classes="card-source")

        # Skill/agent counts
        parts = []
        if self.plugin.skill_count > 0:
            parts.append(f"{self.plugin.skill_count} skill{'s' if self.plugin.skill_count != 1 else ''}")
        if self.plugin.agent_count > 0:
            parts.append(f"{self.plugin.agent_count} agent{'s' if self.plugin.agent_count != 1 else ''}")

        if parts:
            yield Static(", ".join(parts), classes="card-details")

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
        status_widget = self.query_one(".card-status", Static)
        status = f"[{GREEN}]● ENABLED[/]" if self.enabled else f"[{RED}]○ DISABLED[/]"
        status_widget.update(status)

        self.post_message(self.Toggled(self, self.enabled))


class PluginsTab(VerticalScroll):
    """Plugins tab showing installed plugins as a card grid with enable/disable support."""

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

    PluginsTab > #plugins-grid {
        grid-size: 3;
        grid-gutter: 1;
        height: auto;
        min-height: 10;
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

    def __init__(self) -> None:
        super().__init__()
        self._plugins: list[Plugin] = []

    def compose(self) -> ComposeResult:
        yield Static("INSTALLED PLUGINS", id="plugins-title")
        yield Static("[click/space/enter] toggle  [arrows] navigate  [r] refresh", id="plugins-hint")
        yield Grid(id="plugins-grid")

    def on_mount(self) -> None:
        """Load plugins when mounted."""
        self.refresh_plugins()

    def refresh_plugins(self) -> None:
        """Refresh the plugins list."""
        enabled_plugins = load_enabled_plugins()
        self._plugins = find_installed_plugins(enabled_plugins=enabled_plugins)
        grid = self.query_one("#plugins-grid", Grid)

        # Clear and rebuild
        grid.remove_children()

        if not self._plugins:
            # Show no plugins message
            no_plugins = Static("No plugins installed", id="no-plugins")
            grid.mount(no_plugins)
            return

        # Create cards for each plugin
        for plugin in self._plugins:
            card = PluginCard(plugin)
            grid.mount(card)

    def on_plugin_card_toggled(self, event: PluginCard.Toggled) -> None:
        """Handle plugin toggle event."""
        plugin = event.card.plugin
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
