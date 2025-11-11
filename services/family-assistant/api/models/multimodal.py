"""
Multimodal content models and schemas for Family Assistant.

Supports:
- Text content with rich formatting
- Image content with metadata
- Audio content with transcription
- File attachments with processing status
- Combined multimodal messages
"""

import uuid
from enum import Enum
from typing import Optional, List, Dict, Any, Union, BinaryIO
from datetime import datetime
from pydantic import BaseModel, Field, validator
from pydantic.types import constr, confloat, conint


class ContentType(str, Enum):
    """Content types supported by the Family Assistant."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    FILE = "file"


class ProcessingStatus(str, Enum):
    """Processing status for multimodal content."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MessageRole(str, Enum):
    """Message roles in conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MediaMetadata(BaseModel):
    """Metadata for media content."""
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None  # For images/videos
    height: Optional[int] = None  # For images/videos
    duration_seconds: Optional[float] = None  # For audio/video
    format: Optional[str] = None  # e.g., "jpeg", "png", "mp3", "mp4"
    codec: Optional[str] = None  # e.g., "h264", "aac"
    fps: Optional[float] = None  # For video

    @validator('width', 'height')
    def validate_dimensions(cls, v, values):
        """Validate that dimensions are positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Dimensions must be positive')
        return v


class TextContent(BaseModel):
    """Text content with rich metadata."""
    content: constr(min_length=1, max_length=100000) = Field(..., description="Text content")
    language_code: Optional[str] = Field(None, description="ISO 639-1 language code")
    content_type: str = Field(ContentType.TEXT, description="Content type identifier")
    word_count: Optional[int] = Field(None, description="Number of words in text")
    reading_time_minutes: Optional[float] = Field(None, description="Estimated reading time")
    sentiment_score: Optional[confloat(ge=-1.0, le=1.0)] = Field(None, description="Sentiment analysis score")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities detected")
    keywords: Optional[List[str]] = Field(None, description="Keywords extracted from text")

    @validator('reading_time_minutes')
    def calculate_reading_time(cls, v, values):
        """Calculate reading time if word count is available."""
        if v is None and 'word_count' in values and values['word_count']:
            # Average reading speed: 200-250 words per minute
            return max(0.1, values['word_count'] / 250.0)
        return v


class ImageContent(BaseModel):
    """Image content with analysis metadata."""
    file_data: Optional[bytes] = Field(None, description="Raw image data")
    file_path: Optional[str] = Field(None, description="Path to stored image file")
    url: Optional[str] = Field(None, description="URL to image resource")
    caption: Optional[str] = Field(None, description="Image caption or description")
    content_type: str = Field(ContentType.IMAGE, description="Content type identifier")
    metadata: MediaMetadata = Field(..., description="Image metadata")

    # Vision analysis results
    description: Optional[str] = Field(None, description="AI-generated image description")
    objects_detected: Optional[List[Dict[str, Any]]] = Field(None, description="Objects detected in image")
    faces_detected: Optional[List[Dict[str, Any]]] = Field(None, description="Faces detected in image")
    text_detected: Optional[List[str]] = Field(None, description="Text detected in image (OCR)")
    emotional_analysis: Optional[Dict[str, float]] = Field(None, description="Emotional analysis results")
    safety_score: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Content safety score")

    @validator('file_data', 'file_path', 'url')
    def validate_image_source(cls, v, values):
        """Ensure at least one image source is provided."""
        if not any([v, values.get('file_path'), values.get('url')]):
            raise ValueError('At least one of file_data, file_path, or url must be provided')
        return v


class AudioContent(BaseModel):
    """Audio content with transcription metadata."""
    file_data: Optional[bytes] = Field(None, description="Raw audio data")
    file_path: Optional[str] = Field(None, description="Path to stored audio file")
    url: Optional[str] = Field(None, description="URL to audio resource")
    caption: Optional[str] = Field(None, description="Audio description or context")
    content_type: str = Field(ContentType.AUDIO, description="Content type identifier")
    metadata: MediaMetadata = Field(..., description="Audio metadata")

    # Speech processing results
    transcription: Optional[str] = Field(None, description="Transcribed text content")
    language_code: Optional[str] = Field(None, description="Detected language")
    speaker_count: Optional[int] = Field(None, description="Number of speakers detected")
    speaker_diarization: Optional[List[Dict[str, Any]]] = Field(None, description="Speaker segments")
    confidence_score: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Transcription confidence")
    sentiment_analysis: Optional[Dict[str, Any]] = Field(None, description="Sentiment analysis of speech")
    keywords_spoken: Optional[List[str]] = Field(None, description="Keywords detected in speech")

    @validator('file_data', 'file_path', 'url')
    def validate_audio_source(cls, v, values):
        """Ensure at least one audio source is provided."""
        if not any([v, values.get('file_path'), values.get('url')]):
            raise ValueError('At least one of file_data, file_path, or url must be provided')
        return v


