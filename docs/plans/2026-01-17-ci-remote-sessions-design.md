# CI & Remote Sessions Design

> **Status:** Draft - Ready for implementation
> **Created:** 2026-01-17
> **Author:** Brainstormed with Claude

## Vision

Extend claude-dash to monitor GitHub Actions workflows that use Claude Code, with a future path for remote/background session monitoring when Anthropic exposes an API.

## Scope

### In Scope (Iteration 9)
- Auto-discover repos with `claude-code-action` workflows
- CI summary panel on Overview tab
- Dedicated CI tab with per-repo breakdown
- Hidden repos management

### Future (Iteration 10+)
- Remote/background session monitoring (blocked on API)

---

## Data Sources

### GitHub Actions Discovery

```python
def discover_claude_repos():
    """Find repos using claude-code-action."""
    # 1. List all accessible repos
    repos = gh_api("/user/repos")

    # 2. For each, check workflows
    claude_repos = []
    for repo in repos:
        workflows = gh_api(f"/repos/{repo}/actions/workflows")
        for wf in workflows:
            content = fetch_workflow_yaml(wf)
            if "claude-code-action" in content or "anthropics/claude-code" in content:
                claude_repos.append(repo)
                break

    return claude_repos
```

### Settings Storage

New file or extend existing: `~/.claude/cdash-settings.json`

```json
{
  "github_actions": {
    "discovered_repos": ["owner/repo1", "owner/repo2"],
    "hidden_repos": ["owner/repo-i-dont-want"],
    "last_discovery": "2026-01-17T10:00:00Z"
  }
}
```

### Refresh Strategy

| Data | Interval | Trigger |
|------|----------|---------|
| Repo discovery | Weekly | First launch, manual `R` |
| Run data | 60s | Auto-refresh |
| Settings | On change | User action |

---

## UI Design

### Overview Tab Integration

New "CI ACTIVITY" panel (compact):

```
├─────────────────────────────────────────────────────────────────┤
│ CI ACTIVITY (today)                        │ WEEKLY TREND       │
│ ● 15 runs  ✓ 12 passed  ✗ 3 failed        │ █ █ ▄ █ ▄ ░ ░      │
│   ios-app: 8 runs (7✓ 1✗)                 │                     │
│   api-svc: 7 runs (5✓ 2✗)                 │                     │
│                                [6: CI tab] │                     │
├─────────────────────────────────────────────────────────────────┤
```

**Data shown:**
- Today's totals: runs, passed, failed
- Top 2-3 repos by activity
- Hint to press `6` for full CI tab

### CI Tab (Tab 6)

Full dedicated view:

```
┌─────────────────────────────────────────────────────────────────┐
│ [1:Overview] [2:Plugins] [3:MCP] [4:Skills] [5:Agents] [6:CI]   │
├─────────────────────────────────────────────────────────────────┤
│ GITHUB ACTIONS (Claude Code)                    ↻ 45s ago       │
├─────────────────────────────────────────────────────────────────┤
│ REPO                    TODAY      WEEK     SUCCESS   LAST RUN  │
│ ─────────────────────────────────────────────────────────────── │
│ schmoli/ios-app           8         42        95%     2m ago ✓  │
│ schmoli/api-service       7         31        87%     15m ago ✗ │
│ schmoli/dashboard         0         12       100%     2d ago ✓  │
│ work-org/backend          0          8        75%     1d ago ✓  │
│                                                                 │
│ [dim]── Hidden: 2 repos (press H to manage) ──[/dim]            │
├─────────────────────────────────────────────────────────────────┤
│ RECENT RUNS                                                     │
│ ✗ schmoli/api-service    PR #142 "fix auth"         15m ago     │
│ ✓ schmoli/ios-app        PR #89 "add dark mode"     18m ago     │
│ ✓ schmoli/ios-app        issue #45 "refactor"       1h ago      │
│ ✓ schmoli/api-service    PR #141 "update deps"      2h ago      │
├─────────────────────────────────────────────────────────────────┤
│ R:refresh  H:hide/show repos  Enter:open in browser  /:filter   │
└─────────────────────────────────────────────────────────────────┘
```

**Columns:**
| Column | Description |
|--------|-------------|
| REPO | owner/name (truncated if needed) |
| TODAY | runs in last 24h |
| WEEK | runs in last 7d |
| SUCCESS | pass rate (week) |
| LAST RUN | relative time + status icon |

