"""Plugins tab UI component with enable/disable support."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from cdash.data.claude_settings import (
    get_plugin_id,
    load_enabled_plugins,
    set_plugin_enabled,
)
from cdash.data.plugins import Plugin, find_installed_plugins


class PluginsTab(Vertical):
    """Plugins tab showing installed plugins with enable/disable support."""

    BINDINGS = [
        Binding("space", "toggle_plugin", "Toggle"),
        Binding("enter", "toggle_plugin", "Toggle"),
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    PluginsTab {
        height: auto;
        padding: 1;
    }

    PluginsTab > #plugins-title {
        text-style: bold;
        margin-bottom: 0;
    }

    PluginsTab > #plugins-hint {
        color: $text-muted;
        margin-bottom: 1;
    }

    PluginsTab > #plugins-list {
        height: auto;
        min-height: 5;
        max-height: 20;
        border: solid $primary;
    }

    PluginsTab > #no-plugins {
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._plugins: list[Plugin] = []

    def compose(self) -> ComposeResult:
        yield Static("INSTALLED PLUGINS", id="plugins-title")
        yield Static("[space/enter] toggle  [r] refresh", id="plugins-hint")
        yield OptionList(id="plugins-list")

    def on_mount(self) -> None:
        """Load plugins when mounted."""
        self.refresh_plugins()

    def refresh_plugins(self) -> None:
        """Refresh the plugins list."""
        enabled_plugins = load_enabled_plugins()
        self._plugins = find_installed_plugins(enabled_plugins=enabled_plugins)
        option_list = self.query_one("#plugins-list", OptionList)

        # Clear and rebuild
        option_list.clear_options()

        if not self._plugins:
            option_list.add_option(Option("No plugins installed", disabled=True))
            return

        for plugin in self._plugins:
            option_list.add_option(self._make_option(plugin))

    def _make_option(self, plugin: Plugin) -> Option:
        """Create an option for a plugin."""
        # Status indicator: green filled circle for enabled, red empty for disabled
        status = "[green]●[/]" if plugin.enabled else "[red]○[/]"
        source_short = _shorten_source(plugin.source)

        # Main line with status
        main = f"{status} [bold]{plugin.name}[/]  {plugin.version}  [dim]{source_short}[/]"

        # Details line
        parts = []
        if plugin.skill_count > 0:
            parts.append(f"{plugin.skill_count} skill{'s' if plugin.skill_count != 1 else ''}")
        if plugin.agent_count > 0:
            parts.append(f"{plugin.agent_count} agent{'s' if plugin.agent_count != 1 else ''}")

        if parts:
            details = "  └─ " + ", ".join(parts)
            main += f"\n{details}"

        return Option(main, id=get_plugin_id(plugin.name, plugin.source))

    def action_toggle_plugin(self) -> None:
        """Toggle the selected plugin's enabled state."""
        option_list = self.query_one("#plugins-list", OptionList)

        if option_list.highlighted is None:
            return

        # Find the plugin
        idx = option_list.highlighted
        if idx >= len(self._plugins):
            return

        plugin = self._plugins[idx]
        plugin_id = get_plugin_id(plugin.name, plugin.source)

        # Toggle the state
        new_state = not plugin.enabled
        set_plugin_enabled(plugin_id, new_state)

        # Update local state and display
        # Create new plugin with updated enabled state
        self._plugins[idx] = Plugin(
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            source=plugin.source,
            repository=plugin.repository,
            skill_count=plugin.skill_count,
            agent_count=plugin.agent_count,
            path=plugin.path,
            enabled=new_state,
        )

        # Replace the option in place
        option_list.replace_option_prompt(
            option_list.get_option_at_index(idx).id,
            self._make_option(self._plugins[idx]).prompt,
        )

        # Show notification
        state_text = "enabled" if new_state else "disabled"
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
