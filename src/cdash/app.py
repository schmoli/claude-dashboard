"""Main Textual application for Claude Dashboard."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Static


class StatusBar(Static):
    """Top status bar showing app name and summary stats."""

    def compose(self) -> ComposeResult:
        yield Static("claude-dash", id="app-name")


class ClaudeDashApp(App):
    """Claude Code monitoring dashboard."""

    TITLE = "claude-dash"
    CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }

    #app-name {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield Footer()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)