**Keybindings:**
| Key | Action |
|-----|--------|
| `R` | Force refresh (discovery + runs) |
| `H` | Toggle hidden repos modal |
| `Enter` | Open selected run in browser |
| `/` | Filter by repo name |
| `j/k` | Navigate list |

### Hidden Repos Modal

```
┌─────────────────────────────────────────────┐
│ MANAGE REPOS                                │
├─────────────────────────────────────────────┤
│ [x] schmoli/ios-app                         │
│ [x] schmoli/api-service                     │
│ [x] schmoli/dashboard                       │
│ [ ] schmoli/old-prototype      (hidden)     │
│ [ ] work-org/internal-tools    (hidden)     │
│ [x] work-org/backend                        │
├─────────────────────────────────────────────┤
│ Space:toggle  Enter:done  R:re-discover     │
└─────────────────────────────────────────────┘
```

---

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `src/cdash/data/github.py` | GH API client, repo discovery, run fetching |
| `src/cdash/data/settings.py` | Settings load/save for hidden repos |
| `src/cdash/components/ci.py` | CIActivityPanel, CITab, RepoModal |
| `tests/test_github.py` | Tests for discovery, filtering |
| `tests/test_ci.py` | Tests for CI components |

### Data Models

```python
@dataclass
class WorkflowRun:
    repo: str              # "owner/repo"
    run_id: int
    workflow_name: str
    status: str            # "success", "failure", "in_progress"
    conclusion: str | None
    trigger: str           # "pull_request", "issue_comment", etc.
    pr_number: int | None
    title: str             # PR/issue title or commit message
    created_at: datetime
    html_url: str

@dataclass
class RepoStats:
    repo: str
    runs_today: int
    runs_week: int
    success_rate: float    # 0.0 - 1.0
    last_run: WorkflowRun | None
    is_hidden: bool
```

### GitHub API Calls

```python
# List user repos (paginated)
GET /user/repos?per_page=100

# Get workflows for repo
GET /repos/{owner}/{repo}/actions/workflows

# Get workflow file content (to check for claude-code-action)
GET /repos/{owner}/{repo}/contents/.github/workflows/{file}

# Get recent runs
GET /repos/{owner}/{repo}/actions/runs?per_page=50&created=>={week_ago}
```

### Rate Limiting

GitHub API: 5000 requests/hour for authenticated users

**Budget per refresh cycle (60s):**
- Run fetches: 1 request per visible repo
- 10 repos = 10 requests/minute = 600/hour (safe)

**Discovery (weekly):**
- Repo list: ~5 requests (paginated)
- Workflow check: 1-2 per repo
- 100 repos = ~200 requests (one-time, safe)

---

## Iteration Plan

### Iteration 9: CI Tab

- [ ] Create `src/cdash/data/github.py` with discovery + run fetching
- [ ] Create `src/cdash/data/settings.py` for hidden repos
- [ ] Add CIActivityPanel to Overview tab
- [ ] Create CI tab with repo table + recent runs
- [ ] Implement hidden repos modal
- [ ] Add keybindings (R, H, Enter, /)
- [ ] Update tab navigation (1-6 keys)
- [ ] Write tests
- [ ] Update CLAUDE.md

**Ship criteria:** See Claude Code GH Actions across repos with hide/show control.

### Iteration 10+: Remote Sessions (Future)

Blocked on: Anthropic API for listing background sessions

**When available:**
- Show active background tasks
- Status: running/completed/failed
- Teleport action (opens terminal with `claude --teleport <id>`)
- Session duration, token usage
- Integrate into Overview + dedicated section

**Data we'd want:**
```python
@dataclass
class RemoteSession:
    session_id: str
    status: str            # "running", "completed", "failed"
    started_at: datetime
    completed_at: datetime | None
    prompt_preview: str
    repo: str | None
    branch: str | None
    token_usage: int | None
```

---

## Open Questions

- Should we cache workflow run data locally for offline viewing?
- Add cost estimation if we can detect model usage from run logs?
- Support for GitHub Enterprise (different API base URL)?

---

## References

- [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)
- [Claude Code Background Tasks](https://apidog.com/blog/claude-code-background-tasks/)
- [GitHub Actions API](https://docs.github.com/en/rest/actions)
