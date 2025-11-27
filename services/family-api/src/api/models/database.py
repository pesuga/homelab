"""
Database models and schemas for Family Assistant multimodal content.

SQLAlchemy models for:
- Enhanced conversation history with multimodal support
- Content processing results and metadata
- File storage and management
- Enhanced family member profiles
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    JSON, ForeignKey, Index, LargeBinary, BigInteger, TypeDecorator
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.types import TypeDecorator, TEXT
from pydantic.json import pydantic_encoder

from .multimodal import (
    ContentType, ProcessingStatus, MessageRole,
    MultimodalContent, ContentProcessingResult,
    FamilyMemberProfile
)

Base = declarative_base()


class ContentTypeEnum(TypeDecorator):
    """Custom type for ContentType enum."""
    impl = String(20)

    def process_bind_param(self, value, dialect):
        return value.value if isinstance(value, ContentType) else value

    def process_result_value(self, value, dialect):
        return ContentType(value) if value else None


class ProcessingStatusEnum(TypeDecorator):
    """Custom type for ProcessingStatus enum."""
    impl = String(20)

    def process_bind_param(self, value, dialect):
        return value.value if isinstance(value, ProcessingStatus) else value

    def process_result_value(self, value, dialect):
        return ProcessingStatus(value) if value else None


class MessageRoleEnum(TypeDecorator):
    """Custom type for MessageRole enum."""
    impl = String(20)

    def process_bind_param(self, value, dialect):
        return value.value if isinstance(value, MessageRole) else value

    def process_result_value(self, value, dialect):
        return MessageRole(value) if value else None


class PydanticJSON(TypeDecorator):
    """Custom type for storing Pydantic models as JSON."""
    impl = JSONB

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        # Handle Pydantic models
        if hasattr(value, 'dict'):
            return value.dict()
        return json.loads(json.dumps(value, default=pydantic_encoder))

    def process_result_value(self, value, dialect):
        return value


# Enhanced Family Member Model
class FamilyMember(Base):
    """Enhanced family member model with multimodal preferences."""
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    username = Column(String(100), nullable=True)

    # Basic profile
    name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False)  # parent, child, teenager, grandparent
    age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    # Multimodal preferences (JSON)
    preferred_content_types = Column(ARRAY(String), default=[])
    content_filters = Column(ARRAY(String), default=[])
    language_preferences = Column(ARRAY(String), default=['en'])

    # Vision preferences
    vision_analysis_enabled = Column(Boolean, default=True)
    photo_privacy_level = Column(String(20), default='family')  # private, family, public
    auto_image_description = Column(Boolean, default=True)

    # Audio preferences
    speech_recognition_enabled = Column(Boolean, default=True)
    preferred_audio_format = Column(String(10), default='ogg')
    voice_privacy_level = Column(String(20), default='family')

    # Document preferences
    document_extraction_enabled = Column(Boolean, default=True)
    auto_summarization = Column(Boolean, default=False)

    # Legacy compatibility
    permissions = Column(JSONB, default=dict)
    preferences = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="family_member")
    content_uploads = relationship("ContentUpload", back_populates="uploaded_by")

    __table_args__ = (
        Index('idx_family_members_user_id', 'user_id'),
        Index('idx_family_members_telegram_id', 'telegram_id'),
        Index('idx_family_members_role', 'role'),
        Index('idx_family_members_active', 'is_active'),
    )


# Enhanced Conversation Model
class Conversation(Base):
    """Enhanced conversation model with multimodal support."""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(100), nullable=False, index=True)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey('family_members.id'), nullable=False)

    # Message content
    role = Column(MessageRoleEnum, nullable=False)
    content = Column(Text, nullable=True)  # Backward compatibility
    multimodal_content = Column(PydanticJSON, nullable=True)  # List[MultimodalContent]

    # Processing metadata
    processing_time_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)

    # Message metadata
    reply_to_id = Column(UUID(as_uuid=True), nullable=True)
    reactions = Column(JSONB, default=list)
    edited = Column(Boolean, default=False)
    edit_history = Column(JSONB, default=list)

    # Content analysis
    content_analysis = Column(JSONB, nullable=True)  # Analysis results
    safety_analysis = Column(JSONB, nullable=True)  # Safety assessment
    sentiment_analysis = Column(JSONB, nullable=True)  # Sentiment data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    family_member = relationship("FamilyMember", back_populates="conversations")
    content_uploads = relationship("ContentUpload", back_populates="conversation")

    __table_args__ = (
        Index('idx_conversations_thread_id', 'thread_id'),
        Index('idx_conversations_family_member', 'family_member_id'),
        Index('idx_conversations_role', 'role'),
        Index('idx_conversations_created_at', 'created_at'),
        Index('idx_conversations_thread_member', 'thread_id', 'family_member_id'),
    )


# Content Upload Model
class ContentUpload(Base):
    """Model for tracking uploaded content files."""
    __tablename__ = "content_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False, unique=True)
    file_path = Column(String(1000), nullable=False)

    # Content classification
    content_type = Column(ContentTypeEnum, nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=False)

    # Upload metadata
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey('family_members.id'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=True)
    upload_source = Column(String(50), default='telegram')  # telegram, api, etc.

    # Media-specific metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    codec = Column(String(50), nullable=True)

    # Processing status
    processing_status = Column(ProcessingStatusEnum, default=ProcessingStatus.PENDING)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)

    # Processing results
    extracted_data = Column(JSONB, nullable=True)
    analysis_results = Column(JSONB, nullable=True)
    safety_score = Column(Float, nullable=True)

    # Privacy and access control
    privacy_level = Column(String(20), default='family')  # private, family, public
    download_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)

    # Storage information
    storage_backend = Column(String(50), default='local')  # local, s3, gcs
    storage_url = Column(String(1000), nullable=True)
    checksum_md5 = Column(String(32), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    uploaded_by = relationship("FamilyMember", back_populates="content_uploads")
    conversation = relationship("Conversation", back_populates="content_uploads")

    __table_args__ = (
        Index('idx_content_uploads_content_type', 'content_type'),
        Index('idx_content_uploads_uploaded_by', 'uploaded_by_id'),
        Index('idx_content_uploads_conversation', 'conversation_id'),
        Index('idx_content_uploads_status', 'processing_status'),
        Index('idx_content_uploads_created_at', 'created_at'),
        Index('idx_content_uploads_privacy', 'privacy_level'),
    )


# Content Processing Job Model
class ContentProcessingJob(Base):
    """Model for tracking content processing jobs."""
    __tablename__ = "content_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(100), unique=True, nullable=False, index=True)

    # Job details
    content_upload_id = Column(UUID(as_uuid=True), ForeignKey('content_uploads.id'), nullable=False)
    job_type = Column(String(50), nullable=False)  # transcription, ocr, vision_analysis, etc.
    job_parameters = Column(JSONB, nullable=True)

    # Status tracking
    status = Column(ProcessingStatusEnum, default=ProcessingStatus.PENDING)
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(100), nullable=True)

    # Timing information
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Processing results
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Resource usage
    processing_time_ms = Column(Float, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)

    # Worker information
    worker_id = Column(String(100), nullable=True)
    worker_version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_upload = relationship("ContentUpload")

    __table_args__ = (
        Index('idx_content_jobs_job_id', 'job_id'),
        Index('idx_content_jobs_upload_id', 'content_upload_id'),
        Index('idx_content_jobs_status', 'status'),
        Index('idx_content_jobs_type', 'job_type'),
        Index('idx_content_jobs_queued_at', 'queued_at'),
    )


# Family Context Model
class FamilyContext(Base):
    """Model for storing family context information."""
    __tablename__ = "family_context"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey('family_members.id'), nullable=False)

    # Context type and key
    context_type = Column(String(50), nullable=False)  # schedule, preferences, history, etc.
    context_key = Column(String(100), nullable=False)
    context_value = Column(JSONB, nullable=False)

    # Validity and expiry
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Metadata
    source = Column(String(50), nullable=True)  # manual, automatic, etc.
    confidence_score = Column(Float, nullable=True)
    tags = Column(ARRAY(String), default=[])

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    family_member = relationship("FamilyMember")

    __table_args__ = (
        Index('idx_family_context_member_id', 'family_member_id'),
        Index('idx_family_context_type', 'context_type'),
        Index('idx_family_context_key', 'context_key'),
        Index('idx_family_context_active', 'is_active'),
        Index('idx_family_context_validity', 'valid_from', 'valid_until'),
        Index('idx_family_context_unique', 'family_member_id', 'context_type', 'context_key',
              unique=True, postgresql_where='is_active = true'),
    )


# Audit Log Model (Enhanced)
class AuditLog(Base):
    """Enhanced audit log model for multimodal content tracking."""
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey('family_members.id'), nullable=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)

    # Detailed information
    details = Column(JSONB, nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)

    # Request information
    request_ip = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)

    # Context information
    session_id = Column(String(100), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=True)
    content_upload_id = Column(UUID(as_uuid=True), ForeignKey('content_uploads.id'), nullable=True)

    # Security and compliance
    security_level = Column(String(20), default='normal')  # low, normal, high, critical
    compliance_tags = Column(ARRAY(String), default=[])
    retention_days = Column(Integer, default=365)

    # Status
    status = Column(String(20), default='success')  # success, failed, partial
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    family_member = relationship("FamilyMember")
    conversation = relationship("Conversation")
    content_upload = relationship("ContentUpload")

    __table_args__ = (
        Index('idx_audit_member_id', 'family_member_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_security', 'security_level'),
        Index('idx_audit_status', 'status'),
    )


# Database utility functions
def create_family_member_profile(family_member: FamilyMember) -> FamilyMemberProfile:
    """Convert SQLAlchemy FamilyMember to Pydantic FamilyMemberProfile."""
    return FamilyMemberProfile(
        user_id=family_member.user_id,
        name=family_member.name,
        role=family_member.role,
        age=family_member.age,
        preferred_content_types=[ContentType(t) for t in family_member.preferred_content_types or []],
        content_filters=family_member.content_filters or [],
        language_preferences=family_member.language_preferences or ['en'],
        vision_analysis_enabled=family_member.vision_analysis_enabled,
        photo_privacy_level=family_member.photo_privacy_level,
        auto_image_description=family_member.auto_image_description,
        speech_recognition_enabled=family_member.speech_recognition_enabled,
        preferred_audio_format=family_member.preferred_audio_format,
        voice_privacy_level=family_member.voice_privacy_level,
        document_extraction_enabled=family_member.document_extraction_enabled,
        auto_summarization=family_member.auto_summarization,
        permissions=family_member.permissions or {},
        preferences=family_member.preferences or {},
        created_at=family_member.created_at,
        updated_at=family_member.updated_at
    )


def get_family_member_by_user_id(db: Session, user_id: str) -> Optional[FamilyMember]:
    """Get family member by user_id."""
    return db.query(FamilyMember).filter(
        FamilyMember.user_id == user_id,
        FamilyMember.is_active == True
    ).first()


def get_family_member_by_telegram_id(db: Session, telegram_id: int) -> Optional[FamilyMember]:
    """Get family member by Telegram ID."""
    return db.query(FamilyMember).filter(
        FamilyMember.telegram_id == telegram_id,
        FamilyMember.is_active == True
    ).first()


def create_content_processing_result(upload: ContentUpload) -> ContentProcessingResult:
    """Convert SQLAlchemy ContentUpload to Pydantic ContentProcessingResult."""
    return ContentProcessingResult(
        content_id=str(upload.id),
        content_type=upload.content_type,
        processing_status=upload.processing_status,
        processing_time_ms=upload.processing_time_ms,
        extracted_data=upload.extracted_data,
        analysis_results=upload.analysis_results,
        error_message=upload.processing_error,
        created_at=upload.created_at,
        updated_at=upload.updated_at,
        file_size_bytes=upload.file_size_bytes,
        processed_file_path=upload.file_path
    )


# Database initialization functions
def create_multimodal_tables(engine):
    """Create all multimodal database tables."""
    Base.metadata.create_all(engine)
    print("✅ Multimodal database tables created successfully!")


def drop_multimodal_tables(engine):
    """Drop all multimodal database tables."""
    Base.metadata.drop_all(engine)
    print("⚠️  Multimodal database tables dropped!")


# Utility functions for database operations
def get_conversation_multimodal_content(db: Session, thread_id: str) -> List[Dict[str, Any]]:
    """Get conversation with multimodal content."""
    conversations = db.query(Conversation).filter(
        Conversation.thread_id == thread_id
    ).order_by(Conversation.created_at.asc()).all()

    result = []
    for conv in conversations:
        content_data = {
            'id': str(conv.id),
            'role': conv.role.value,
            'content': conv.content,
            'multimodal_content': conv.multimodal_content,
            'timestamp': conv.created_at.isoformat(),
            'processing_time_ms': conv.processing_time_ms,
            'content_analysis': conv.content_analysis,
            'safety_analysis': conv.safety_analysis
        }
        result.append(content_data)

    return result