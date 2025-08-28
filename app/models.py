from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class FileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class FileFormat(str, Enum):
    JPG = "jpg"
    PNG = "png"
    MP4 = "mp4"
    AVI = "avi"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Persistent models (stored in database)
class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_type: FileType
    file_format: FileFormat
    file_size: int = Field(ge=0)  # Size in bytes
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)
    duration: Optional[Decimal] = Field(default=None, ge=0)  # Video duration in seconds
    fps: Optional[Decimal] = Field(default=None, ge=0)  # Frames per second for videos
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)

    # Relationships
    analysis_results: List["AnalysisResult"] = Relationship(back_populates="file")


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(foreign_key="uploaded_files.id")
    total_sperm_count: int = Field(ge=0)
    processing_time: Decimal = Field(ge=0)  # Processing time in seconds
    model_version: str = Field(max_length=50)  # YOLOv8 model version used
    confidence_threshold: Decimal = Field(ge=0, le=1)
    analysis_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional analysis metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    file: UploadedFile = Relationship(back_populates="analysis_results")
    sperm_detections: List["SpermDetection"] = Relationship(back_populates="analysis_result")
    sperm_tracks: List["SpermTrack"] = Relationship(back_populates="analysis_result")


class SpermDetection(SQLModel, table=True):
    __tablename__ = "sperm_detections"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_result_id: int = Field(foreign_key="analysis_results.id")
    frame_number: Optional[int] = Field(default=None, ge=0)  # Null for static images
    bbox_x: Decimal = Field(ge=0)  # Bounding box coordinates
    bbox_y: Decimal = Field(ge=0)
    bbox_width: Decimal = Field(gt=0)
    bbox_height: Decimal = Field(gt=0)
    confidence: Decimal = Field(ge=0, le=1)
    detection_timestamp: Optional[Decimal] = Field(default=None, ge=0)  # Time in video (seconds)

    # Relationships
    analysis_result: AnalysisResult = Relationship(back_populates="sperm_detections")


class SpermTrack(SQLModel, table=True):
    __tablename__ = "sperm_tracks"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_result_id: int = Field(foreign_key="analysis_results.id")
    track_id: int = Field(ge=0)  # DeepSORT track ID
    start_frame: int = Field(ge=0)
    end_frame: int = Field(ge=0)
    start_time: Decimal = Field(ge=0)  # Start time in video (seconds)
    end_time: Decimal = Field(ge=0)  # End time in video (seconds)
    total_frames: int = Field(gt=0)
    trajectory: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))  # List of {frame, x, y, timestamp}

    # Relationships
    analysis_result: AnalysisResult = Relationship(back_populates="sperm_tracks")
    casa_metrics: Optional["CASAMetrics"] = Relationship(back_populates="sperm_track")


class CASAMetrics(SQLModel, table=True):
    __tablename__ = "casa_metrics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    sperm_track_id: int = Field(foreign_key="sperm_tracks.id", unique=True)

    # Core CASA parameters
    vcl: Decimal = Field(ge=0)  # Curvilinear velocity (μm/s)
    vsl: Decimal = Field(ge=0)  # Straight-line velocity (μm/s)
    vap: Decimal = Field(ge=0)  # Average path velocity (μm/s)
    lin: Decimal = Field(ge=0, le=100)  # Linearity (VSL/VCL * 100)
    str_value: Decimal = Field(ge=0, le=100)  # Straightness (VSL/VAP * 100)
    wob: Decimal = Field(ge=0, le=100)  # Wobble (VAP/VCL * 100)

    # Additional motion characteristics
    alh: Decimal = Field(ge=0)  # Amplitude of lateral head displacement (μm)
    bcf: Decimal = Field(ge=0)  # Beat cross frequency (Hz)

    # Path measurements
    total_distance: Decimal = Field(ge=0)  # Total path length (μm)
    net_distance: Decimal = Field(ge=0)  # Net displacement (μm)

    # Quality metrics
    path_smoothness: Decimal = Field(ge=0, le=1)  # Path quality indicator
    tracking_quality: Decimal = Field(ge=0, le=1)  # Tracking confidence

    # Calculation metadata
    pixel_to_micron_ratio: Decimal = Field(gt=0)  # Conversion factor
    frame_rate: Decimal = Field(gt=0)  # Video frame rate used
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sperm_track: SpermTrack = Relationship(back_populates="casa_metrics")


