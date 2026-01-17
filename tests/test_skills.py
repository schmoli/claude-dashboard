"""Tests for skills discovery and display."""

from pathlib import Path

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.skills import SkillsTab
from cdash.data.skills import (
    Skill,
    PluginSkills,
    find_all_skills,
    _parse_frontmatter,
)


class TestParseFrontmatter:
    """Tests for frontmatter parsing."""

    def test_parses_name_and_description(self):
        """Parses name and description from frontmatter."""
        content = '''---
name: test-skill
description: "A test skill"
---
# Content'''
        result = _parse_frontmatter(content)
        assert result == {"name": "test-skill", "description": "A test skill"}

    def test_handles_no_frontmatter(self):
        """Returns None when no frontmatter."""
        content = "# Just a heading\nSome content"
        result = _parse_frontmatter(content)
        assert result is None

    def test_handles_empty_frontmatter(self):
        """Returns None for empty frontmatter."""
        content = "---\n---\n# Content"
        result = _parse_frontmatter(content)
        assert result is None

    def test_handles_unquoted_values(self):
        """Parses unquoted values."""
        content = '''---
name: myskill
---'''
        result = _parse_frontmatter(content)
        assert result == {"name": "myskill"}


class TestFindAllSkills:
    """Tests for skill discovery."""

    def test_empty_cache(self, tmp_path: Path):
        """Empty cache returns no skills."""
        cache = tmp_path / "cache"
        cache.mkdir()
        skills = find_all_skills(cache)
        assert skills == []

    def test_nonexistent_cache(self, tmp_path: Path):
        """Nonexistent cache returns no skills."""
        cache = tmp_path / "nonexistent"
        skills = find_all_skills(cache)
        assert skills == []

    def test_finds_skill(self, tmp_path: Path):
        """Finds a skill with SKILL.md."""
        cache = tmp_path / "cache"
        skill_dir = cache / "source" / "plugin" / "1.0.0" / "skills" / "myskill"
        skill_dir.mkdir(parents=True)

        (skill_dir / "SKILL.md").write_text('''---
name: myskill
description: "Test skill"
---
# My Skill''')

        skills = find_all_skills(cache)
        assert len(skills) == 1
        ps = skills[0]
        assert ps.plugin_name == "plugin"
        assert len(ps.skills) == 1
        assert ps.skills[0].name == "myskill"
        assert ps.skills[0].description == "Test skill"

    def test_groups_by_plugin(self, tmp_path: Path):
        """Skills are grouped by plugin."""
        cache = tmp_path / "cache"

        # Plugin 1 with 2 skills
        for skill in ["skill1", "skill2"]:
            skill_dir = cache / "source" / "plugin1" / "1.0.0" / "skills" / skill
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f'''---
name: {skill}
---''')

        # Plugin 2 with 1 skill
        skill_dir = cache / "source" / "plugin2" / "1.0.0" / "skills" / "skill3"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text('''---
name: skill3
---''')

        skills = find_all_skills(cache)
        assert len(skills) == 2  # 2 plugins

        # Find plugin1
        plugin1 = next(ps for ps in skills if ps.plugin_name == "plugin1")
        assert len(plugin1.skills) == 2

        # Find plugin2
        plugin2 = next(ps for ps in skills if ps.plugin_name == "plugin2")
        assert len(plugin2.skills) == 1

    def test_skills_sorted_by_name(self, tmp_path: Path):
        """Skills within a plugin are sorted by name."""
        cache = tmp_path / "cache"

        for skill in ["zeta", "alpha", "beta"]:
            skill_dir = cache / "source" / "plugin" / "1.0.0" / "skills" / skill
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f'''---
name: {skill}
---''')

        skills = find_all_skills(cache)
        assert len(skills) == 1
        skill_names = [s.name for s in skills[0].skills]
        assert skill_names == ["alpha", "beta", "zeta"]


class TestSkillsTab:
    """Tests for SkillsTab UI component."""

    @pytest.mark.asyncio
    async def test_skills_tab_present(self):
        """Skills tab exists in app."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("4")  # Switch to Skills tab
            skills_tab = app.query_one(SkillsTab)
            assert skills_tab is not None

    @pytest.mark.asyncio
    async def test_skills_tab_has_title(self):
        """Skills tab has title."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("4")
            skills_tab = app.query_one(SkillsTab)
            title = skills_tab.query_one("#skills-title")
            assert "SKILLS" in title.render().plain
