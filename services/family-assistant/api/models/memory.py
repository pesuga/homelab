"""
Memory and Context Models for Phase 2

Pydantic models for memory management and context handling.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ==============================================================================
# Enums
# ==============================================================================

class UserRole(str, Enum):
    """User role in family hierarchy"""
    PARENT = "parent"
    TEENAGER = "teenager"
    CHILD = "child"
    GRANDPARENT = "grandparent"
    MEMBER = "member"


class LanguagePreference(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    BILINGUAL = "bilingual"


class PrivacyLevel(str, Enum):
    """Conversation privacy levels"""
    PRIVATE = "private"
    FAMILY = "family"
    PARENTAL_ONLY = "parental_only"


class SafetyLevel(str, Enum):
    """Content safety levels"""
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"


# ==============================================================================
# Core Context Models
# ==============================================================================

class MemoryContext(BaseModel):
    """Memory context retrieved from all layers"""
    user_id: str
    conversation_id: str
    immediate_context: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Layer 1: Recent messages from Redis"
    )
    working_memory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Layer 2: Session memories from Mem0"
    )
    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Layer 3: User profile from PostgreSQL"
    )
    semantic_memories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Layer 4: Relevant memories from Qdrant"
    )
    conversation_summary: Optional[str] = Field(
        default=None,
        description="Auto-generated conversation summary"
    )
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences and settings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "conversation_id": "conv-456",
                "immediate_context": [
                    {"role": "user", "content": "Hola, necesito ayuda"},
                    {"role": "assistant", "content": "¡Claro! ¿En qué puedo ayudarte?"}
                ],
                "working_memory": [],
                "structured_data": {"role": "parent", "language": "es"},
                "semantic_memories": [],
                "user_preferences": {"tone": "friendly"}
            }
        }


class UserContext(BaseModel):
    """User context for prompt building"""
    user_id: str
    role: UserRole = Field(
        default=UserRole.PARENT,
        description="User's role in family"
    )
    age_group: Optional[str] = Field(
        default=None,
        description="Age group (child/teen/adult)"
    )
    language_preference: LanguagePreference = Field(
        default=LanguagePreference.ENGLISH,
        description="Preferred language"
    )
    active_skills: List[str] = Field(
        default_factory=list,
        description="Currently active skills/tools"
    )
    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.FAMILY,
        description="Conversation privacy level"
    )
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.ADULT,
        description="Content safety filtering level"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "role": "parent",
                "age_group": "adult",
                "language_preference": "es",
                "active_skills": ["calendar", "reminders"],
                "privacy_level": "family",
                "safety_level": "adult"
            }
        }


# ==============================================================================
# API Request/Response Models
# ==============================================================================

class MemorySearchRequest(BaseModel):
    """Request model for memory search"""
    query: str = Field(..., description="Search query")
    user_id: str = Field(..., description="User ID to search within")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    include_sources: bool = Field(
        default=True,
        description="Include source information (mem0/qdrant)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "eventos familiares en diciembre",
                "user_id": "user-123",
                "limit": 10,
                "include_sources": True
            }
        }


class MemorySearchResponse(BaseModel):
    """Response model for memory search"""
    query: str
    user_id: str
    results: List[Dict[str, Any]]
    result_count: int
    search_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "query": "eventos familiares",
                "user_id": "user-123",
                "results": [
                    {
                        "source": "qdrant",
                        "content": "Cumpleaños de María el 15 de diciembre",
                        "score": 0.89,
                        "timestamp": "2025-11-10T10:30:00"
                    }
                ],
                "result_count": 1,
                "search_time_ms": 245.3
            }
        }


class SaveContextRequest(BaseModel):
    """Request model for saving conversation context"""
    user_id: str
    conversation_id: str
    message_type: str = Field(..., description="user, assistant, or system")
    content: str
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (language, intent, tools_used, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "conversation_id": "conv-456",
                "message_type": "user",
                "content": "Ayúdame con el calendario de esta semana",
                "metadata": {
                    "language": "es",
                    "intent": "calendar_query",
                    "detected_entities": ["esta semana"]
                }
            }
        }


class SaveContextResponse(BaseModel):
    """Response model for context save operation"""
    success: bool
    user_id: str
    conversation_id: str
    layers_saved: List[str] = Field(
        description="Memory layers where context was saved"
    )
    save_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "user_id": "user-123",
                "conversation_id": "conv-456",
                "layers_saved": ["redis", "mem0", "postgresql", "qdrant"],
                "save_time_ms": 156.7
            }
        }


class PromptBuildRequest(BaseModel):
    """Request model for building dynamic prompt"""
    user_id: str
    conversation_id: str
    query: Optional[str] = Field(
        default=None,
        description="Optional semantic search query for relevant memories"
    )
    minimal: bool = Field(
        default=False,
        description="Use minimal prompt for faster inference"
    )
    include_principles: bool = Field(
        default=True,
        description="Include PRINCIPLES.md in prompt"
    )
    include_rules: bool = Field(
        default=True,
        description="Include RULES.md in prompt"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "conversation_id": "conv-456",
                "query": "calendar events",
                "minimal": False,
                "include_principles": True,
                "include_rules": True
            }
        }


class PromptBuildResponse(BaseModel):
    """Response model for prompt build operation"""
    user_id: str
    conversation_id: str
    prompt: str = Field(description="Assembled system prompt")
    prompt_stats: Dict[str, Any] = Field(
        description="Prompt statistics (length, tokens, sections)"
    )
    build_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "conversation_id": "conv-456",
                "prompt": "# Family Assistant Core System Prompt...",
                "prompt_stats": {
                    "total_length": 15432,
                    "estimated_tokens": 3858,
                    "section_count": 8,
                    "has_memory_context": True,
                    "has_language_context": True
                },
                "build_time_ms": 87.3
            }
        }


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    user_id: str
    role: Optional[UserRole] = None
    age_group: Optional[str] = None
    language_preference: Optional[LanguagePreference] = None
    active_skills: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "role": "parent",
                "language_preference": "bilingual",
                "active_skills": ["calendar", "reminders", "homework_help"],
                "preferences": {
                    "tone": "friendly",
                    "verbosity": "concise",
                    "emoji_usage": "moderate"
                }
            }
        }


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    user_id: str
    role: UserRole
    age_group: Optional[str]
    language_preference: LanguagePreference
    active_skills: List[str]
    privacy_level: PrivacyLevel
    safety_level: SafetyLevel
    preferences: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "role": "parent",
                "age_group": "adult",
                "language_preference": "bilingual",
                "active_skills": ["calendar", "reminders"],
                "privacy_level": "family",
                "safety_level": "adult",
                "preferences": {"tone": "friendly"},
                "created_at": "2025-11-01T10:00:00",
                "updated_at": "2025-11-12T14:30:00"
            }
        }


class ConversationSummaryRequest(BaseModel):
    """Request model for conversation summary"""
    conversation_id: str
    user_id: str
    max_messages: int = Field(
        default=50,
        ge=10,
        le=500,
        description="Maximum messages to include in summary"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-456",
                "user_id": "user-123",
                "max_messages": 50
            }
        }


class ConversationSummaryResponse(BaseModel):
    """Response model for conversation summary"""
    conversation_id: str
    user_id: str
    summary: str
    message_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    topics: List[str] = Field(
        default_factory=list,
        description="Main topics discussed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-456",
                "user_id": "user-123",
                "summary": "User asked about family calendar events for December...",
                "message_count": 24,
                "start_time": "2025-11-12T10:00:00",
                "end_time": "2025-11-12T10:45:00",
                "topics": ["calendar", "family_events", "december_planning"]
            }
        }


# ==============================================================================
# Health and Stats Models
# ==============================================================================

class MemoryHealthResponse(BaseModel):
    """Health check response for memory system"""
    status: str = Field(description="healthy, degraded, or unhealthy")
    layers: Dict[str, Dict[str, Any]] = Field(
        description="Status of each memory layer"
    )
    overall_latency_ms: float
    error_rate: float = Field(description="Error rate percentage (0-100)")
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "layers": {
                    "redis": {"status": "healthy", "latency_ms": 2.3},
                    "mem0": {"status": "healthy", "latency_ms": 45.1},
                    "postgresql": {"status": "healthy", "latency_ms": 12.7},
                    "qdrant": {"status": "healthy", "latency_ms": 78.4}
                },
                "overall_latency_ms": 138.5,
                "error_rate": 0.5,
                "timestamp": "2025-11-12T14:30:00"
            }
        }


class MemoryStatsResponse(BaseModel):
    """Statistics response for memory system"""
    total_conversations: int
    total_memories: int
    total_embeddings: int
    storage_used_mb: float
    cache_hit_rate: float = Field(description="Percentage (0-100)")
    avg_retrieval_time_ms: float
    users_active_today: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_conversations": 1247,
                "total_memories": 18532,
                "total_embeddings": 15420,
                "storage_used_mb": 342.7,
                "cache_hit_rate": 87.3,
                "avg_retrieval_time_ms": 234.5,
                "users_active_today": 12
            }
        }
