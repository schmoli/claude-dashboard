# GitHub Tab Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move CI tab to position 2, rename to "GitHub", and add Claude agent activity features (duration, aggregate stats, quick actions).

**Architecture:** Reorder existing tab infrastructure, enhance WorkflowRun dataclass with duration, add aggregate stats header component, add keyboard handlers for browser actions.

**Tech Stack:** Python, Textual, subprocess (for `open` command on macOS)

---

## Task 1: Rename Tab ID and Label

**Files:**
- Modify: `src/cdash/components/tabs.py:138-139`
- Modify: `src/cdash/app.py:89`
- Modify: `tests/test_tabs.py:40,93-99`

**Step 1: Update test for new tab ID**

Edit `tests/test_tabs.py` - change `tab-ci` references to `tab-github`:

```python
# In test_six_tabs_exist (line 40):
assert tabs.query_one("#tab-github") is not None  # was #tab-ci

# In test_switch_to_ci_with_6 (lines 93-99), rename entire test:
async def test_switch_to_github_with_6(self):
    """Pressing 6 switches to GitHub tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("6")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-github"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tabs.py::TestDashboardTabs::test_six_tabs_exist tests/test_tabs.py::TestTabNavigation::test_switch_to_github_with_6 -v`
Expected: FAIL - `tab-github` not found

**Step 3: Update tabs.py**

Edit `src/cdash/components/tabs.py` line 138-139:

```python
            with TabPane("GitHub", id="tab-github"):
                yield CITab()
```

**Step 4: Update app.py binding**

Edit `src/cdash/app.py` line 89:

```python
        ("6", "switch_tab('tab-github')", "GitHub"),
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_tabs.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/cdash/components/tabs.py src/cdash/app.py tests/test_tabs.py
git commit -m "refactor(ui): rename CI tab to GitHub

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Reorder Tab to Position 2

**Files:**
- Modify: `src/cdash/components/tabs.py:127-139`
- Modify: `src/cdash/app.py:84-89`
- Modify: `tests/test_tabs.py` (multiple navigation tests)

**Step 1: Update navigation tests for new order**

Edit `tests/test_tabs.py` - update all navigation tests for new order:
- Key 2 = GitHub (was Plugins)
- Key 3 = Plugins (was MCP)
- Key 4 = MCP (was Skills)
- Key 5 = Skills (was Agents)
- Key 6 = Agents (was CI)

```python
# Replace test_switch_to_plugins_with_2:
async def test_switch_to_github_with_2(self):
    """Pressing 2 switches to GitHub tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-github"

# Replace test_switch_to_mcp_with_3:
async def test_switch_to_plugins_with_3(self):
    """Pressing 3 switches to Plugins tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("3")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-plugins"

# Replace test_switch_to_skills_with_4:
async def test_switch_to_mcp_with_4(self):
    """Pressing 4 switches to MCP Servers tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("4")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-mcp"

# Replace test_switch_to_agents_with_5:
async def test_switch_to_skills_with_5(self):
    """Pressing 5 switches to Skills tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("5")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-skills"

