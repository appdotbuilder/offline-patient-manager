"""
Smoke tests for sperm analysis dashboard UI.
"""

import pytest
from nicegui.testing import User
from nicegui import ui

from app.database import reset_db
from app.dashboard import SpermAnalysisDashboard


@pytest.fixture
def new_db():
    reset_db()
    yield
    reset_db()


async def test_dashboard_page_loads(user: User, new_db) -> None:
    """Test that the main dashboard page loads successfully."""
    dashboard = SpermAnalysisDashboard()

    @ui.page("/test_dashboard")
    def test_page():
        dashboard.create_main_layout()

    await user.open("/test_dashboard")

    # Check main components are present
    await user.should_see("🔬 Sperm Analysis System")
    await user.should_see("📁 Upload Files")
    await user.should_see("📋 Recent Uploads")
    await user.should_see("📊 Analysis Results")


async def test_upload_section_present(user: User, new_db) -> None:
    """Test that upload section displays correctly."""
    dashboard = SpermAnalysisDashboard()

    @ui.page("/test_upload_section")
    def test_page():
        dashboard.create_main_layout()

    await user.open("/test_upload_section")

    await user.should_see("Supported formats: JPG, PNG (images) • MP4, AVI (videos)")

    # Check upload component exists
    upload_elements = user.find(ui.upload).elements
    assert len(upload_elements) > 0


async def test_empty_state_messages(user: User, new_db) -> None:
    """Test empty state messages display correctly."""
    dashboard = SpermAnalysisDashboard()

    @ui.page("/test_empty_state")
    def test_page():
        dashboard.create_main_layout()

    await user.open("/test_empty_state")

    # Should show empty states
    await user.should_see("No files uploaded yet")
    await user.should_see("Select a file from the list to view analysis results")


async def test_statistics_section_present(user: User, new_db) -> None:
    """Test that statistics section displays correctly."""
    dashboard = SpermAnalysisDashboard()

    @ui.page("/test_stats_section")
    def test_page():
        dashboard.create_main_layout()

    await user.open("/test_stats_section")

    # Check statistics labels are present
    await user.should_see("Total Files")
    await user.should_see("Images")
    await user.should_see("Videos")
    await user.should_see("Completed")


class TestDashboardInitialization:
    """Test dashboard class initialization."""

    def test_dashboard_creates_successfully(self):
        """Test dashboard can be created without errors."""
        dashboard = SpermAnalysisDashboard()

        assert dashboard.file_service is not None
        assert dashboard.analysis_service is not None
        assert dashboard.results_display is not None
        assert dashboard.current_file_id is None

    def test_dashboard_services_are_configured(self):
        """Test dashboard uses properly configured services."""
        dashboard = SpermAnalysisDashboard()

        # Services should be properly configured instances
        from app.file_service import FileUploadService
        from app.analysis_service import SpermAnalysisService
        from app.results_display import ResultsDisplayService

        assert isinstance(dashboard.file_service, FileUploadService)
        assert isinstance(dashboard.analysis_service, SpermAnalysisService)
        assert isinstance(dashboard.results_display, ResultsDisplayService)
