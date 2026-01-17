"""Skills tab UI component."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.skills import PluginSkills, Skill, find_all_skills


class SkillRow(Static):
    """Single skill row display."""

    DEFAULT_CSS = """
    SkillRow {
        height: auto;
        padding: 0 1;
    }
    """

    def __init__(self, skill: Skill) -> None:
        super().__init__()
        self._skill = skill

    def compose(self) -> ComposeResult:
        s = self._skill
        # Truncate description if too long
        desc = s.description
        if len(desc) > 50:
            desc = desc[:47] + "..."
        line = f"  [bold]{s.name}[/bold]  [dim]{desc}[/dim]"
        yield Static(line, markup=True)


class PluginSkillsGroup(Vertical):
    """Group of skills for a plugin."""

    DEFAULT_CSS = """
    PluginSkillsGroup {
        height: auto;
        margin-bottom: 1;
    }

    PluginSkillsGroup > .plugin-header {
        text-style: bold;
        color: $text;
    }
    """

    def __init__(self, plugin_skills: PluginSkills) -> None:
        super().__init__()
        self._plugin_skills = plugin_skills

    def compose(self) -> ComposeResult:
        ps = self._plugin_skills
        count = len(ps.skills)
        header = f"▼ {ps.plugin_name} ({count})"
        yield Static(header, classes="plugin-header")

        for skill in ps.skills:
            yield SkillRow(skill)


class SkillsTab(Vertical):
    """Skills tab showing available skills grouped by plugin."""

    DEFAULT_CSS = """
    SkillsTab {
        height: 100%;
        padding: 1;
    }

    SkillsTab > #skills-title {
        text-style: bold;
        margin-bottom: 1;
    }

    SkillsTab > #skills-list {
        height: auto;
    }

    SkillsTab > #no-skills {
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("SKILLS", id="skills-title")
        yield Vertical(id="skills-list")

    def on_mount(self) -> None:
        """Load skills when mounted."""
        self.refresh_skills()

    def refresh_skills(self) -> None:
        """Refresh the skills list."""
        plugin_skills = find_all_skills()
        skills_list = self.query_one("#skills-list", Vertical)

        # Clear existing content
        skills_list.remove_children()

        if not plugin_skills:
            skills_list.mount(Static("No skills found", id="no-skills"))
            return

        for ps in plugin_skills:
            skills_list.mount(PluginSkillsGroup(ps))
