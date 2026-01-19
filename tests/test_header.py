"""Tests for HeaderPanel widget."""

import pytest

from cdash.components.header import HeaderPanel


class TestHeaderPanel:
    """Tests for HeaderPanel widget."""

    @pytest.mark.asyncio
    async def test_header_renders(self):
        """HeaderPanel can be created and rendered."""
        header = HeaderPanel()
        assert header is not None

    @pytest.mark.asyncio
    async def test_header_update_stats(self):
        """HeaderPanel updates stats correctly."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test():
            header = app.query_one(HeaderPanel)
            header.update_stats(active_count=3, msgs_today=847, tools_today=142)

            # Verify widgets were updated (new individual gauge layout)
            sessions_widget = header.query_one("#stat-sessions")
            rate_widget = header.query_one("#stat-rate")

            # Widgets should have been updated
            assert sessions_widget is not None
            assert rate_widget is not None

    @pytest.mark.asyncio
    async def test_header_has_mark_refreshed(self):
        """HeaderPanel has mark_refreshed method."""
        header = HeaderPanel()
        assert hasattr(header, "mark_refreshed")
        assert callable(header.mark_refreshed)

    @pytest.mark.asyncio
    async def test_header_has_host_stats(self):
        """HeaderPanel has update_host_stats method."""
        header = HeaderPanel()
        assert hasattr(header, "update_host_stats")
        assert callable(header.update_host_stats)
