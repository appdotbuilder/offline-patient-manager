from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for role-based access control
class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class ExamStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    created_patients: List["Patient"] = Relationship(back_populates="created_by_user")
    created_exams: List["Exam"] = Relationship(back_populates="created_by_user")
    analyzed_videos: List["VideoAnalysis"] = Relationship(back_populates="analyzed_by_user")


class Patient(SQLModel, table=True):
    __tablename__ = "patients"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(unique=True, max_length=50)  # External patient identifier
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: datetime
    gender: Gender
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    medical_history: Optional[str] = Field(default=None, max_length=2000)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    # Relationships
    created_by_user: User = Relationship(back_populates="created_patients")
    exams: List["Exam"] = Relationship(back_populates="patient")


class Exam(SQLModel, table=True):
    __tablename__ = "exams"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_number: str = Field(unique=True, max_length=50)
    patient_id: int = Field(foreign_key="patients.id")
    exam_type: str = Field(max_length=100)  # Type of examination
    status: ExamStatus = Field(default=ExamStatus.PENDING)
    notes: Optional[str] = Field(default=None, max_length=2000)
    scheduled_date: Optional[datetime] = Field(default=None)
    completed_date: Optional[datetime] = Field(default=None)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Clinical parameters
    temperature: Optional[Decimal] = Field(default=None, decimal_places=1)
    duration_minutes: Optional[int] = Field(default=None)
    sample_volume_ml: Optional[Decimal] = Field(default=None, decimal_places=2)

    # Relationships
    patient: Patient = Relationship(back_populates="exams")
    created_by_user: User = Relationship(back_populates="created_exams")
    video_analyses: List["VideoAnalysis"] = Relationship(back_populates="exam")
    reports: List["Report"] = Relationship(back_populates="exam")


class VideoAnalysis(SQLModel, table=True):
    __tablename__ = "video_analyses"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id")
    video_filename: str = Field(max_length=255)
    video_path: str = Field(max_length=500)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    analyzed_by: int = Field(foreign_key="users.id")

    # CASA-like metrics for sperm analysis
    total_sperm_count: Optional[int] = Field(default=None)
    concentration_millions_per_ml: Optional[Decimal] = Field(default=None, decimal_places=2)
    motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    progressive_motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    non_progressive_motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    immotile_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Velocity measurements (micrometers per second)
    vcl_average: Optional[Decimal] = Field(default=None, decimal_places=2)  # Curvilinear velocity
    vsl_average: Optional[Decimal] = Field(default=None, decimal_places=2)  # Straight line velocity
    vap_average: Optional[Decimal] = Field(default=None, decimal_places=2)  # Average path velocity

    # Path characteristics
    linearity_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    straightness_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    wobble_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Head morphology
    normal_morphology_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    head_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    midpiece_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    tail_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Analysis settings and metadata
    frame_rate: Optional[Decimal] = Field(default=None, decimal_places=2)
    total_frames_analyzed: Optional[int] = Field(default=None)
    analysis_duration_seconds: Optional[Decimal] = Field(default=None, decimal_places=2)
    microscope_magnification: Optional[str] = Field(default=None, max_length=50)
    chamber_depth_microns: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Quality control
    analysis_quality_score: Optional[Decimal] = Field(default=None, decimal_places=2)
    tracking_efficiency_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # OpenCV processing metadata
    opencv_version: Optional[str] = Field(default=None, max_length=20)
    processing_parameters: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    raw_tracking_data: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    exam: Exam = Relationship(back_populates="video_analyses")
    analyzed_by_user: User = Relationship(back_populates="analyzed_videos")


class Report(SQLModel, table=True):
    __tablename__ = "reports"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id")
    report_type: str = Field(max_length=100, default="standard")
    title: str = Field(max_length=200)
    pdf_filename: str = Field(max_length=255)
    pdf_path: str = Field(max_length=500)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Report metadata
    template_used: Optional[str] = Field(default=None, max_length=100)
    include_charts: bool = Field(default=True)
    include_raw_data: bool = Field(default=False)

    # Report content structure
    summary: Optional[str] = Field(default=None, max_length=2000)
    conclusions: Optional[str] = Field(default=None, max_length=2000)
    recommendations: Optional[str] = Field(default=None, max_length=2000)

    # Quality assurance
    reviewed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    review_date: Optional[datetime] = Field(default=None)
    approval_status: str = Field(default="draft", max_length=20)  # draft, approved, rejected

    # Relationships
    exam: Exam = Relationship(back_populates="reports")


