"""
Voice Schemas

Pydantic models for voice transcription and interaction validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AudioMetadata(BaseModel):
    """Audio file metadata."""
    format: str
    duration: float = Field(ge=0, description="Audio duration in seconds")
    sample_rate: int = Field(gt=0, description="Sample rate in Hz")
    channels: int = Field(gt=0, description="Number of audio channels")
    size: int = Field(ge=0, description="File size in bytes")

class VoiceTranscriptionRequest(BaseModel):
    """Request for voice transcription."""
    audio_format: str = Field(..., pattern="^(wav|mp3|ogg|m4a|flac)$")
    language: Optional[str] = Field(None, pattern="^(es|en|fr|de|it|pt)$")
    model: Optional[str] = None

class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription."""
    transcription: str
    confidence: float = Field(ge=0, le=1, description="Transcription confidence score")
    language_detected: str
    processing_time: float = Field(ge=0, description="Processing time in seconds")
    audio_metadata: AudioMetadata

class VoiceInteractionRequest(BaseModel):
    """Request for complete voice interaction processing."""
    audio_data: bytes  # Raw audio data
    audio_format: str = Field(..., pattern="^(wav|mp3|ogg|m4a|flac)$")
    family_id: str
    member_id: str
    context: Optional[Dict[str, Any]] = {}

class VoiceInteractionResponse(BaseModel):
    """Response from voice interaction processing."""
    transcription: str
    confidence: float = Field(ge=0, le=1)
    language: str
    response: Optional[str] = None
    audio_response_url: Optional[str] = None
    processing_time: float = Field(ge=0)

class AudioUploadResponse(BaseModel):
    """Response from audio file upload."""
    file_id: str
    filename: str
    size: int = Field(ge=0)
    content_type: str
    upload_status: str = Field(pattern="^(pending|processing|completed|failed)$")
    description: Optional[str] = None
    processing_url: Optional[str] = None

class VoiceStatusResponse(BaseModel):
    """Voice service status response."""
    service_status: str = Field(pattern="^(healthy|unhealthy|degraded)$")
    supported_languages: list[str]
    supported_formats: list[str]
    max_file_size_mb: int = Field(ge=0)
    default_model: str
    default_language: str
    service_info: Dict[str, Any] = {}

class VoiceAnalytics(BaseModel):
    """Voice interaction analytics."""
    period_days: int
    total_voice_interactions: int
    by_language: list[Dict[str, Any]]
    by_member: list[Dict[str, Any]]
    daily_activity: list[Dict[str, Any]]
    average_confidence: Optional[float] = Field(None, ge=0, le=1)
    total_duration_seconds: Optional[float] = Field(None, ge=0)

class VoiceSettings(BaseModel):
    """Voice service settings."""
    preferred_language: str = Field(default="es", pattern="^(es|en)$")
    auto_transcribe: bool = True
    save_recordings: bool = True
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    max_recording_duration: int = Field(default=300, ge=1, le=3600, description="Max recording duration in seconds")

class VoiceProfile(BaseModel):
    """Voice profile for a family member."""
    member_id: str
    voice_characteristics: Dict[str, Any]
    accuracy_improvements: Dict[str, float]
    common_phrases: list[str]
    language_preferences: list[str]
    created_at: datetime
    last_updated: datetime

class VoiceCommand(BaseModel):
    """Voice command structure."""
    command: str
    intent: str
    parameters: Dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    language: str
    processing_time: float = Field(ge=0)

class VoiceCommandResponse(BaseModel):
    """Response from voice command processing."""
    command: VoiceCommand
    response: Optional[str] = None
    action_taken: Optional[str] = None
    success: bool
    error_message: Optional[str] = None