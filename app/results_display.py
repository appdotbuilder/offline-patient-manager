"""
Results display components for sperm analysis application.
"""

from typing import List

from nicegui import ui
from app.models import AnalysisResult, SpermTrack


class ResultsDisplayService:
    """Service for displaying analysis results in various formats."""

    def create_summary_cards(self, result: AnalysisResult) -> None:
        """Create summary metric cards for analysis results."""
        with ui.row().classes("w-full gap-4 mb-6"):
            # Sperm count card
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label("🧬").classes("text-3xl mb-2")
                ui.label(str(result.total_sperm_count)).classes("text-2xl font-bold text-primary")
                ui.label("Total Sperm").classes("text-sm text-gray-600")

            # Processing time card
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label("⏱️").classes("text-3xl mb-2")
                ui.label(f"{float(result.processing_time):.2f}s").classes("text-2xl font-bold text-primary")
                ui.label("Processing Time").classes("text-sm text-gray-600")

            # Model version card
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label("🤖").classes("text-3xl mb-2")
                ui.label(result.model_version).classes("text-lg font-bold text-primary")
                ui.label("AI Model").classes("text-sm text-gray-600")

            # Confidence card
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label("🎯").classes("text-3xl mb-2")
                ui.label(f"{float(result.confidence_threshold) * 100:.0f}%").classes("text-2xl font-bold text-primary")
                ui.label("Confidence").classes("text-sm text-gray-600")

    def create_casa_metrics_table(self, tracks_with_metrics: List[SpermTrack]) -> None:
        """Create detailed CASA metrics table for video analysis."""
        if not tracks_with_metrics:
            ui.label("No tracking data available").classes("text-gray-500 italic")
            return

        ui.label("📈 CASA Metrics (Individual Sperm Tracks)").classes("text-lg font-bold mb-4")

        # Define table columns
        columns = [
            {"name": "track_id", "label": "Track ID", "field": "track_id", "align": "center"},
            {"name": "vcl", "label": "VCL (μm/s)", "field": "vcl", "align": "right"},
            {"name": "vsl", "label": "VSL (μm/s)", "field": "vsl", "align": "right"},
            {"name": "vap", "label": "VAP (μm/s)", "field": "vap", "align": "right"},
            {"name": "lin", "label": "LIN (%)", "field": "lin", "align": "right"},
            {"name": "str", "label": "STR (%)", "field": "str", "align": "right"},
            {"name": "wob", "label": "WOB (%)", "field": "wob", "align": "right"},
            {"name": "alh", "label": "ALH (μm)", "field": "alh", "align": "right"},
            {"name": "bcf", "label": "BCF (Hz)", "field": "bcf", "align": "right"},
        ]

        # Prepare table rows
        rows = []
        for track in tracks_with_metrics:
            if track.casa_metrics:
                metrics = track.casa_metrics
                rows.append(
                    {
                        "track_id": f"#{track.track_id}",
                        "vcl": f"{float(metrics.vcl):.1f}",
                        "vsl": f"{float(metrics.vsl):.1f}",
                        "vap": f"{float(metrics.vap):.1f}",
                        "lin": f"{float(metrics.lin):.1f}",
                        "str": f"{float(metrics.str_value):.1f}",
                        "wob": f"{float(metrics.wob):.1f}",
                        "alh": f"{float(metrics.alh):.2f}",
                        "bcf": f"{float(metrics.bcf):.1f}",
                    }
                )

        if rows:
            table = ui.table(columns=columns, rows=rows).classes("w-full")
            table.props("flat bordered")

            # Add summary statistics
            self._create_casa_summary_statistics(rows)

    def _create_casa_summary_statistics(self, rows: List[dict]) -> None:
        """Create summary statistics for CASA metrics."""
        if not rows:
            return

        ui.label("📊 Summary Statistics").classes("text-lg font-bold mt-6 mb-4")

        # Calculate averages
        avg_vcl = sum(float(row["vcl"]) for row in rows) / len(rows)
        avg_vsl = sum(float(row["vsl"]) for row in rows) / len(rows)
        avg_lin = sum(float(row["lin"]) for row in rows) / len(rows)
        avg_alh = sum(float(row["alh"]) for row in rows) / len(rows)
        avg_bcf = sum(float(row["bcf"]) for row in rows) / len(rows)

        with ui.row().classes("gap-4 flex-wrap"):
            # VCL statistics
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label(f"{avg_vcl:.1f}").classes("text-xl font-bold text-primary")
                ui.label("μm/s").classes("text-sm text-gray-500")
                ui.label("Avg VCL").classes("text-sm text-gray-600 font-medium")

            # VSL statistics
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label(f"{avg_vsl:.1f}").classes("text-xl font-bold text-primary")
                ui.label("μm/s").classes("text-sm text-gray-500")
                ui.label("Avg VSL").classes("text-sm text-gray-600 font-medium")

            # Linearity statistics
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label(f"{avg_lin:.1f}").classes("text-xl font-bold text-primary")
                ui.label("%").classes("text-sm text-gray-500")
                ui.label("Avg Linearity").classes("text-sm text-gray-600 font-medium")

            # ALH statistics
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label(f"{avg_alh:.2f}").classes("text-xl font-bold text-primary")
                ui.label("μm").classes("text-sm text-gray-500")
                ui.label("Avg ALH").classes("text-sm text-gray-600 font-medium")

            # BCF statistics
            with ui.card().classes("p-4 text-center min-w-32"):
                ui.label(f"{avg_bcf:.1f}").classes("text-xl font-bold text-primary")
                ui.label("Hz").classes("text-sm text-gray-500")
                ui.label("Avg BCF").classes("text-sm text-gray-600 font-medium")

    def create_motility_classification(self, tracks_with_metrics: List[SpermTrack]) -> None:
        """Create motility classification based on CASA parameters."""
        if not tracks_with_metrics:
            return

        ui.label("🏃 Motility Classification").classes("text-lg font-bold mt-6 mb-4")

        # Classify sperm based on standard CASA criteria
        progressive = 0
        non_progressive = 0
        immotile = 0

        for track in tracks_with_metrics:
            if track.casa_metrics:
                vsl = float(track.casa_metrics.vsl)
                vcl = float(track.casa_metrics.vcl)

                # Standard WHO criteria (simplified)
                if vsl > 25 and vcl > 5:
                    progressive += 1
                elif vcl > 5:
                    non_progressive += 1
                else:
                    immotile += 1

        total = progressive + non_progressive + immotile

        if total > 0:
            with ui.row().classes("gap-4"):
                # Progressive motility
                with ui.card().classes("p-4 text-center min-w-40"):
                    ui.label("🏃‍♂️").classes("text-2xl mb-2")
                    ui.label(str(progressive)).classes("text-xl font-bold text-green-600")
                    ui.label(f"({progressive / total * 100:.1f}%)").classes("text-sm text-gray-500")
                    ui.label("Progressive").classes("text-sm text-gray-600 font-medium")

                # Non-progressive motility
                with ui.card().classes("p-4 text-center min-w-40"):
                    ui.label("🔄").classes("text-2xl mb-2")
                    ui.label(str(non_progressive)).classes("text-xl font-bold text-yellow-600")
                    ui.label(f"({non_progressive / total * 100:.1f}%)").classes("text-sm text-gray-500")
                    ui.label("Non-Progressive").classes("text-sm text-gray-600 font-medium")

                # Immotile
                with ui.card().classes("p-4 text-center min-w-40"):
                    ui.label("⏸️").classes("text-2xl mb-2")
                    ui.label(str(immotile)).classes("text-xl font-bold text-red-600")
                    ui.label(f"({immotile / total * 100:.1f}%)").classes("text-sm text-gray-500")
                    ui.label("Immotile").classes("text-sm text-gray-600 font-medium")

    def create_quality_indicators(self, tracks_with_metrics: List[SpermTrack]) -> None:
        """Create analysis quality indicators."""
        if not tracks_with_metrics:
            return

        ui.label("🔍 Analysis Quality").classes("text-lg font-bold mt-6 mb-4")

        # Calculate quality metrics
        total_tracks = len(tracks_with_metrics)
        avg_tracking_quality = (
            sum(float(track.casa_metrics.tracking_quality) for track in tracks_with_metrics if track.casa_metrics)
            / total_tracks
            if total_tracks > 0
            else 0
        )

        avg_path_smoothness = (
            sum(float(track.casa_metrics.path_smoothness) for track in tracks_with_metrics if track.casa_metrics)
            / total_tracks
            if total_tracks > 0
            else 0
        )

        # Calculate average track length
        avg_track_length = (
            sum(track.total_frames for track in tracks_with_metrics) / total_tracks if total_tracks > 0 else 0
        )

        with ui.row().classes("gap-4"):
            # Tracking quality
            with ui.card().classes("p-4 text-center min-w-40"):
                quality_color = (
                    "green" if avg_tracking_quality > 0.8 else "yellow" if avg_tracking_quality > 0.6 else "red"
                )
                ui.label("🎯").classes("text-2xl mb-2")
                ui.label(f"{avg_tracking_quality * 100:.0f}%").classes(f"text-xl font-bold text-{quality_color}-600")
                ui.label("Tracking Quality").classes("text-sm text-gray-600 font-medium")

            # Path smoothness
            with ui.card().classes("p-4 text-center min-w-40"):
                smoothness_color = (
                    "green" if avg_path_smoothness > 0.7 else "yellow" if avg_path_smoothness > 0.5 else "red"
                )
                ui.label("📈").classes("text-2xl mb-2")
                ui.label(f"{avg_path_smoothness * 100:.0f}%").classes(f"text-xl font-bold text-{smoothness_color}-600")
                ui.label("Path Smoothness").classes("text-sm text-gray-600 font-medium")

            # Average track length
            with ui.card().classes("p-4 text-center min-w-40"):
                ui.label("📏").classes("text-2xl mb-2")
                ui.label(f"{avg_track_length:.0f}").classes("text-xl font-bold text-primary")
                ui.label("Avg Track Length").classes("text-sm text-gray-600 font-medium")
                ui.label("(frames)").classes("text-xs text-gray-500")


def get_results_display_service() -> ResultsDisplayService:
    """Get configured results display service instance."""
    return ResultsDisplayService()
