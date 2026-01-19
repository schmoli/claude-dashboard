"""Resource stats for Claude processes using psutil."""

import time
from dataclasses import dataclass

import psutil

# Cache for resource stats (sampling CPU needs time between calls)
_resources_cache: "ResourceStats | None" = None
_resources_cache_time: float = 0
_CACHE_TTL = 2.0  # seconds


@dataclass
class ResourceStats:
    """Aggregate resource usage for all Claude processes."""

    process_count: int
    cpu_percent: float  # combined CPU across all processes
    memory_mb: float  # combined memory in MB
    memory_percent: float  # combined memory as % of system RAM
    claude_dir_mb: float = 0.0  # ~/.claude directory size in MB


def find_claude_processes() -> list[psutil.Process]:
    """Find all Claude-related processes.

    Looks for processes named 'claude' or with 'claude' in cmdline.

    Returns:
        List of psutil.Process objects
    """
    claude_procs = []

    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = proc.info.get("name", "").lower()
            cmdline = proc.info.get("cmdline") or []

            # Match process name
            if "claude" in name:
                claude_procs.append(proc)
                continue

            # Match command line (e.g., 'node /path/to/claude')
            for arg in cmdline:
                if isinstance(arg, str) and "claude" in arg.lower():
                    claude_procs.append(proc)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return claude_procs


def get_resource_stats(use_cache: bool = True) -> ResourceStats:
    """Get aggregate resource stats for all Claude processes.

    Args:
        use_cache: If True, return cached data if fresh

    Returns:
        ResourceStats with combined CPU/memory usage
    """
    global _resources_cache, _resources_cache_time

    # Return cached data if fresh
    if use_cache and _resources_cache is not None:
        if time.time() - _resources_cache_time < _CACHE_TTL:
            return _resources_cache

    procs = find_claude_processes()
    total_cpu = 0.0
    total_memory_bytes = 0

    for proc in procs:
        try:
            # cpu_percent needs to be called twice with interval or cached
            # Here we get non-blocking measurement (since we refresh frequently)
            total_cpu += proc.cpu_percent(interval=None)
            mem_info = proc.memory_info()
            total_memory_bytes += mem_info.rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    total_memory_mb = total_memory_bytes / (1024 * 1024)
    total_mem = psutil.virtual_memory()
    memory_percent = (total_memory_bytes / total_mem.total) * 100 if total_mem.total else 0

    # Get ~/.claude directory size
    claude_dir_mb = 0.0
    try:
        import os
        claude_dir = os.path.expanduser("~/.claude")
        if os.path.isdir(claude_dir):
            total_bytes = 0
            for dirpath, dirnames, filenames in os.walk(claude_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_bytes += os.path.getsize(fp)
                    except (OSError, IOError):
                        pass
            claude_dir_mb = total_bytes / (1024 * 1024)
    except Exception:
        pass

    stats = ResourceStats(
        process_count=len(procs),
        cpu_percent=total_cpu,
        memory_mb=total_memory_mb,
        memory_percent=memory_percent,
        claude_dir_mb=claude_dir_mb,
    )

    # Update cache
    _resources_cache = stats
    _resources_cache_time = time.time()

    return stats
