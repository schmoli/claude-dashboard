"""Plugin discovery and parsing from ~/.claude/plugins/cache/."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Plugin:
    """Represents an installed Claude Code plugin."""

    name: str
    version: str
    description: str
    source: str  # e.g., "superpowers-marketplace", "claude-code-plugins"
    repository: str | None
    skill_count: int
    agent_count: int
    path: Path


def get_plugins_cache_path() -> Path:
    """Get the path to the plugins cache directory."""
    return Path.home() / ".claude" / "plugins" / "cache"


def find_installed_plugins(cache_path: Path | None = None) -> list[Plugin]:
    """Find all installed plugins in the cache directory.

    Scans ~/.claude/plugins/cache/<source>/<name>/<version>/ for plugins.
    For plugins with multiple versions, uses the one with highest semver.
    """
    if cache_path is None:
        cache_path = get_plugins_cache_path()

    if not cache_path.exists():
        return []

    plugins: list[Plugin] = []

    # Iterate through sources (e.g., superpowers-marketplace, claude-code-plugins)
    for source_dir in cache_path.iterdir():
        if not source_dir.is_dir():
            continue

        # Iterate through plugin names
        for plugin_dir in source_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Find the best version (highest semver or most recent)
            version_dir = _find_best_version(plugin_dir)
            if version_dir is None:
                continue

            plugin = _parse_plugin(version_dir, source_dir.name)
            if plugin:
                plugins.append(plugin)

    # Sort by name for consistent display
    return sorted(plugins, key=lambda p: p.name.lower())


def _find_best_version(plugin_dir: Path) -> Path | None:
    """Find the best version directory for a plugin.

    Prefers semantic versions (e.g., 1.0.0) over commit hashes.
    For semver, picks the highest version. For hashes, picks most recently modified.
    """
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
        # Sort by version tuple descending
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
        # Handle prerelease suffixes like "1.0.0-beta"
        if "-" in part:
            part = part.split("-")[0]
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return tuple(result)


def _parse_plugin(version_dir: Path, source: str) -> Plugin | None:
    """Parse plugin metadata from a version directory."""
    plugin_json = version_dir / ".claude-plugin" / "plugin.json"

    if not plugin_json.exists():
        return None

    try:
        with plugin_json.open() as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    # Count skills and agents
    # Skills can be in "commands/" or "skills/" directory
    commands_dir = version_dir / "commands"
    skills_dir = version_dir / "skills"
    agents_dir = version_dir / "agents"

    skill_count = _count_items(commands_dir, ".md") + _count_items(skills_dir, ".md")
    agent_count = _count_items(agents_dir, ".md")

    return Plugin(
        name=data.get("name", version_dir.parent.name),
        version=data.get("version", version_dir.name),
        description=data.get("description", ""),
        source=source,
        repository=data.get("repository") or data.get("homepage"),
        skill_count=skill_count,
        agent_count=agent_count,
        path=version_dir,
    )


def _count_items(directory: Path, suffix: str) -> int:
    """Count files with given suffix in a directory."""
    if not directory.exists():
        return 0
    return len([f for f in directory.iterdir() if f.is_file() and f.suffix == suffix])