class SystemSettings(SQLModel, table=True):
    __tablename__ = "system_settings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    setting_key: str = Field(unique=True, max_length=100)
    setting_value: str = Field(max_length=1000)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)


class UserUpdate(SQLModel, table=False):
    email: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class UserLogin(SQLModel, table=False):
    username: str
    password: str


class PatientCreate(SQLModel, table=False):
    patient_id: str = Field(max_length=50)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: datetime
    gender: Gender
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    medical_history: Optional[str] = Field(default=None, max_length=2000)


class PatientUpdate(SQLModel, table=False):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    medical_history: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = Field(default=None)


class ExamCreate(SQLModel, table=False):
    exam_number: str = Field(max_length=50)
    patient_id: int
    exam_type: str = Field(max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)
    scheduled_date: Optional[datetime] = Field(default=None)
    temperature: Optional[Decimal] = Field(default=None, decimal_places=1)
    duration_minutes: Optional[int] = Field(default=None)
    sample_volume_ml: Optional[Decimal] = Field(default=None, decimal_places=2)


class ExamUpdate(SQLModel, table=False):
    status: Optional[ExamStatus] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=2000)
    scheduled_date: Optional[datetime] = Field(default=None)
    completed_date: Optional[datetime] = Field(default=None)
    temperature: Optional[Decimal] = Field(default=None, decimal_places=1)
    duration_minutes: Optional[int] = Field(default=None)
    sample_volume_ml: Optional[Decimal] = Field(default=None, decimal_places=2)


class VideoAnalysisCreate(SQLModel, table=False):
    exam_id: int
    video_filename: str = Field(max_length=255)
    video_path: str = Field(max_length=500)

    # CASA metrics
    total_sperm_count: Optional[int] = Field(default=None)
    concentration_millions_per_ml: Optional[Decimal] = Field(default=None, decimal_places=2)
    motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    progressive_motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    non_progressive_motility_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    immotile_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Velocity measurements
    vcl_average: Optional[Decimal] = Field(default=None, decimal_places=2)
    vsl_average: Optional[Decimal] = Field(default=None, decimal_places=2)
    vap_average: Optional[Decimal] = Field(default=None, decimal_places=2)

    # Path characteristics
    linearity_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    straightness_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    wobble_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Morphology
    normal_morphology_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    head_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    midpiece_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)
    tail_defects_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Analysis metadata
    frame_rate: Optional[Decimal] = Field(default=None, decimal_places=2)
    total_frames_analyzed: Optional[int] = Field(default=None)
    analysis_duration_seconds: Optional[Decimal] = Field(default=None, decimal_places=2)
    microscope_magnification: Optional[str] = Field(default=None, max_length=50)
    chamber_depth_microns: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Quality metrics
    analysis_quality_score: Optional[Decimal] = Field(default=None, decimal_places=2)
    tracking_efficiency_percentage: Optional[Decimal] = Field(default=None, decimal_places=1)

    # Processing parameters
    opencv_version: Optional[str] = Field(default=None, max_length=20)
    processing_parameters: Optional[Dict[str, Any]] = Field(default={})


class ReportCreate(SQLModel, table=False):
    exam_id: int
    report_type: str = Field(max_length=100, default="standard")
    title: str = Field(max_length=200)
    pdf_filename: str = Field(max_length=255)
    pdf_path: str = Field(max_length=500)
    template_used: Optional[str] = Field(default=None, max_length=100)
    include_charts: bool = Field(default=True)
    include_raw_data: bool = Field(default=False)
    summary: Optional[str] = Field(default=None, max_length=2000)
    conclusions: Optional[str] = Field(default=None, max_length=2000)
    recommendations: Optional[str] = Field(default=None, max_length=2000)


class ReportUpdate(SQLModel, table=False):
    summary: Optional[str] = Field(default=None, max_length=2000)
    conclusions: Optional[str] = Field(default=None, max_length=2000)
    recommendations: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[int] = Field(default=None)
    approval_status: Optional[str] = Field(default=None, max_length=20)


class SystemSettingCreate(SQLModel, table=False):
    setting_key: str = Field(max_length=100)
    setting_value: str = Field(max_length=1000)
    description: Optional[str] = Field(default=None, max_length=500)


class SystemSettingUpdate(SQLModel, table=False):
    setting_value: str = Field(max_length=1000)
    description: Optional[str] = Field(default=None, max_length=500)
