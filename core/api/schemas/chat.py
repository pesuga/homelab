"""
Chat Schemas

Pydantic models for chat and interaction request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """Request for chat interaction with family AI."""
    message: str = Field(..., min_length=1, max_length=4000, description="The message to send to the AI")
    interaction_type: str = Field(default="text", pattern="^(text|voice|command)$", description="Type of interaction")
    language: Optional[str] = Field(None, pattern="^(es|en)$", description="Language code (es or en)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the interaction")
    model: Optional[str] = Field(None, description="Specific AI model to use")

class ChatResponse(BaseModel):
    """Response from chat interaction."""
    interaction_id: str
    response: str
    timestamp: datetime
    language: str
    sentiment: str = Field(pattern="^(positive|neutral|negative)$")
    memories_accessed: List[str] = []
    follow_up_suggestions: List[str] = []
    processing_time: float = Field(ge=0, description="Processing time in seconds")

class ConversationHistoryResponse(BaseModel):
    """Individual conversation entry from history."""
    interaction_id: str
    member_id: str
    interaction_type: str
    content: str
    response: str
    timestamp: datetime
    language: str
    sentiment: str

class FamilySummaryResponse(BaseModel):
    """Family interaction summary."""
    total_interactions: int
    sentiment_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    active_members: int
    last_interaction: Optional[datetime]

class MemoryCreateRequest(BaseModel):
    """Request to create a new memory."""
    category: str = Field(..., pattern="^(preference|schedule|event|knowledge|interaction)$")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    importance: int = Field(default=5, ge=1, le=10, description="Importance score from 1-10")
    metadata: Optional[Dict[str, Any]] = {}
    expires_at: Optional[datetime] = None

class MemoryResponse(BaseModel):
    """Memory response."""
    id: str
    family_id: str
    category: str
    title: str
    content: str
    importance: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    metadata: Dict[str, Any]
    relevance_score: float = Field(ge=0, le=1)

class VoiceTranscriptionRequest(BaseModel):
    """Request for voice transcription."""
    audio_format: str = Field(default="wav", pattern="^(wav|mp3|ogg|m4a)$")
    language: Optional[str] = Field(None, pattern="^(es|en)$")

class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription."""
    transcription: str
    confidence: float = Field(ge=0, le=1)
    language: str
    processing_time: float

class ModelStatusResponse(BaseModel):
    """AI model status response."""
    llm_service: str = Field(pattern="^(healthy|unhealthy|degraded)$")
    memory_service: str = Field(pattern="^(healthy|unhealthy|degraded)$")
    overall_status: str = Field(pattern="^(healthy|unhealthy|degraded)$")
    available_models: List[str] = []
    default_model: str

class FamilyInsight(BaseModel):
    """Family interaction insight."""
    type: str = Field(pattern="^(sentiment|activity|language|preference)$")
    title: str
    description: str
    data: Dict[str, Any]
    recommendation: Optional[str] = None
    confidence: float = Field(ge=0, le=1)

class FamilyAnalytics(BaseModel):
    """Family interaction analytics."""
    total_interactions: int
    average_interactions_per_day: float
    most_active_hour: int
    preferred_language: str
    sentiment_trend: List[Dict[str, Any]]
    activity_by_member: Dict[str, int]
    common_topics: List[Dict[str, Any]]
    insights: List[FamilyInsight]