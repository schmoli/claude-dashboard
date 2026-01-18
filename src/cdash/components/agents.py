"""Agents tab UI component."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.agents import Agent, find_all_agents


class AgentRow(Static):
    """Single agent row display."""

    def __init__(self, agent: Agent) -> None:
        super().__init__()
        self._agent = agent

    def render(self) -> str:
        a = self._agent
        # Format: plugin:name or just name for user/builtin
        if a.plugin_name:
            name = f"{a.plugin_name}:{a.name}"
        else:
            name = a.name

        # Truncate name if too long
        if len(name) > 30:
            name = name[:27] + "..."

        return f"  {name:<32} {a.model}"


class AgentGroup(Vertical):
    """Group of agents by source type."""

    def __init__(self, title: str, agents: list[Agent]) -> None:
        super().__init__()
        self._title = title
        self._agents = agents

    def compose(self) -> ComposeResult:
        yield Static(self._title, classes="group-header")
        for agent in self._agents:
            yield AgentRow(agent)


class AgentsTab(Vertical):
    """Agents tab showing available agents grouped by source."""

    def compose(self) -> ComposeResult:
        yield Static("AGENTS", id="agents-title")
        yield Vertical(id="agents-list")

    def on_mount(self) -> None:
        """Load agents when mounted."""
        self.refresh_agents()

    def refresh_agents(self) -> None:
        """Refresh the agents list."""
        agents_by_source = find_all_agents()
        agents_list = self.query_one("#agents-list", Vertical)

        # Clear existing content
        agents_list.remove_children()

        has_agents = False

        # User agents
        if agents_by_source.get("user"):
            has_agents = True
            agents_list.mount(
                AgentGroup("User Agents (~/.claude/agents/)", agents_by_source["user"])
            )

        # Plugin agents
        if agents_by_source.get("plugin"):
            has_agents = True
            agents_list.mount(AgentGroup("Plugin Agents", agents_by_source["plugin"]))

        # Built-in agents
        if agents_by_source.get("builtin"):
            has_agents = True
            agents_list.mount(AgentGroup("Built-in Agents", agents_by_source["builtin"]))

        if not has_agents:
            agents_list.mount(Static("No agents found", id="no-agents"))
