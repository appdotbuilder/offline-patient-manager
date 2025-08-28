"""
Core integration tests for sperm analysis application.
"""

import pytest
from app.database import reset_db
from app.file_service import get_file_service
from app.analysis_service import get_analysis_service
from app.results_display import get_results_display_service


@pytest.fixture
def new_db():
    reset_db()
    yield
    reset_db()


class TestServiceIntegration:
    """Test core service integration without complex file operations."""

    def test_file_service_creation(self):
        """Test file service can be created."""
        service = get_file_service()
        assert service is not None
        assert service.upload_directory.exists()

    def test_analysis_service_creation(self):
        """Test analysis service can be created."""
        service = get_analysis_service()
        assert service is not None
        assert service.confidence_threshold == 0.5
        assert service.pixel_to_micron_ratio == 0.5

    def test_results_display_service_creation(self):
        """Test results display service can be created."""
        service = get_results_display_service()
        assert service is not None

    def test_file_service_supported_formats(self):
        """Test file service has correct supported formats."""
        service = get_file_service()

        assert ".jpg" in service.SUPPORTED_IMAGE_FORMATS
        assert ".jpeg" in service.SUPPORTED_IMAGE_FORMATS
        assert ".png" in service.SUPPORTED_IMAGE_FORMATS
        assert ".mp4" in service.SUPPORTED_VIDEO_FORMATS
        assert ".avi" in service.SUPPORTED_VIDEO_FORMATS

    def test_file_service_size_limits(self):
        """Test file service has reasonable size limits."""
        service = get_file_service()

        assert service.MAX_IMAGE_SIZE == 50 * 1024 * 1024  # 50MB
        assert service.MAX_VIDEO_SIZE == 500 * 1024 * 1024  # 500MB

    def test_file_service_statistics_empty(self, new_db):
        """Test file statistics with empty database."""
        service = get_file_service()
        stats = service.get_file_statistics()

        assert stats["total_files"] == 0
        assert stats["total_images"] == 0
        assert stats["total_videos"] == 0
        assert stats["pending_files"] == 0
        assert stats["completed_files"] == 0
        assert stats["total_size_mb"] == 0.0

    def test_analysis_service_mock_detection(self):
        """Test analysis service mock detection functionality."""
        service = get_analysis_service()

        # Test image detection
        detections = service._mock_detect_sperm_in_image(800, 600)
        assert 10 <= len(detections) <= 50

        for detection in detections:
            assert detection["frame_number"] is None
            assert detection["bbox_x"] >= 0
            assert detection["bbox_y"] >= 0
            assert detection["bbox_width"] > 0
            assert detection["bbox_height"] > 0
            assert 0 < detection["confidence"] <= 1

    def test_analysis_service_mock_video_tracking(self):
        """Test analysis service mock video tracking."""
        from decimal import Decimal

        service = get_analysis_service()
        detections, tracks = service._mock_detect_and_track_sperm_in_video(640, 480, 100, Decimal("30"))

        assert len(detections) > 0
        assert 5 <= len(tracks) <= 20

        for track in tracks:
            assert track["track_id"] >= 0
            assert track["start_frame"] >= 0
            assert track["end_frame"] >= track["start_frame"]
            assert len(track["trajectory"]) > 0

    def test_database_operations_work(self, new_db):
        """Test basic database operations work."""
        from app.models import FileType, FileFormat, ProcessingStatus, UploadedFile
        from app.database import get_session

        with get_session() as session:
            # Create test file record
            file = UploadedFile(
                filename="test.jpg",
                original_filename="test.jpg",
                file_path="/fake/path.jpg",
                file_type=FileType.IMAGE,
                file_format=FileFormat.JPG,
                file_size=1024,
                processing_status=ProcessingStatus.PENDING,
            )

            session.add(file)
            session.commit()
            session.refresh(file)

            assert file.id is not None
            assert file.filename == "test.jpg"

            # Retrieve file
            retrieved = session.get(UploadedFile, file.id)
            assert retrieved is not None
            assert retrieved.filename == "test.jpg"