class DocumentContent(BaseModel):
    """Document content with text extraction metadata."""
    file_data: Optional[bytes] = Field(None, description="Raw document data")
    file_path: Optional[str] = Field(None, description="Path to stored document file")
    url: Optional[str] = Field(None, description="URL to document resource")
    caption: Optional[str] = Field(None, description="Document description")
    content_type: str = Field(ContentType.DOCUMENT, description="Content type identifier")
    metadata: MediaMetadata = Field(..., description="Document metadata")

    # Document processing results
    extracted_text: Optional[str] = Field(None, description="Extracted text content")
    page_count: Optional[int] = Field(None, description="Number of pages")
    table_count: Optional[int] = Field(None, description="Number of tables detected")
    image_count: Optional[int] = Field(None, description="Number of images detected")
    summary: Optional[str] = Field(None, description="Document summary")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities in document")
    processing_status: ProcessingStatus = Field(ProcessingStatus.PENDING, description="Processing status")

    @validator('file_data', 'file_path', 'url')
    def validate_document_source(cls, v, values):
        """Ensure at least one document source is provided."""
        if not any([v, values.get('file_path'), values.get('url')]):
            raise ValueError('At least one of file_data, file_path, or url must be provided')
        return v


class MultimodalContent(BaseModel):
    """Union type for all supported content types."""
    content: Union[TextContent, ImageContent, AudioContent, DocumentContent]

    class Config:
        """Pydantic configuration for multimodal content."""
        use_enum_values = True
        extra = "forbid"


class ChatMessage(BaseModel):
    """Enhanced chat message supporting multimodal content."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    # Content support - can be simple text or complex multimodal
    content: Optional[str] = Field(None, description="Simple text content (backward compatibility)")
    multimodal_content: Optional[List[MultimodalContent]] = Field(None, description="Multimodal content list")

    # Processing and analysis metadata
    processing_time_ms: Optional[float] = Field(None, description="Time taken to process message")
    tokens_used: Optional[int] = Field(None, description="Tokens used for processing")
    model_used: Optional[str] = Field(None, description="AI model used for processing")

    # Message metadata
    user_id: Optional[str] = Field(None, description="User identifier")
    thread_id: Optional[str] = Field(None, description="Conversation thread identifier")
    reply_to_id: Optional[str] = Field(None, description="ID of message this replies to")
    reactions: Optional[List[Dict[str, Any]]] = Field(None, description="User reactions to message")
    edited: bool = Field(False, description="Whether message has been edited")
    edit_history: Optional[List[Dict[str, Any]]] = Field(None, description="Edit history")

    @validator('multimodal_content')
    def validate_multimodal_content(cls, v, values):
        """Validate multimodal content."""
        if v and not values.get('content'):
            # Set content to a summary of multimodal content for backward compatibility
            content_parts = []
            for item in v:
                if isinstance(item.content, TextContent):
                    content_parts.append(item.content.content[:100] + "..." if len(item.content.content) > 100 else item.content.content)
                elif isinstance(item.content, ImageContent):
                    content_parts.append(f"[Image: {item.content.caption or 'No caption'}]")
                elif isinstance(item.content, AudioContent):
                    content_parts.append(f"[Audio: {item.content.caption or 'No caption'}]")
                elif isinstance(item.content, DocumentContent):
                    content_parts.append(f"[Document: {item.content.caption or 'No caption'}]")
            values['content'] = " | ".join(content_parts)
        return v


class MultimodalChatRequest(BaseModel):
    """Enhanced chat request supporting multimodal content."""
    model: str = Field("family-assistant", description="AI model to use")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")

    # Generation parameters
    temperature: Optional[confloat(ge=0.0, le=2.0)] = Field(0.7, description="Generation temperature")
    max_tokens: Optional[conint(ge=1, le=32768)] = Field(2048, description="Maximum tokens to generate")
    top_p: Optional[confloat(ge=0.0, le=1.0)] = Field(0.9, description="Nucleus sampling parameter")
    top_k: Optional[conint(ge=1)] = Field(40, description="Top-k sampling parameter")
    repeat_penalty: Optional[confloat(ge=0.0, le=2.0)] = Field(1.1, description="Repeat penalty")

    # Streaming and response format
    stream: bool = Field(False, description="Enable streaming response")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Response format specification")

    # Context and memory
    user_id: Optional[str] = Field(None, description="User identifier")
    thread_id: Optional[str] = Field(None, description="Conversation thread identifier")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    context_window: Optional[conint(ge=1, le=128)] = Field(10, description="Context window size")

    # Processing options
    enable_vision_analysis: bool = Field(True, description="Enable image content analysis")
    enable_speech_recognition: bool = Field(True, description="Enable audio transcription")
    enable_document_extraction: bool = Field(True, description="Enable document text extraction")
    enable_content_filtering: bool = Field(True, description="Enable content safety filtering")

    # Family-specific options
    family_context: Optional[Dict[str, Any]] = Field(None, description="Family context information")
    time_zone: Optional[str] = Field("UTC", description="Time zone for time-sensitive content")
    language_preference: Optional[str] = Field("en", description="Preferred language code")


class MultimodalChatResponse(BaseModel):
    """Enhanced chat response with multimodal processing metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Response identifier")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")

    # Response content
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")

    # Enhanced usage statistics
    usage: Dict[str, Union[int, float]] = Field(..., description="Token usage statistics")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time")

    # Multimodal processing metadata
    content_processed: Dict[str, int] = Field(default_factory=dict, description="Count of content types processed")
    analysis_results: Optional[Dict[str, Any]] = Field(None, description="Content analysis results")
    safety_analysis: Optional[Dict[str, Any]] = Field(None, description="Content safety analysis")

    # Family context
    family_actions_suggested: Optional[List[Dict[str, Any]]] = Field(None, description="Family-oriented actions suggested")
    time_sensitive_info: Optional[List[Dict[str, Any]]] = Field(None, description="Time-sensitive information detected")


