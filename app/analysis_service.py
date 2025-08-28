"""
Core analysis service for sperm detection and tracking.
Handles YOLOv8 detection and DeepSORT tracking with CASA metrics calculation.
"""

import time
from pathlib import Path
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from PIL import Image
import numpy as np

from app.models import (
    UploadedFile,
    AnalysisResult,
    SpermDetection,
    SpermTrack,
    CASAMetrics,
    AnalysisResultCreate,
    SpermDetectionCreate,
    SpermTrackCreate,
    ProcessingStatus,
    FileType,
)
from app.database import get_session

logger = logging.getLogger(__name__)


class SpermAnalysisService:
    """Service for analyzing sperm in images and videos."""

    def __init__(self, confidence_threshold: float = 0.5, pixel_to_micron_ratio: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.pixel_to_micron_ratio = pixel_to_micron_ratio
        self.model_version = "YOLOv8n-mock"

        # Initialize mock detection patterns
        self._mock_detections = True

    def analyze_file(self, file_id: int) -> Optional[AnalysisResult]:
        """Analyze uploaded file and return results."""
        with get_session() as session:
            file = session.get(UploadedFile, file_id)
            if file is None:
                logger.error(f"File with ID {file_id} not found")
                return None

            # Update status to processing
            file.processing_status = ProcessingStatus.PROCESSING
            session.add(file)
            session.commit()

            try:
                start_time = time.time()

                if file.file_type == FileType.IMAGE:
                    result = self._analyze_image(file)
                elif file.file_type == FileType.VIDEO:
                    result = self._analyze_video(file)
                else:
                    raise ValueError(f"Unsupported file type: {file.file_type}")

                processing_time = time.time() - start_time

                # Create analysis result
                analysis_data = AnalysisResultCreate(
                    file_id=file_id,
                    total_sperm_count=result["total_count"],
                    processing_time=Decimal(str(processing_time)),
                    model_version=self.model_version,
                    confidence_threshold=Decimal(str(self.confidence_threshold)),
                    analysis_metadata=result.get("metadata", {}),
                )

                analysis_result = AnalysisResult.model_validate(analysis_data)
                session.add(analysis_result)
                session.flush()

                # Store detections
                for detection_data in result["detections"]:
                    detection_data["analysis_result_id"] = analysis_result.id
                    detection = SpermDetection.model_validate(SpermDetectionCreate(**detection_data))
                    session.add(detection)

                # Store tracks and CASA metrics for videos
                if "tracks" in result:
                    for track_data in result["tracks"]:
                        track_data["analysis_result_id"] = analysis_result.id
                        track = SpermTrack.model_validate(SpermTrackCreate(**track_data))
                        session.add(track)
                        session.flush()

                        # Calculate and store CASA metrics
                        casa_metrics = self._calculate_casa_metrics(track, file.fps or Decimal("30"))
                        if casa_metrics and track.id is not None:
                            casa_metrics.sperm_track_id = track.id
                            session.add(casa_metrics)

                # Update file status
                file.processing_status = ProcessingStatus.COMPLETED
                file.processed_at = datetime.utcnow()
                session.add(file)

                session.commit()
                session.refresh(analysis_result)
                return analysis_result

            except Exception as e:
                logger.exception(f"Error analyzing file {file_id}")
                file.processing_status = ProcessingStatus.FAILED
                file.error_message = str(e)
                session.add(file)
                session.commit()
                return None

    def _analyze_image(self, file: UploadedFile) -> Dict[str, Any]:
        """Analyze static image for sperm detection."""
        file_path = Path(file.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file.file_path}")

        # Load and analyze image
        image = Image.open(file.file_path)
        width, height = image.size

        # Mock detection for demonstration
        detections = self._mock_detect_sperm_in_image(width, height)

        return {
            "total_count": len(detections),
            "detections": detections,
            "metadata": {"image_width": width, "image_height": height, "detection_method": "YOLOv8_mock"},
        }

    def _analyze_video(self, file: UploadedFile) -> Dict[str, Any]:
        """Analyze video for sperm detection and tracking."""
        file_path = Path(file.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file.file_path}")

        # Mock video analysis
        total_frames = int((file.duration or Decimal("5")) * (file.fps or Decimal("30")))
        detections, tracks = self._mock_detect_and_track_sperm_in_video(
            file.width or 640, file.height or 480, total_frames, file.fps or Decimal("30")
        )

        return {
            "total_count": len(set(track["track_id"] for track in tracks)),
            "detections": detections,
            "tracks": tracks,
            "metadata": {
                "video_width": file.width,
                "video_height": file.height,
                "total_frames": total_frames,
                "fps": float(file.fps or 30),
                "tracking_method": "DeepSORT_mock",
            },
        }

    def _mock_detect_sperm_in_image(self, width: int, height: int) -> List[Dict[str, Any]]:
        """Mock sperm detection in image."""
        np.random.seed(42)  # For consistent results
        num_sperm = np.random.randint(10, 50)

        detections = []
        for i in range(num_sperm):
            x = np.random.uniform(0, width - 50)
            y = np.random.uniform(0, height - 30)
            w = np.random.uniform(20, 50)
            h = np.random.uniform(15, 30)
            confidence = np.random.uniform(0.6, 0.95)

            detections.append(
                {
                    "frame_number": None,
                    "bbox_x": Decimal(str(x)),
                    "bbox_y": Decimal(str(y)),
                    "bbox_width": Decimal(str(w)),
                    "bbox_height": Decimal(str(h)),
                    "confidence": Decimal(str(confidence)),
                    "detection_timestamp": None,
                }
            )

        return detections

    def _mock_detect_and_track_sperm_in_video(
        self, width: int, height: int, total_frames: int, fps: Decimal
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Mock sperm detection and tracking in video."""
        np.random.seed(42)
        num_tracks = np.random.randint(5, 20)

        detections = []
        tracks = []

        for track_id in range(num_tracks):
            # Generate random track duration
            track_length = np.random.randint(30, min(150, total_frames))
            start_frame = np.random.randint(0, max(1, total_frames - track_length))
            end_frame = start_frame + track_length

            # Generate trajectory
            trajectory = []
            start_x = np.random.uniform(50, width - 50)
            start_y = np.random.uniform(50, height - 50)

            for frame in range(start_frame, end_frame):
                # Simulate sperm movement
                progress = (frame - start_frame) / track_length

                # Add some randomness to movement
                noise_x = np.random.normal(0, 5)
                noise_y = np.random.normal(0, 5)

                # Simulate curved path
                x = start_x + progress * np.random.uniform(-100, 100) + noise_x
                y = start_y + progress * np.random.uniform(-50, 50) + noise_y

                # Keep within bounds
                x = max(10, min(width - 10, x))
                y = max(10, min(height - 10, y))

                timestamp = frame / float(fps)

                trajectory.append({"frame": frame, "x": float(x), "y": float(y), "timestamp": timestamp})

                # Add detection for this frame
                detections.append(
                    {
                        "frame_number": frame,
                        "bbox_x": Decimal(str(x - 10)),
                        "bbox_y": Decimal(str(y - 8)),
                        "bbox_width": Decimal(str(20 + np.random.uniform(-3, 3))),
                        "bbox_height": Decimal(str(16 + np.random.uniform(-2, 2))),
                        "confidence": Decimal(str(np.random.uniform(0.6, 0.95))),
                        "detection_timestamp": Decimal(str(timestamp)),
                    }
                )

            tracks.append(
                {
                    "track_id": track_id,
                    "start_frame": start_frame,
                    "end_frame": end_frame - 1,
                    "start_time": Decimal(str(start_frame / float(fps))),
                    "end_time": Decimal(str((end_frame - 1) / float(fps))),
                    "total_frames": track_length,
                    "trajectory": trajectory,
                }
            )

        return detections, tracks

    def _calculate_casa_metrics(self, track: SpermTrack, fps: Decimal) -> Optional[CASAMetrics]:
        """Calculate CASA metrics for a sperm track."""
        if len(track.trajectory) < 3:
            return None

        try:
            # Extract coordinates and timestamps
            points = [(point["x"], point["y"], point["timestamp"]) for point in track.trajectory]

            # Calculate distances and velocities
            total_distance = Decimal("0")
            velocities = []

            for i in range(1, len(points)):
                x1, y1, t1 = points[i - 1]
                x2, y2, t2 = points[i]

                # Distance between consecutive points
                segment_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 * self.pixel_to_micron_ratio
                total_distance += Decimal(str(segment_distance))

                # Instantaneous velocity
                time_diff = t2 - t1
                if time_diff > 0:
                    velocity = segment_distance / time_diff
                    velocities.append(velocity)

            # Net displacement (straight-line distance)
            start_x, start_y = points[0][:2]
            end_x, end_y = points[-1][:2]
            net_distance = Decimal(
                str(((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5 * self.pixel_to_micron_ratio)
            )

            # Time duration
            total_time = points[-1][2] - points[0][2]

            # CASA metrics calculation
            vcl = total_distance / Decimal(str(total_time)) if total_time > 0 else Decimal("0")
            vsl = net_distance / Decimal(str(total_time)) if total_time > 0 else Decimal("0")
            vap = (
                sum(Decimal(str(v)) for v in velocities[: len(velocities) // 2])
                / Decimal(str(max(1, len(velocities) // 2)))
                if velocities
                else Decimal("0")
            )

            # Ratios (percentages)
            lin = (vsl / vcl * 100) if vcl > 0 else Decimal("0")
            str_value = (vsl / vap * 100) if vap > 0 else Decimal("0")
            wob = (vap / vcl * 100) if vcl > 0 else Decimal("0")

            # Mock additional metrics
            alh = Decimal(str(np.random.uniform(1.5, 4.5)))  # Mock amplitude
            bcf = Decimal(str(np.random.uniform(8, 25)))  # Mock beat frequency

            # Quality metrics
            path_smoothness = Decimal("0.8") - (Decimal(str(len(points))) / Decimal("1000"))
            path_smoothness = max(Decimal("0.1"), min(Decimal("1.0"), path_smoothness))
            tracking_quality = Decimal("0.9") if len(points) > 10 else Decimal("0.7")

            return CASAMetrics(
                sperm_track_id=0,  # Will be set by caller
                vcl=vcl,
                vsl=vsl,
                vap=vap,
                lin=min(Decimal("100"), lin),
                str_value=min(Decimal("100"), str_value),
                wob=min(Decimal("100"), wob),
                alh=alh,
                bcf=bcf,
                total_distance=total_distance,
                net_distance=net_distance,
                path_smoothness=path_smoothness,
                tracking_quality=tracking_quality,
                pixel_to_micron_ratio=Decimal(str(self.pixel_to_micron_ratio)),
                frame_rate=fps,
            )

        except Exception:
            logger.exception(f"Error calculating CASA metrics for track {track.id}")
            return None


def get_analysis_service() -> SpermAnalysisService:
    """Get configured analysis service instance."""
    return SpermAnalysisService(
        confidence_threshold=0.5,
        pixel_to_micron_ratio=0.5,  # This should be configured based on microscopy settings
    )
