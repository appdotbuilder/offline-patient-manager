"""
Main dashboard for sperm analysis application.
"""

import asyncio
from typing import Optional
import logging

from nicegui import ui
from nicegui.events import UploadEventArguments

from app.file_service import get_file_service
from app.analysis_service import get_analysis_service
from app.results_display import get_results_display_service
from app.models import UploadedFile, AnalysisResult, ProcessingStatus, FileType
from app.database import get_session

logger = logging.getLogger(__name__)


class SpermAnalysisDashboard:
    """Main dashboard for sperm analysis application."""

    def __init__(self):
        self.file_service = get_file_service()
        self.analysis_service = get_analysis_service()
        self.results_display = get_results_display_service()

        # UI components
        self.file_list_container = None
        self.stats_container = None
        self.current_file_id: Optional[int] = None

    def create_main_layout(self) -> None:
        """Create the main dashboard layout."""
        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Header
        with ui.row().classes("w-full bg-primary text-white p-4 mb-6 shadow-lg"):
            ui.label("🔬 Sperm Analysis System").classes("text-2xl font-bold")
            ui.space()
            ui.label("Advanced AI-powered CASA analysis").classes("text-lg opacity-90")

        # Main content
        with ui.row().classes("w-full gap-6"):
            # Left panel - Upload and file list
            with ui.column().classes("w-1/3"):
                self._create_upload_section()
                self._create_file_list_section()

            # Right panel - Analysis results
            with ui.column().classes("w-2/3"):
                self._create_analysis_results_section()

    def _create_upload_section(self) -> None:
        """Create file upload section."""
        with ui.card().classes("w-full p-6 mb-6 shadow-lg"):
            ui.label("📁 Upload Files").classes("text-xl font-bold mb-4")
            ui.label("Supported formats: JPG, PNG (images) • MP4, AVI (videos)").classes("text-sm text-gray-600 mb-4")

            # Upload component
            upload = ui.upload(on_upload=self._handle_upload, multiple=True, auto_upload=True).classes("w-full")

            upload.props('accept=".jpg,.jpeg,.png,.mp4,.avi" max-file-size="524288000"')

            # Upload stats
            self.stats_container = ui.row().classes("mt-4 gap-4 w-full")
            self._update_upload_stats()

    def _create_file_list_section(self) -> None:
        """Create file list section."""
        with ui.card().classes("w-full p-6 shadow-lg"):
            ui.label("📋 Recent Uploads").classes("text-xl font-bold mb-4")

            self.file_list_container = ui.column().classes("w-full")
            self._refresh_file_list()

    def _create_analysis_results_section(self) -> None:
        """Create analysis results section."""
        with ui.card().classes("w-full p-6 shadow-lg min-h-96"):
            ui.label("📊 Analysis Results").classes("text-xl font-bold mb-4")

            self.results_container = ui.column().classes("w-full")

            # Initial message
            with self.results_container:
                ui.label("Select a file from the list to view analysis results").classes(
                    "text-gray-500 italic text-center mt-8"
                )

    async def _handle_upload(self, upload_event: UploadEventArguments) -> None:
        """Handle file upload."""
        try:
            ui.notify(f"Uploading {upload_event.name}...", type="info")

            # Save file
            uploaded_file = self.file_service.handle_file_upload(upload_event)

            if uploaded_file is None:
                ui.notify(f"Failed to upload {upload_event.name}", type="negative")
                return

            ui.notify(f"File uploaded successfully: {upload_event.name}", type="positive")

            # Start analysis in background
            if uploaded_file is not None and uploaded_file.id is not None:
                asyncio.create_task(self._analyze_file_async(uploaded_file.id))

            # Refresh UI
            self._refresh_file_list()
            self._update_upload_stats()

        except Exception as e:
            logger.exception(f"Upload error for file {upload_event.name}")
            ui.notify(f"Upload error: {str(e)}", type="negative")

    async def _analyze_file_async(self, file_id: int) -> None:
        """Analyze file asynchronously."""
        try:
            ui.notify("Starting analysis...", type="info")

            # Run analysis in thread to avoid blocking UI
            result = await asyncio.get_event_loop().run_in_executor(None, self.analysis_service.analyze_file, file_id)

            if result is not None:
                ui.notify("Analysis completed successfully!", type="positive")
                # Refresh file list to show updated status
                self._refresh_file_list()

                # If this is the currently selected file, refresh results
                if self.current_file_id == file_id:
                    self._show_analysis_results(file_id)
            else:
                ui.notify("Analysis failed", type="negative")

        except Exception as e:
            logger.exception(f"Analysis error for file {file_id}")
            ui.notify(f"Analysis error: {str(e)}", type="negative")

    def _refresh_file_list(self) -> None:
        """Refresh the file list display."""
        if self.file_list_container is None:
            return

        self.file_list_container.clear()

        with self.file_list_container:
            files = self.file_service.get_all_uploaded_files()

            if not files:
                ui.label("No files uploaded yet").classes("text-gray-500 italic text-center py-4")
                return

            for file in files[:10]:  # Show last 10 files
                self._create_file_item(file)

    def _create_file_item(self, file: UploadedFile) -> None:
        """Create a file list item."""
        # Status color mapping
        status_colors = {
            ProcessingStatus.PENDING: "orange",
            ProcessingStatus.PROCESSING: "blue",
            ProcessingStatus.COMPLETED: "green",
            ProcessingStatus.FAILED: "red",
        }

        # Status icons
        status_icons = {
            ProcessingStatus.PENDING: "⏳",
            ProcessingStatus.PROCESSING: "⚙️",
            ProcessingStatus.COMPLETED: "✅",
            ProcessingStatus.FAILED: "❌",
        }

        with (
            ui.card()
            .classes("w-full p-3 mb-2 cursor-pointer hover:shadow-md transition-shadow")
            .on("click", lambda event, f_id=file.id: self._select_file(f_id) if f_id is not None else None)
        ):
            with ui.row().classes("w-full items-center gap-3"):
                # File type icon
                file_icon = "🖼️" if file.file_type == FileType.IMAGE else "🎥"
                ui.label(file_icon).classes("text-2xl")

                # File info
                with ui.column().classes("flex-1"):
                    ui.label(file.original_filename).classes("font-semibold text-sm")

                    info_parts = [f"{file.file_format.value.upper()}", f"{file.file_size / (1024 * 1024):.1f}MB"]

                    if file.width and file.height:
                        info_parts.append(f"{file.width}×{file.height}")
                    if file.duration:
                        info_parts.append(f"{float(file.duration):.1f}s")

                    ui.label(" • ".join(info_parts)).classes("text-xs text-gray-600")

                # Status
                status_color = status_colors[file.processing_status]
                status_icon = status_icons[file.processing_status]

                with ui.row().classes("items-center gap-1"):
                    ui.label(status_icon)
                    ui.label(file.processing_status.value.title()).classes(
                        f"text-{status_color}-600 text-xs font-medium"
                    )

    def _select_file(self, file_id: int) -> None:
        """Select a file and show its analysis results."""
        self.current_file_id = file_id
        self._show_analysis_results(file_id)

    def _show_analysis_results(self, file_id: int) -> None:
        """Show analysis results for selected file."""
        self.results_container.clear()

        with self.results_container:
            file = self.file_service.get_uploaded_file(file_id)
            if file is None:
                ui.label("File not found").classes("text-red-500")
                return

            # File header
            with ui.row().classes("w-full items-center mb-4"):
                file_icon = "🖼️" if file.file_type == FileType.IMAGE else "🎥"
                ui.label(file_icon).classes("text-3xl mr-2")

                with ui.column():
                    ui.label(file.original_filename).classes("text-xl font-bold")
                    ui.label(f"Uploaded: {file.uploaded_at.strftime('%Y-%m-%d %H:%M')}").classes(
                        "text-sm text-gray-600"
                    )

            # Processing status
            match file.processing_status:
                case ProcessingStatus.PENDING:
                    ui.label("⏳ Analysis pending...").classes("text-orange-600 font-medium")
                    return
                case ProcessingStatus.PROCESSING:
                    ui.label("⚙️ Analysis in progress...").classes("text-blue-600 font-medium")
                    return
                case ProcessingStatus.FAILED:
                    ui.label("❌ Analysis failed").classes("text-red-600 font-medium")
                    if file.error_message:
                        ui.label(f"Error: {file.error_message}").classes("text-red-500 text-sm mt-2")
                    return

            # Show analysis results
            self._display_analysis_results(file)

    def _display_analysis_results(self, file: UploadedFile) -> None:
        """Display detailed analysis results."""
        with get_session() as session:
            # Get analysis results
            from sqlmodel import select

            analysis_results = list(session.exec(select(AnalysisResult).where(AnalysisResult.file_id == file.id)).all())

            if not analysis_results:
                ui.label("No analysis results available").classes("text-gray-500 italic")
                return

            result = analysis_results[0]  # Get latest result

            # Use results display service for summary
            self.results_display.create_summary_cards(result)

            # Video-specific results
            if file.file_type == FileType.VIDEO:
                self._display_video_analysis_results(result)

    def _display_video_analysis_results(self, result) -> None:
        """Display video-specific analysis results including CASA metrics."""
        with get_session() as session:
            # Get tracks and CASA metrics
            from sqlmodel import select
            from app.models import SpermTrack

            tracks_with_metrics = list(
                session.exec(select(SpermTrack).where(SpermTrack.analysis_result_id == result.id)).all()
            )

            if not tracks_with_metrics:
                ui.label("No tracking data available").classes("text-gray-500 italic")
                return

            # Use results display service for comprehensive video analysis display
            self.results_display.create_casa_metrics_table(tracks_with_metrics)
            self.results_display.create_motility_classification(tracks_with_metrics)
            self.results_display.create_quality_indicators(tracks_with_metrics)

    def _update_upload_stats(self) -> None:
        """Update upload statistics display."""
        if self.stats_container is None:
            return

        self.stats_container.clear()

        with self.stats_container:
            stats = self.file_service.get_file_statistics()

            # Create stat cards
            stat_items = [
                ("📁", stats["total_files"], "Total Files"),
                ("🖼️", stats["total_images"], "Images"),
                ("🎥", stats["total_videos"], "Videos"),
                ("✅", stats["completed_files"], "Completed"),
            ]

            for icon, value, label in stat_items:
                with ui.card().classes("p-3 text-center min-w-20"):
                    ui.label(icon).classes("text-xl")
                    ui.label(str(value)).classes("text-lg font-bold text-primary")
                    ui.label(label).classes("text-xs text-gray-600")


def create():
    """Create and register dashboard pages."""
    dashboard = SpermAnalysisDashboard()

    @ui.page("/")
    def index():
        dashboard.create_main_layout()

    @ui.page("/dashboard")
    def dashboard_page():
        dashboard.create_main_layout()
