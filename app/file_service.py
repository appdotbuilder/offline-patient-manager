"""
File upload and management service for sperm analysis application.
"""

from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from PIL import Image
from nicegui import events

from app.models import UploadedFile, FileType, FileFormat, ProcessingStatus, FileUploadCreate
from app.database import get_session

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and management."""

    # Supported file extensions
    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png"}
    SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi"}

    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

    def __init__(self, upload_directory: str = "uploads"):
        self.upload_directory = Path(upload_directory)
        self.upload_directory.mkdir(exist_ok=True)

        # Create subdirectories
        (self.upload_directory / "images").mkdir(exist_ok=True)
        (self.upload_directory / "videos").mkdir(exist_ok=True)

    def handle_file_upload(self, upload_event: events.UploadEventArguments) -> Optional[UploadedFile]:
        """Handle file upload from NiceGUI upload component."""
        try:
            # Validate file
            validation_result = self._validate_file(upload_event)
            if validation_result is not None:
                logger.warning(f"File validation failed: {validation_result}")
                return None

            # Determine file type and format
            file_type, file_format = self._determine_file_type_and_format(upload_event.name)
            if file_type is None or file_format is None:
                logger.error(f"Unsupported file type: {upload_event.name}")
                return None

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{upload_event.name}"

            # Determine subdirectory
            subdir = "images" if file_type == FileType.IMAGE else "videos"
            file_path = self.upload_directory / subdir / filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(upload_event.content.read())

            # Extract metadata
            width, height, duration, fps = self._extract_file_metadata(file_path, file_type)

            # Create database record
            # Get file size
            content_data = upload_event.content.read()
            upload_event.content.seek(0)  # Reset for saving

            file_data = FileUploadCreate(
                filename=filename,
                file_type=file_type,
                file_format=file_format,
                file_size=len(content_data),
                width=width,
                height=height,
                duration=Decimal(str(duration)) if duration is not None else None,
                fps=Decimal(str(fps)) if fps is not None else None,
            )

            with get_session() as session:
                uploaded_file = UploadedFile(
                    **file_data.model_dump(),
                    original_filename=upload_event.name,
                    file_path=str(file_path),
                    processing_status=ProcessingStatus.PENDING,
                )

                session.add(uploaded_file)
                session.commit()
                session.refresh(uploaded_file)

                logger.info(f"File uploaded successfully: {uploaded_file.id} - {upload_event.name}")
                return uploaded_file

        except Exception:
            logger.exception(f"Error uploading file {upload_event.name}")
            return None

    def _validate_file(self, upload_event: events.UploadEventArguments) -> Optional[str]:
        """Validate uploaded file. Returns error message if invalid."""
        # Check file extension
        file_ext = Path(upload_event.name).suffix.lower()
        supported_formats = self.SUPPORTED_IMAGE_FORMATS | self.SUPPORTED_VIDEO_FORMATS

        if file_ext not in supported_formats:
            return f"Unsupported file format: {file_ext}. Supported formats: {', '.join(sorted(supported_formats))}"

        # Check file size
        content = upload_event.content.read()
        upload_event.content.seek(0)  # Reset stream position
        file_size = len(content)
        max_size = self.MAX_IMAGE_SIZE if file_ext in self.SUPPORTED_IMAGE_FORMATS else self.MAX_VIDEO_SIZE

        if file_size > max_size:
            return f"File too large: {file_size / (1024 * 1024):.1f}MB. Maximum allowed: {max_size / (1024 * 1024)}MB"

        if file_size == 0:
            return "Empty file"

        return None

    def _determine_file_type_and_format(self, filename: str) -> Tuple[Optional[FileType], Optional[FileFormat]]:
        """Determine file type and format from filename."""
        ext = Path(filename).suffix.lower()

        if ext in {".jpg", ".jpeg"}:
            return FileType.IMAGE, FileFormat.JPG
        elif ext == ".png":
            return FileType.IMAGE, FileFormat.PNG
        elif ext == ".mp4":
            return FileType.VIDEO, FileFormat.MP4
        elif ext == ".avi":
            return FileType.VIDEO, FileFormat.AVI

        return None, None

    def _extract_file_metadata(
        self, file_path: Path, file_type: FileType
    ) -> Tuple[Optional[int], Optional[int], Optional[float], Optional[float]]:
        """Extract metadata from uploaded file."""
        width, height, duration, fps = None, None, None, None

        try:
            if file_type == FileType.IMAGE:
                with Image.open(file_path) as img:
                    width, height = img.size
            else:
                # For video files, we'll use mock values since we don't have opencv
                # In a real implementation, you would use cv2.VideoCapture
                width, height = 640, 480
                duration = 10.0  # Mock duration
                fps = 30.0  # Mock FPS

        except Exception as e:
            logger.warning(f"Could not extract metadata from {file_path}: {e}")

        return width, height, duration, fps

    def get_uploaded_file(self, file_id: int) -> Optional[UploadedFile]:
        """Get uploaded file by ID."""
        with get_session() as session:
            return session.get(UploadedFile, file_id)

    def get_all_uploaded_files(self) -> List[UploadedFile]:
        """Get all uploaded files."""
        with get_session() as session:
            from sqlmodel import desc

            return list(session.query(UploadedFile).order_by(desc(UploadedFile.uploaded_at)).all())

    def delete_uploaded_file(self, file_id: int) -> bool:
        """Delete uploaded file and its associated data."""
        with get_session() as session:
            file = session.get(UploadedFile, file_id)
            if file is None:
                return False

            try:
                # Delete physical file
                file_path = Path(file.file_path)
                if file_path.exists():
                    file_path.unlink()

                # Delete database record (cascades to related data)
                session.delete(file)
                session.commit()

                logger.info(f"File deleted successfully: {file_id}")
                return True

            except Exception:
                logger.exception(f"Error deleting file {file_id}")
                session.rollback()
                return False

    def get_file_statistics(self) -> dict:
        """Get upload statistics."""
        with get_session() as session:
            files = session.query(UploadedFile).all()

            stats = {
                "total_files": len(files),
                "total_images": len([f for f in files if f.file_type == FileType.IMAGE]),
                "total_videos": len([f for f in files if f.file_type == FileType.VIDEO]),
                "pending_files": len([f for f in files if f.processing_status == ProcessingStatus.PENDING]),
                "processing_files": len([f for f in files if f.processing_status == ProcessingStatus.PROCESSING]),
                "completed_files": len([f for f in files if f.processing_status == ProcessingStatus.COMPLETED]),
                "failed_files": len([f for f in files if f.processing_status == ProcessingStatus.FAILED]),
                "total_size_mb": sum(f.file_size for f in files) / (1024 * 1024),
            }

            return stats


def get_file_service() -> FileUploadService:
    """Get configured file upload service instance."""
    return FileUploadService()