# Non-persistent schemas (for validation, forms, API requests/responses)
class FileUploadCreate(SQLModel, table=False):
    filename: str = Field(max_length=255)
    file_type: FileType
    file_format: FileFormat
    file_size: int = Field(ge=0)
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)
    duration: Optional[Decimal] = Field(default=None, ge=0)
    fps: Optional[Decimal] = Field(default=None, ge=0)


class AnalysisResultCreate(SQLModel, table=False):
    file_id: int
    total_sperm_count: int = Field(ge=0)
    processing_time: Decimal = Field(ge=0)
    model_version: str = Field(max_length=50)
    confidence_threshold: Decimal = Field(ge=0, le=1)
    analysis_metadata: Dict[str, Any] = Field(default={})


class SpermDetectionCreate(SQLModel, table=False):
    analysis_result_id: int
    frame_number: Optional[int] = Field(default=None, ge=0)
    bbox_x: Decimal = Field(ge=0)
    bbox_y: Decimal = Field(ge=0)
    bbox_width: Decimal = Field(gt=0)
    bbox_height: Decimal = Field(gt=0)
    confidence: Decimal = Field(ge=0, le=1)
    detection_timestamp: Optional[Decimal] = Field(default=None, ge=0)


class SpermTrackCreate(SQLModel, table=False):
    analysis_result_id: int
    track_id: int = Field(ge=0)
    start_frame: int = Field(ge=0)
    end_frame: int = Field(ge=0)
    start_time: Decimal = Field(ge=0)
    end_time: Decimal = Field(ge=0)
    trajectory: List[Dict[str, Any]] = Field(default=[])


class CASAMetricsCreate(SQLModel, table=False):
    sperm_track_id: int
    vcl: Decimal = Field(ge=0)
    vsl: Decimal = Field(ge=0)
    vap: Decimal = Field(ge=0)
    lin: Decimal = Field(ge=0, le=100)
    str_value: Decimal = Field(ge=0, le=100)
    wob: Decimal = Field(ge=0, le=100)
    alh: Decimal = Field(ge=0)
    bcf: Decimal = Field(ge=0)
    total_distance: Decimal = Field(ge=0)
    net_distance: Decimal = Field(ge=0)
    path_smoothness: Decimal = Field(ge=0, le=1)
    tracking_quality: Decimal = Field(ge=0, le=1)
    pixel_to_micron_ratio: Decimal = Field(gt=0)
    frame_rate: Decimal = Field(gt=0)


# Response schemas for API
class FileUploadResponse(SQLModel, table=False):
    id: int
    filename: str
    file_type: FileType
    file_format: FileFormat
    file_size: int
    processing_status: ProcessingStatus
    uploaded_at: str  # ISO format datetime string
    total_sperm_count: Optional[int] = Field(default=None)


class AnalysisResultResponse(SQLModel, table=False):
    id: int
    file_id: int
    total_sperm_count: int
    processing_time: Decimal
    model_version: str
    confidence_threshold: Decimal
    created_at: str  # ISO format datetime string
    sperm_detections_count: int = Field(default=0)
    sperm_tracks_count: int = Field(default=0)


class CASAMetricsResponse(SQLModel, table=False):
    track_id: int
    vcl: Decimal
    vsl: Decimal
    vap: Decimal
    lin: Decimal
    str_value: Decimal
    wob: Decimal
    alh: Decimal
    bcf: Decimal
    total_distance: Decimal
    net_distance: Decimal
    path_smoothness: Decimal
    tracking_quality: Decimal


class ProcessingStatusUpdate(SQLModel, table=False):
    processing_status: ProcessingStatus
    error_message: Optional[str] = Field(default=None, max_length=1000)
    processed_at: Optional[datetime] = Field(default=None)