# Delete test_switch_to_github_with_6 (from Task 1), add:
async def test_switch_to_agents_with_6(self):
    """Pressing 6 switches to Agents tab."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("6")
        tabs = app.query_one(DashboardTabs)
        assert tabs.active == "tab-agents"
```

Also update `tests/test_tabs.py` TestTabsRender class - fix key presses:

```python
# test_plugins_tab_has_height: press "3" instead of "2"
# test_mcp_tab_has_height: press "4" instead of "3"
# test_skills_tab_has_height: press "5" instead of "4"
# test_agents_tab_has_height: press "6" instead of "5"
# Delete test_ci_tab_has_height (CI is now GitHub at position 2)
# Add test_github_tab_has_height with press "2"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tabs.py::TestTabNavigation -v`
Expected: FAIL - wrong tabs for keys

**Step 3: Reorder tabs in tabs.py**

Edit `src/cdash/components/tabs.py` lines 127-139 to new order:

```python
    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tab-overview"):
            with TabPane("Overview", id="tab-overview"):
                yield OverviewTab()
            with TabPane("GitHub", id="tab-github"):
                yield CITab()
            with TabPane("Plugins", id="tab-plugins"):
                yield PluginsTab()
            with TabPane("MCP Servers", id="tab-mcp"):
                yield MCPServersTab()
            with TabPane("Skills", id="tab-skills"):
                yield SkillsTab()
            with TabPane("Agents", id="tab-agents"):
                yield AgentsTab()
```

**Step 4: Update key bindings in app.py**

Edit `src/cdash/app.py` lines 84-89:

```python
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_tab('tab-overview')", "Overview"),
        ("2", "switch_tab('tab-github')", "GitHub"),
        ("3", "switch_tab('tab-plugins')", "Plugins"),
        ("4", "switch_tab('tab-mcp')", "MCP"),
        ("5", "switch_tab('tab-skills')", "Skills"),
        ("6", "switch_tab('tab-agents')", "Agents"),
    ]
```

**Step 5: Run all tests**

Run: `pytest tests/test_tabs.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/cdash/components/tabs.py src/cdash/app.py tests/test_tabs.py
git commit -m "feat(ui): move GitHub tab to position 2

Tab order: Overview → GitHub → Plugins → MCP → Skills → Agents

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Add Duration to WorkflowRun

**Files:**
- Modify: `src/cdash/data/github.py:35-53,67-86`
- Modify: `tests/test_github.py`

**Step 1: Write test for duration property**

Add to `tests/test_github.py`:

```python
from datetime import datetime, timezone, timedelta
from cdash.data.github import WorkflowRun, parse_workflow_run

class TestWorkflowRunDuration:
    """Tests for workflow run duration."""

    def test_duration_completed_run(self):
        """Duration calculated for completed run."""
        created = datetime(2026, 1, 17, 10, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2026, 1, 17, 10, 5, 30, tzinfo=timezone.utc)
        run = WorkflowRun(
            repo="o/r",
            run_id=1,
            workflow_name="CI",
            status="completed",
            conclusion="success",
            trigger="push",
            pr_number=None,
            title="test",
            created_at=created,
            updated_at=updated,
            html_url="",
        )
        assert run.duration_seconds == 330  # 5m 30s

    def test_duration_in_progress(self):
        """Duration is None for in-progress runs."""
        now = datetime.now(timezone.utc)
        run = WorkflowRun(
            repo="o/r",
            run_id=1,
            workflow_name="CI",
            status="in_progress",
            conclusion=None,
            trigger="push",
            pr_number=None,
            title="test",
            created_at=now,
            updated_at=now,
            html_url="",
        )
        assert run.duration_seconds is None

    def test_duration_formatted(self):
        """Duration formats nicely."""
        created = datetime(2026, 1, 17, 10, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2026, 1, 17, 10, 12, 45, tzinfo=timezone.utc)
        run = WorkflowRun(
            repo="o/r",
            run_id=1,
            workflow_name="CI",
            status="completed",
            conclusion="success",
            trigger="push",
            pr_number=None,
            title="test",
            created_at=created,
            updated_at=updated,
            html_url="",
        )
        assert run.duration_formatted == "12m"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github.py::TestWorkflowRunDuration -v`
Expected: FAIL - `updated_at` not in dataclass

**Step 3: Add updated_at and duration to WorkflowRun**

Edit `src/cdash/data/github.py`:

Add `updated_at` field to dataclass (after `created_at`, line ~47):

```python
@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""

    repo: str
    run_id: int
    workflow_name: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: str | None  # "success", "failure", "cancelled", etc.
    trigger: str  # "pull_request", "issue_comment", "push", etc.
    pr_number: int | None
    title: str
    created_at: datetime
    updated_at: datetime
    html_url: str

    @property
    def is_success(self) -> bool:
        """Check if run was successful."""
        return self.conclusion == "success"

    @property
    def duration_seconds(self) -> int | None:
        """Duration in seconds, or None if not completed."""
        if self.status != "completed":
            return None
        return int((self.updated_at - self.created_at).total_seconds())

    @property
    def duration_formatted(self) -> str | None:
        """Duration as human-readable string."""
        secs = self.duration_seconds
        if secs is None:
            return None
        mins = secs // 60
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        remaining_mins = mins % 60
        return f"{hours}h{remaining_mins}m"
```

**Step 4: Update parse_workflow_run**

Edit `src/cdash/data/github.py` function `parse_workflow_run` (~line 75):

```python
def parse_workflow_run(repo: str, data: dict) -> WorkflowRun:
    """Parse a workflow run from GitHub API response."""
    pr_number = None
    if data.get("pull_requests"):
        pr_number = data["pull_requests"][0].get("number")

    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

    return WorkflowRun(
        repo=repo,
        run_id=data["id"],
        workflow_name=data.get("name", ""),
        status=data.get("status", ""),
        conclusion=data.get("conclusion"),
        trigger=data.get("event", ""),
        pr_number=pr_number,
        title=data.get("display_title", ""),
        created_at=created_at,
        updated_at=updated_at,
        html_url=data.get("html_url", ""),
    )
```

**Step 5: Fix existing tests that construct WorkflowRun**

Update `tests/test_ci.py` to include `updated_at`:

```python
# In test_repo_row_renders:
last_run = WorkflowRun(
    "o/r", 1, "CI", "completed", "success", "push", None, "t", now, now, ""
)
```

**Step 6: Run all tests**

Run: `pytest tests/test_github.py tests/test_ci.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/cdash/data/github.py tests/test_github.py tests/test_ci.py
git commit -m "feat(github): add duration tracking to workflow runs

- Add updated_at field to WorkflowRun
- Add duration_seconds and duration_formatted properties

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Display Duration in RunRow

**Files:**
- Modify: `src/cdash/components/ci.py:174-206`
- Modify: `tests/test_ci.py`

**Step 1: Write test for duration display**

Add to `tests/test_ci.py`:

```python
def test_run_row_shows_duration(self):
    """Run row displays duration for completed runs."""
    from cdash.components.ci import RunRow

    created = datetime(2026, 1, 17, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 17, 10, 8, 0, tzinfo=timezone.utc)
    run = WorkflowRun(
        "owner/repo", 1, "CI", "completed", "success",
        "push", None, "test title", created, updated, ""
    )
    row = RunRow(run)
    rendered = row.render()
    assert "8m" in rendered

def test_run_row_shows_failure_reason(self):
    """Run row displays failure conclusion."""
    from cdash.components.ci import RunRow

    now = datetime.now(timezone.utc)
    run = WorkflowRun(
        "owner/repo", 1, "CI", "completed", "timed_out",
        "push", None, "test", now, now, ""
    )
    row = RunRow(run)
    rendered = row.render()
    assert "timed_out" in rendered
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci.py::TestCITab::test_run_row_shows_duration -v`
Expected: FAIL - "8m" not in rendered

**Step 3: Update RunRow.render()**

Edit `src/cdash/components/ci.py` class `RunRow`, method `render` (~line 188):

```python
    def render(self) -> str:
        r = self._run
        status = "[green]✓[/]" if r.is_success else "[red]✗[/]"

        # Format trigger info
        if r.pr_number:
            trigger = f"PR #{r.pr_number}"
        else:
            trigger = r.trigger[:12]

        # Truncate title
        title = r.title
        if len(title) > 20:
            title = title[:17] + "..."

        time = format_relative_time(r.created_at)

        # Duration (only for completed)
        duration = r.duration_formatted or ""
        if duration:
            duration = f"{duration:>4}"

        # Show failure reason for non-success
        reason = ""
        if r.conclusion and r.conclusion not in ("success", None):
            reason = f"[dim]{r.conclusion}[/]"

        repo_short = r.repo.split("/")[-1]
        return f'{status} {repo_short:<14} {trigger:<10} "{title}"  {duration}  {reason}  {time}'
```

**Step 4: Run tests**

Run: `pytest tests/test_ci.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/components/ci.py tests/test_ci.py
git commit -m "feat(ui): show duration and failure reason in run rows

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Add Aggregate Stats Header

**Files:**
- Modify: `src/cdash/components/ci.py:209-287`
- Modify: `tests/test_ci.py`

**Step 1: Write test for aggregate stats**

Add to `tests/test_ci.py`:

```python
def test_ci_tab_shows_aggregate_stats(self):
    """CI tab header shows aggregate statistics."""
    from cdash.components.ci import CITab

    tab = CITab()
    # Simulate data with known totals
    created = datetime(2026, 1, 17, 10, 0, 0, tzinfo=timezone.utc)
    runs = [
        WorkflowRun("o/r", i, "CI", "completed", "success" if i % 3 else "failure",
                    "push", None, "t", created, created, "")
        for i in range(12)
    ]
    stats = [RepoStats("o/r", 12, 50, 0.75, runs[0], False)]
    tab.update_data(stats, runs)

    # Check aggregate stats are tracked
    assert tab._total_duration_today == 0  # 0 because created==updated
    assert tab._timeout_count == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci.py::TestCITab::test_ci_tab_shows_aggregate_stats -v`
Expected: FAIL - `_total_duration_today` not found

**Step 3: Add aggregate stats to CITab**

Edit `src/cdash/components/ci.py` class `CITab`:

Add instance variables in `__init__` (~line 270):

```python
    def __init__(self) -> None:
        super().__init__()
        self._repo_stats: list[RepoStats] = []
        self._recent_runs: list[WorkflowRun] = []
        self._hidden_count = 0
        self._loading = False
        self._discovered = False
        # Aggregate stats
        self._total_duration_today = 0  # seconds
        self._timeout_count = 0
        self._runs_today = 0
        self._passed_today = 0
        self._failed_today = 0
```

Add aggregate stats widget in `compose` (after title):

```python
    def compose(self) -> ComposeResult:
        yield Static("GITHUB ACTIONS (Claude Code)", classes="ci-title")
        yield Static("", classes="ci-aggregate", id="aggregate-stats")
        yield Center(LoadingIndicator(), id="loading-container")
        # ... rest unchanged
```

Add CSS for aggregate stats (in DEFAULT_CSS):

```python
    CITab > .ci-aggregate {
        height: 1;
        padding: 0 1;
        margin-bottom: 1;
    }
```

Update `update_data` to calculate aggregates:

```python
    def update_data(
        self,
        repo_stats: list[RepoStats],
        recent_runs: list[WorkflowRun],
    ) -> None:
        """Update the display with new data."""
        self._repo_stats = repo_stats
        self._recent_runs = recent_runs
        self._hidden_count = sum(1 for s in repo_stats if s.is_hidden)

        # Calculate aggregates from today's runs
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_runs = [r for r in recent_runs if r.created_at >= today_start]

        self._runs_today = len(today_runs)
        self._passed_today = sum(1 for r in today_runs if r.is_success)
        self._failed_today = self._runs_today - self._passed_today
        self._total_duration_today = sum(
            r.duration_seconds or 0 for r in today_runs if r.status == "completed"
        )
        self._timeout_count = sum(
            1 for r in today_runs if r.conclusion == "timed_out"
        )

        self._refresh_display()
```

Add `_refresh_aggregate_stats` method:

```python
    def _refresh_aggregate_stats(self) -> None:
        """Update aggregate stats display."""
        try:
            agg = self.query_one("#aggregate-stats", Static)
            mins = self._total_duration_today // 60
            pass_rate = (
                f"{int(100 * self._passed_today / self._runs_today)}%"
                if self._runs_today > 0 else "-"
            )
            timeout_warn = f" [yellow]| {self._timeout_count} timeout[/]" if self._timeout_count else ""
            agg.update(
                f"TODAY: [cyan]{self._runs_today}[/] runs | "
                f"[green]{mins}m[/] total | "
                f"{pass_rate} pass{timeout_warn}"
            )
        except Exception:
            pass
```

Call it from `_refresh_display`:

```python
    def _refresh_display(self) -> None:
        """Refresh the UI."""
        self._refresh_aggregate_stats()
        # ... rest of method unchanged
```

**Step 4: Run tests**

Run: `pytest tests/test_ci.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/components/ci.py tests/test_ci.py
git commit -m "feat(ui): add aggregate stats header to GitHub tab

Shows: runs today, total duration, pass rate, timeout warnings

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Add Quick Actions (Open in Browser)

**Files:**
- Modify: `src/cdash/components/ci.py`
- Add: `tests/test_ci.py` (browser action tests)

**Step 1: Write test for open action**

Add to `tests/test_ci.py`:

```python
from unittest.mock import patch

def test_run_row_has_url(self):
    """Run row stores URL for browser action."""
    from cdash.components.ci import RunRow

    now = datetime.now(timezone.utc)
    run = WorkflowRun(
        "owner/repo", 123, "CI", "completed", "success",
        "pull_request", 42, "test", now, now,
        "https://github.com/owner/repo/actions/runs/123"
    )
    row = RunRow(run)
    assert row._run.html_url == "https://github.com/owner/repo/actions/runs/123"
    assert row._run.pr_number == 42
```

**Step 2: Run test**

Run: `pytest tests/test_ci.py::TestCITab::test_run_row_has_url -v`
Expected: PASS (URL already stored)

**Step 3: Add keybindings to CITab**

Edit `src/cdash/components/ci.py` CITab BINDINGS:

```python
    BINDINGS = [
        ("h", "toggle_hidden", "Hide/Show repos"),
        ("r", "refresh", "Refresh"),
        ("d", "discover", "Discover repos"),
        ("o", "open_run", "Open in browser"),
        ("p", "open_pr", "Open PR"),
    ]
```

**Step 4: Add action methods**

Add to CITab class:

```python
    def _get_selected_run(self) -> WorkflowRun | None:
        """Get first recent run (selection not implemented yet)."""
        return self._recent_runs[0] if self._recent_runs else None

    def action_open_run(self) -> None:
        """Open selected run in browser."""
        run = self._get_selected_run()
        if run and run.html_url:
            import subprocess
            subprocess.run(["open", run.html_url], check=False)
            self.notify(f"Opening run #{run.run_id}")
        else:
            self.notify("No run selected")

    def action_open_pr(self) -> None:
        """Open associated PR in browser."""
        run = self._get_selected_run()
        if run and run.pr_number:
            url = f"https://github.com/{run.repo}/pull/{run.pr_number}"
            import subprocess
            subprocess.run(["open", url], check=False)
            self.notify(f"Opening PR #{run.pr_number}")
        else:
            self.notify("No PR associated with this run")
```

**Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/cdash/components/ci.py tests/test_ci.py
git commit -m "feat(ui): add quick actions to open runs/PRs in browser

- o: open workflow run
- p: open associated PR

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Update Overview Tab CI Hint

**Files:**
- Modify: `src/cdash/components/ci.py:78`

**Step 1: Update hint text**

Edit `src/cdash/components/ci.py` CIActivityPanel compose method:

```python
    def compose(self) -> ComposeResult:
        yield Static("CI ACTIVITY (today)", classes="ci-header")
        yield Static("", classes="ci-stats")
        yield Static("", classes="ci-repos")
        yield Static("[2: GitHub tab]", classes="ci-hint")  # was [6: CI tab]
```

**Step 2: Run tests**

Run: `pytest tests/ -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/cdash/components/ci.py
git commit -m "fix(ui): update CI hint to reference GitHub tab at key 2

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Update CLAUDE.md and Design Doc

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/plans/2026-01-17-claude-dash-design.md`

**Step 1: Update design doc layout**

Update the layout diagram to show new tab order and GitHub tab features.

**Step 2: Update CLAUDE.md**

Add note about GitHub tab in "What's Working" section.

**Step 3: Commit**

```bash
git add CLAUDE.md docs/plans/2026-01-17-claude-dash-design.md
git commit -m "docs: update design doc with GitHub tab changes

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Rename tab-ci → tab-github | tabs.py, app.py, test_tabs.py |
| 2 | Reorder tab to position 2 | tabs.py, app.py, test_tabs.py |
| 3 | Add duration to WorkflowRun | github.py, test_github.py, test_ci.py |
| 4 | Display duration in RunRow | ci.py, test_ci.py |
| 5 | Add aggregate stats header | ci.py, test_ci.py |
| 6 | Add quick actions (o/p) | ci.py, test_ci.py |
| 7 | Update Overview hint | ci.py |
| 8 | Update docs | CLAUDE.md, design.md |

## Unresolved Questions

None - design is complete.
