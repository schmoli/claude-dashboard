"""Skill discovery and parsing from plugin directories."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    """Represents a Claude Code skill."""

    name: str
    description: str
    plugin_name: str
    plugin_source: str
    path: Path


@dataclass
class PluginSkills:
    """Skills grouped by plugin."""

    plugin_name: str
    plugin_source: str
    skills: list[Skill]


def get_plugins_cache_path() -> Path:
    """Get the path to the plugins cache directory."""
    return Path.home() / ".claude" / "plugins" / "cache"


def find_all_skills(cache_path: Path | None = None) -> list[PluginSkills]:
    """Find all skills organized by plugin.

    Scans ~/.claude/plugins/cache/<source>/<plugin>/<version>/skills/<skill>/SKILL.md
    """
    if cache_path is None:
        cache_path = get_plugins_cache_path()

    if not cache_path.exists():
        return []

    plugin_skills_map: dict[tuple[str, str], list[Skill]] = {}

    # Iterate through sources (e.g., superpowers-marketplace)
    for source_dir in cache_path.iterdir():
        if not source_dir.is_dir():
            continue

        # Iterate through plugins
        for plugin_dir in source_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Find the best version (using same logic as plugins.py)
            version_dir = _find_best_version(plugin_dir)
            if version_dir is None:
                continue

            # Find skills in this plugin
            skills_dir = version_dir / "skills"
            if not skills_dir.exists():
                continue

            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue

                skill = _parse_skill_file(skill_file, plugin_dir.name, source_dir.name)
                if skill:
                    key = (plugin_dir.name, source_dir.name)
                    if key not in plugin_skills_map:
                        plugin_skills_map[key] = []
                    plugin_skills_map[key].append(skill)

    # Convert to list of PluginSkills, sorted by plugin name
    result = []
    for (plugin_name, source), skills in sorted(plugin_skills_map.items()):
        # Sort skills by name within each plugin
        skills.sort(key=lambda s: s.name.lower())
        result.append(PluginSkills(
            plugin_name=plugin_name,
            plugin_source=source,
            skills=skills,
        ))

    return result


def _find_best_version(plugin_dir: Path) -> Path | None:
    """Find the best version directory for a plugin."""
    version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir()]
    if not version_dirs:
        return None

    # Separate semver versions from hash versions
    semver_dirs = []
    hash_dirs = []

    for vdir in version_dirs:
        if _is_semver(vdir.name):
            semver_dirs.append(vdir)
        else:
            hash_dirs.append(vdir)

    # Prefer semver versions
    if semver_dirs:
        return max(semver_dirs, key=lambda d: _parse_semver(d.name))

    # Fall back to most recently modified hash dir
    if hash_dirs:
        return max(hash_dirs, key=lambda d: d.stat().st_mtime)

    return None


def _is_semver(version: str) -> bool:
    """Check if a version string looks like semantic versioning."""
    parts = version.split(".")
    if len(parts) < 2:
        return False
    return all(part.isdigit() for part in parts[:2])


def _parse_semver(version: str) -> tuple[int, ...]:
    """Parse a semver string into a tuple for comparison."""
    parts = version.split(".")
    result = []
    for part in parts:
        if "-" in part:
            part = part.split("-")[0]
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return tuple(result)


def _parse_skill_file(skill_file: Path, plugin_name: str, source: str) -> Skill | None:
    """Parse a SKILL.md file for skill metadata."""
    try:
        content = skill_file.read_text()
    except OSError:
        return None

    # Parse YAML frontmatter (between --- markers)
    frontmatter = _parse_frontmatter(content)
    if not frontmatter:
        # Use directory name as fallback
        return Skill(
            name=skill_file.parent.name,
            description="",
            plugin_name=plugin_name,
            plugin_source=source,
            path=skill_file,
        )

    return Skill(
        name=frontmatter.get("name", skill_file.parent.name),
        description=frontmatter.get("description", ""),
        plugin_name=plugin_name,
        plugin_source=source,
        path=skill_file,
    )


def _parse_frontmatter(content: str) -> dict[str, str] | None:
    """Parse YAML frontmatter from markdown content."""
    # Match content between --- markers at start of file
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter_text = match.group(1)
    result = {}

    # Simple YAML parsing for key: value pairs
    for line in frontmatter_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value

    return result if result else None
