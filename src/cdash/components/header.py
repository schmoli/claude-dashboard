"""k9s-style header panel for the dashboard."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.resources import get_resource_stats
from cdash.theme import AMBER, BLUE, CORAL, GREEN, TEXT_MUTED

# ASCII art logo for claude-dash (fits in ~7 lines)
LOGO = """\
       __         __
  ____/ /__ ____ / /
 / __/ / _ `(_-</ _ \\
 \\__/_/\\_,_/___/_//_/
      ⬡ dashboard"""


class HeaderPanel(Vertical):
    """k9s-style header with multi-row stats display.

    Layout:
    ┌───────────────────────────────────────────────────────────────────┐
    │ Sessions: 3 active     │ <q>  Quit        │        __         __  │
    │ Today:    42m / 128t   │ <r>  Reload      │   ____/ /__ ____ / /  │
    │ CPU:      15%          │                  │  / __/ / _ `(_-</ _ \\ │
    │ MEM:      1.2G         │                  │  \\__/_/\\_,_/___/_//_/ │
    │ Procs:    8            │                  │       ⬡ dashboard     │
    │ ●                      │                  │                       │
    └───────────────────────────────────────────────────────────────────┘
    """

    DEFAULT_CSS = """
    HeaderPanel {
        dock: top;
        height: 7;
        background: $surface;
        padding: 0 1;
    }

    HeaderPanel .header-row {
        height: 1;
        width: 100%;
    }

    HeaderPanel .stats-col {
        width: 1fr;
    }

    HeaderPanel .shortcuts-col {
        width: auto;
        min-width: 20;
        padding: 0 2;
    }

    HeaderPanel .logo-col {
        width: auto;
        min-width: 26;
        color: $warning;
    }

    HeaderPanel .stat-label {
        width: 10;
        color: $secondary;
    }

    HeaderPanel .stat-value {
        width: auto;
    }

    HeaderPanel .shortcut-key {
        width: auto;
        color: $warning;
    }

    HeaderPanel .shortcut-desc {
        width: auto;
        color: $text-muted;
    }

    HeaderPanel .logo-line {
        width: auto;
        text-style: bold;
    }

    HeaderPanel .indicator-row {
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        # Row 1: Sessions / <q> Quit / Logo line 1
        with Horizontal(classes="header-row"):
            yield Static("Sessions:", classes="stat-label")
            yield Static("0 active", id="stat-sessions", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static("<q>", classes="shortcut-key")
            yield Static("  Quit", classes="shortcut-desc shortcuts-col")
            yield Static(LOGO.splitlines()[0] if LOGO.splitlines() else "", classes="logo-line logo-col")

        # Row 2: Today / <r> Reload / Logo line 2
        with Horizontal(classes="header-row"):
            yield Static("Today:", classes="stat-label")
            yield Static("0m / 0t", id="stat-today", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static("<r>", classes="shortcut-key")
            yield Static("  Reload", classes="shortcut-desc shortcuts-col")
            yield Static(LOGO.splitlines()[1] if len(LOGO.splitlines()) > 1 else "", classes="logo-line logo-col")

        # Row 3: CPU / Logo line 3
        with Horizontal(classes="header-row"):
            yield Static("CPU:", classes="stat-label")
            yield Static("0%", id="stat-cpu", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static("", classes="shortcut-key")
            yield Static("", classes="shortcut-desc shortcuts-col")
            yield Static(LOGO.splitlines()[2] if len(LOGO.splitlines()) > 2 else "", classes="logo-line logo-col")

        # Row 4: MEM / Logo line 4
        with Horizontal(classes="header-row"):
            yield Static("MEM:", classes="stat-label")
            yield Static("0M", id="stat-mem", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static("", classes="shortcut-key")
            yield Static("", classes="shortcut-desc shortcuts-col")
            yield Static(LOGO.splitlines()[3] if len(LOGO.splitlines()) > 3 else "", classes="logo-line logo-col")

        # Row 5: Procs / Logo line 5
        with Horizontal(classes="header-row"):
            yield Static("Procs:", classes="stat-label")
            yield Static("0", id="stat-procs", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static("", classes="shortcut-key")
            yield Static("", classes="shortcut-desc shortcuts-col")
            yield Static(LOGO.splitlines()[4] if len(LOGO.splitlines()) > 4 else "", classes="logo-line logo-col")

        # Row 6: Refresh indicator + code changed
        with Horizontal(classes="header-row indicator-row"):
            yield RefreshIndicator(id="header-refresh")
            yield Static("", id="code-changed", classes="stat-value")
            yield Static("", classes="stats-col")

    def update_stats(
        self,
        active_count: int,
        msgs_today: int = 0,
        tools_today: int = 0,
    ) -> None:
        """Update session and activity stats."""
        try:
            sessions_widget = self.query_one("#stat-sessions", Static)
            today_widget = self.query_one("#stat-today", Static)

            if active_count > 0:
                sessions_widget.update(f"[{GREEN}]{active_count} active[/]")
            else:
                sessions_widget.update(f"[{TEXT_MUTED}]0 active[/]")

            today_widget.update(f"[{CORAL}]{msgs_today}[/]m / [{CORAL}]{tools_today}[/]t")
        except Exception:
            pass

    def update_host_stats(self) -> None:
        """Refresh host resource stats from psutil."""
        stats = get_resource_stats()

        try:
            cpu_widget = self.query_one("#stat-cpu", Static)
            mem_widget = self.query_one("#stat-mem", Static)
            procs_widget = self.query_one("#stat-procs", Static)

            cpu_display = min(stats.cpu_percent, 999)
            if stats.memory_mb >= 1024:
                mem_display = f"{stats.memory_mb / 1024:.1f}G"
            else:
                mem_display = f"{stats.memory_mb:.0f}M"

            cpu_widget.update(f"[{CORAL}]{cpu_display:.0f}%[/]")
            mem_widget.update(f"[{CORAL}]{mem_display}[/]")
            procs_widget.update(f"[{BLUE}]{stats.process_count}[/]")
        except Exception:
            pass

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed."""
        try:
            indicator = self.query_one("#header-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass

    def show_code_changed(self, changed: bool, file_count: int = 0) -> None:
        """Show/hide the code changed indicator."""
        try:
            widget = self.query_one("#code-changed", Static)
            if changed:
                widget.update(f"[{AMBER}]⟳{file_count}f(r)[/]")
            else:
                widget.update("")
        except Exception:
            pass
