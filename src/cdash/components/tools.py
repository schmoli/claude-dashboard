"""Tool breakdown widget for displaying tool usage statistics."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.tools import ToolUsage, get_tool_usage_for_date, horizontal_bar


class ToolItem(Static):
    """A single tool in the breakdown list."""

    def __init__(self, name: str, count: int, max_count: int) -> None:
        super().__init__()
        self.tool_name = name
        self.count = count
        self.max_count = max_count

    def render(self) -> str:
        """Render the tool item with bar."""
        bar = horizontal_bar(self.count, self.max_count, width=12)
        return f"{self.tool_name:<10} {bar} {self.count:>3}"


class ToolBreakdownPanel(Vertical):
    """Panel displaying tool usage breakdown for today."""

    DEFAULT_CSS = """
    ToolBreakdownPanel {
        height: auto;
        padding: 0 1;
        margin-top: 1;
    }

    ToolBreakdownPanel > .section-title {
        text-style: bold;
        color: $text;
        padding: 0;
        margin-bottom: 1;
    }

    ToolBreakdownPanel > ToolItem {
        height: 1;
        padding: 0;
    }

    ToolBreakdownPanel > .no-data {
        color: $text-muted;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the tool breakdown panel."""
        yield Static("TOOL BREAKDOWN (today)", classes="section-title")
        yield from self._build_tool_items()

    def _build_tool_items(self) -> list[Static]:
        """Build tool item widgets."""
        usage = get_tool_usage_for_date()

        if not usage.tool_counts:
            return [Static("No tool usage today", classes="no-data")]

        top_tools = usage.top_tools(6)
        if not top_tools:
            return [Static("No tool usage today", classes="no-data")]

        max_count = top_tools[0][1] if top_tools else 1

        items = []
        for name, count in top_tools:
            items.append(ToolItem(name, count, max_count))

        return items

    def refresh_tools(self) -> None:
        """Refresh the tool breakdown display."""
        # Remove old items
        for widget in self.query("ToolItem, .no-data"):
            widget.remove()

        # Add new items
        for item in self._build_tool_items():
            self.mount(item)