class ContentProcessingResult(BaseModel):
    """Result of processing multimodal content."""
    content_id: str = Field(..., description="Content identifier")
    content_type: ContentType = Field(..., description="Type of content processed")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

    # Processing results
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Data extracted from content")
    analysis_results: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: Optional[int] = Field(None, description="Original file size")
    processed_file_path: Optional[str] = Field(None, description="Path to processed file")


class FamilyMemberProfile(BaseModel):
    """Enhanced family member profile with multimodal preferences."""
    user_id: str = Field(..., description="Family member identifier")
    name: str = Field(..., description="Family member name")
    role: str = Field(..., description="Family role (parent, child, teenager, grandparent)")
    age: Optional[int] = Field(None, description="Family member age")

    # Multimodal preferences
    preferred_content_types: List[ContentType] = Field(default_factory=list, description="Preferred content types")
    content_filters: List[str] = Field(default_factory=list, description="Content filtering preferences")
    language_preferences: List[str] = Field(default_factory=lambda: ["en"], description="Preferred languages")

    # Vision preferences
    vision_analysis_enabled: bool = Field(True, description="Enable image content analysis")
    photo_privacy_level: str = Field("family", description="Photo privacy settings")
    auto_image_description: bool = Field(True, description="Automatically describe images")

    # Audio preferences
    speech_recognition_enabled: bool = Field(True, description="Enable speech recognition")
    preferred_audio_format: str = Field("ogg", description="Preferred audio format")
    voice_privacy_level: str = Field("family", description="Voice privacy settings")

    # Document preferences
    document_extraction_enabled: bool = Field(True, description="Enable document text extraction")
    auto_summarization: bool = Field(False, description="Automatically summarize documents")

    # Permissions (enhanced for multimodal)
    permissions: Dict[str, bool] = Field(default_factory=dict, description="User permissions")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('photo_privacy_level', 'voice_privacy_level')
    def validate_privacy_levels(cls, v):
        """Validate privacy level values."""
        valid_levels = ["private", "family", "public"]
        if v not in valid_levels:
            raise ValueError(f'Privacy level must be one of: {valid_levels}')
        return v


# Backward compatibility aliases
OpenAIChatMessage = ChatMessage
OpenAIChatRequest = MultimodalChatRequest
OpenAIChatResponse = MultimodalChatResponse