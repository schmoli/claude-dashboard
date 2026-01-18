"""Stats panel widget for displaying usage statistics."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from cdash.data.sessions import load_all_sessions
from cdash.data.stats import load_stats_cache, sparkline


class TrendWidget(Static):
    """Widget displaying weekly trend sparkline."""

    def __init__(self) -> None:
        super().__init__()
        self._trend_data: list[int] = []

    def update_trend(self, daily_stats: list) -> None:
        """Update the trend display with last 7 days."""
        self._trend_data = [d.message_count for d in daily_stats]
        self.refresh()

    def render(self) -> str:
        """Render the sparkline."""
        if not self._trend_data:
            return "No data"
        return sparkline(self._trend_data)


class ProjectItem(Static):
    """A single project in the ranked list."""

    def __init__(self, name: str, msg_count: int, session_count: int) -> None:
        super().__init__()
        self.project_name = name
        self.msg_count = msg_count
        self.session_count = session_count

    def render(self) -> str:
        """Render the project item."""
        # Truncate project name if too long
        name = self.project_name.split("/")[-1]
        if len(name) > 18:
            name = name[:15] + "..."
        sessions_word = "session" if self.session_count == 1 else "sessions"
        return f"{name:<18} {self.msg_count:>4} msgs │ {self.session_count:>2} {sessions_word}"


class StatsPanel(Vertical):
    """Panel displaying stats, trends, and project rankings."""

    def compose(self) -> ComposeResult:
        """Compose the stats panel."""
        with Horizontal():
            with Vertical():
                yield Static("PROJECTS (by recent activity)", classes="section-title")
                yield from self._build_project_items()
            with Vertical(classes="trend-container"):
                yield Static("WEEKLY TREND", classes="section-title")
                yield TrendWidget()
                yield Static("M T W T F S S", classes="trend-label")

    def _build_project_items(self) -> list[Static]:
        """Build project ranking items."""
        # Aggregate sessions by project
        sessions = load_all_sessions()
        if not sessions:
            return [Static("No projects found", classes="no-data")]

        # Count messages and sessions per project
        project_stats: dict[str, dict] = {}
        for session in sessions:
            name = session.project_name
            if name not in project_stats:
                project_stats[name] = {"msgs": 0, "sessions": 0, "last_modified": 0}
            project_stats[name]["sessions"] += 1
            # Use message count from session file parsing - approximate via prompt existing
            if session.prompt_preview:
                project_stats[name]["msgs"] += 1
            if session.last_modified > project_stats[name]["last_modified"]:
                project_stats[name]["last_modified"] = session.last_modified

        # Sort by last_modified (most recent first)
        sorted_projects = sorted(
            project_stats.items(), key=lambda x: x[1]["last_modified"], reverse=True
        )

        items = []
        for name, stats in sorted_projects[:5]:  # Top 5 projects
            items.append(ProjectItem(name, stats["msgs"], stats["sessions"]))

        return items

    def refresh_stats(self) -> None:
        """Refresh the stats display."""
        # Update trend widget
        trend_widget = self.query_one(TrendWidget)
        stats_cache = load_stats_cache()
        if stats_cache:
            last_7_days = stats_cache.get_last_n_days(7)
            trend_widget.update_trend(last_7_days)

        # Refresh project items
        for widget in self.query("ProjectItem, .no-data"):
            widget.remove()

        # Find the projects container (first Vertical in the Horizontal)
        containers = list(self.query("Horizontal > Vertical"))
        if containers:
            projects_container = containers[0]
            for item in self._build_project_items():
                projects_container.mount(item)
