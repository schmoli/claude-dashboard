"""Agent discovery from user and plugin directories."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AgentSource(Enum):
    """Source of an agent definition."""

    USER = "user"
    PLUGIN = "plugin"
    BUILTIN = "builtin"


@dataclass
class Agent:
    """Represents a Claude Code agent."""

    name: str
    description: str
    model: str  # e.g., "haiku", "sonnet", "inherit"
    source: AgentSource
    plugin_name: str | None  # For plugin agents
    path: Path | None


# Built-in agents that are part of Claude Code
BUILTIN_AGENTS = [
    Agent("Bash", "Command execution specialist", "inherit", AgentSource.BUILTIN, None, None),
    Agent(
        "general-purpose",
        "General-purpose agent for complex tasks",
        "inherit",
        AgentSource.BUILTIN,
        None,
        None,
    ),
    Agent("Explore", "Fast codebase exploration agent", "haiku", AgentSource.BUILTIN, None, None),
    Agent("Plan", "Software architect agent for plans", "inherit", AgentSource.BUILTIN, None, None),
    Agent(
        "claude-code-guide",
        "Claude Code documentation guide",
        "haiku",
        AgentSource.BUILTIN,
        None,
        None,
    ),
]


def get_user_agents_dir() -> Path:
    """Get the path to user agents directory."""
    return Path.home() / ".claude" / "agents"


def get_plugins_cache_path() -> Path:
    """Get the path to the plugins cache directory."""
    return Path.home() / ".claude" / "plugins" / "cache"


def find_all_agents(
    user_dir: Path | None = None,
    plugins_dir: Path | None = None,
    include_builtin: bool = True,
) -> dict[str, list[Agent]]:
    """Find all agents organized by source type.

    Returns:
        Dict with keys "user", "plugin", "builtin" mapping to lists of agents.
    """
    result: dict[str, list[Agent]] = {
        "user": [],
        "plugin": [],
        "builtin": [],
    }

    # User agents
    if user_dir is None:
        user_dir = get_user_agents_dir()

    if user_dir.exists():
        for agent_file in user_dir.glob("*.md"):
            agent = _parse_agent_file(agent_file, AgentSource.USER)
            if agent:
                result["user"].append(agent)

    # Plugin agents
    if plugins_dir is None:
        plugins_dir = get_plugins_cache_path()

    if plugins_dir.exists():
        seen_plugins: set[tuple[str, str]] = set()  # (plugin_name, agent_name)

        for source_dir in plugins_dir.iterdir():
            if not source_dir.is_dir():
                continue

            for plugin_dir in source_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                version_dir = _find_best_version(plugin_dir)
                if version_dir is None:
                    continue

                agents_dir = version_dir / "agents"
                if not agents_dir.exists():
                    continue

                for agent_file in agents_dir.glob("*.md"):
                    key = (plugin_dir.name, agent_file.stem)
                    if key in seen_plugins:
                        continue  # Skip duplicates across versions
                    seen_plugins.add(key)

                    agent = _parse_agent_file(agent_file, AgentSource.PLUGIN, plugin_dir.name)
                    if agent:
                        result["plugin"].append(agent)

    # Built-in agents
    if include_builtin:
        result["builtin"] = list(BUILTIN_AGENTS)

    # Sort each list by name
    for key in result:
        result[key].sort(key=lambda a: a.name.lower())

    return result


def _find_best_version(plugin_dir: Path) -> Path | None:
    """Find the best version directory for a plugin."""
    version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir()]
    if not version_dirs:
        return None

    semver_dirs = []
    hash_dirs = []

    for vdir in version_dirs:
        if _is_semver(vdir.name):
            semver_dirs.append(vdir)
        else:
            hash_dirs.append(vdir)

    if semver_dirs:
        return max(semver_dirs, key=lambda d: _parse_semver(d.name))

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


def _parse_agent_file(
    agent_file: Path, source: AgentSource, plugin_name: str | None = None
) -> Agent | None:
    """Parse an agent markdown file."""
    try:
        content = agent_file.read_text()
    except OSError:
        return None

    frontmatter = _parse_frontmatter(content)

    name = agent_file.stem
    description = ""
    model = "inherit"

    if frontmatter:
        name = frontmatter.get("name", name)
        description = frontmatter.get("description", "")
        model = frontmatter.get("model", "inherit")

    # Truncate long descriptions
    if len(description) > 100:
        description = description[:97] + "..."

    return Agent(
        name=name,
        description=description,
        model=model,
        source=source,
        plugin_name=plugin_name,
        path=agent_file,
    )


def _parse_frontmatter(content: str) -> dict[str, str] | None:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter_text = match.group(1)
    result = {}

    for line in frontmatter_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # Handle multiline with |
            if value == "|":
                continue  # Skip multiline indicators
            result[key] = value

    return result if result else None
