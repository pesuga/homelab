"""
Voice API Routes

Endpoints for voice-based interactions, speech-to-text, and audio processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from ..dependencies import get_db, get_current_member, CurrentMember
from ..schemas.voice import (
    VoiceTranscriptionRequest, VoiceTranscriptionResponse,
    VoiceInteractionRequest, VoiceInteractionResponse,
    AudioUploadResponse, VoiceStatusResponse
)
from ...services.voice_service import VoiceService, VoiceConfig
from ...services.family_engine import FamilyEngine
from ...services.family_context import FamilyContextService
from ...services.memory_service import MemoryService
import tempfile
import os
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize voice service
voice_config = VoiceConfig()
voice_service = VoiceService(voice_config)

@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Transcribe audio file using Whisper speech-to-text.

    Supports WAV, MP3, OGG, M4A, and FLAC formats with automatic language detection.
    """
    try:
        # Check voice service availability
        if not await voice_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice transcription service is currently unavailable"
            )

        # Validate file format
        if not audio_file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file format not specified"
            )

        # Extract format from content type or filename
        format_mapping = {
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/mp3": "mp3",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "audio/m4a": "m4a",
            "audio/x-m4a": "m4a",
            "audio/flac": "flac"
        }

        audio_format = format_mapping.get(audio_file.content_type.lower())
        if not audio_format:
            # Try to get from filename
            if audio_file.filename:
                ext = os.path.splitext(audio_file.filename)[1].lower().lstrip('.')
                if ext in voice_config.supported_formats:
                    audio_format = ext
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported audio format: {ext}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to determine audio format"
                )

        # Read audio data
        audio_data = await audio_file.read()

        # Validate audio size
        if len(audio_data) > voice_config.max_audio_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio file too large. Maximum size: {voice_config.max_audio_size // (1024*1024)}MB"
            )

        # Transcribe audio
        transcription_result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language or current_member.preferences.get("preferred_language", "es")
        )

        return VoiceTranscriptionResponse(
            transcription=transcription_result.text,
            confidence=transcription_result.confidence,
            language_detected=transcription_result.language_detected,
            processing_time=transcription_result.processing_time,
            audio_metadata=transcription_result.audio_metadata.dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )

@router.post("/interaction", response_model=VoiceInteractionResponse)
async def process_voice_interaction(
    audio_file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Process complete voice interaction including transcription and AI response.

    This endpoint handles the full voice interaction flow:
    1. Speech-to-text transcription
    2. AI response generation with family context
    3. Optional text-to-speech (future enhancement)
    """
    try:
        # Check service availability
        if not await voice_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice service is currently unavailable"
            )

        # Validate and read audio
        audio_data = await audio_file.read()

        if len(audio_data) > voice_config.max_audio_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Audio file too large"
            )

        # Detect voice activity
        if not voice_service.detect_voice_activity(audio_data, "wav"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No voice activity detected in audio"
            )

        # Determine audio format
        audio_format = "wav"  # Default to WAV, could be enhanced to detect from file
        if audio_file.filename:
            ext = os.path.splitext(audio_file.filename)[1].lower().lstrip('.')
            if ext in voice_config.supported_formats:
                audio_format = ext

        # Parse context
        interaction_context = {}
        if context:
            import json
            try:
                interaction_context = json.loads(context)
            except json.JSONDecodeError:
                interaction_context = {"raw_context": context}

        # Initialize family engine
        family_context_service = FamilyContextService()
        memory_service = MemoryService()
        family_engine = FamilyEngine(
            llm_service=None,  # Will be initialized if needed
            family_context_service=family_context_service,
            memory_service=memory_service,
            db=db
        )

        # Create voice interaction request
        voice_request = VoiceInteractionRequest(
            audio_data=audio_data,
            audio_format=audio_format,
            family_id=current_member.family_id,
            member_id=current_member.id,
            context=interaction_context
        )

        # Process voice interaction
        response = await voice_service.process_voice_interaction(
            request=voice_request,
            family_engine=family_engine
        )

        return VoiceInteractionResponse(
            transcription=response.transcription,
            confidence=response.confidence,
            language=response.language,
            response=response.response,
            processing_time=response.processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice interaction processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice interaction"
        )

@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio_file(
    audio_file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Upload and store audio file for later processing.

    Useful for batch processing or when immediate processing is not needed.
    """
    try:
        # Validate file
        if not audio_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Read audio data
        audio_data = await audio_file.read()

        # Save to temporary location or cloud storage
        # For now, we'll just return metadata about the upload
        file_id = f"audio-{current_member.id}-{int(time.time())}"

        # In production, this would:
        # 1. Save file to storage (S3, local filesystem, etc.)
        # 2. Create database record
        # 3. Return file metadata and processing status

        return AudioUploadResponse(
            file_id=file_id,
            filename=audio_file.filename,
            size=len(audio_data),
            content_type=audio_file.content_type,
            upload_status="completed",
            description=description or ""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload audio file"
        )

@router.get("/status", response_model=VoiceStatusResponse)
async def get_voice_service_status(
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get status of voice service and available features.
    """
    try:
        # Check service health
        is_healthy = await voice_service.health_check()

        # Get supported languages
        supported_languages = await voice_service.get_supported_languages()

        # Get service info
        service_info = await voice_service.get_service_info()

        return VoiceStatusResponse(
            service_status="healthy" if is_healthy else "unhealthy",
            supported_languages=supported_languages,
            supported_formats=voice_config.supported_formats,
            max_file_size_mb=voice_config.max_audio_size // (1024 * 1024),
            default_model=voice_config.whisper_model,
            default_language=voice_config.language,
            service_info=service_info
        )

    except Exception as e:
        logger.error(f"Failed to get voice service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice service status"
        )

@router.get("/languages")
async def get_supported_languages(
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get list of languages supported by the voice service.
    """
    try:
        languages = await voice_service.get_supported_languages()
        return {
            "languages": languages,
            "default_language": voice_config.language,
            "language_codes": {
                "es": "Spanish",
                "en": "English",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        return {
            "languages": ["es", "en"],  # Fallback
            "default_language": "es"
        }

@router.delete("/cleanup/{family_id}")
async def cleanup_old_recordings(
    family_id: str,
    days_old: int = 7,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Clean up old voice recordings for a family.
    Only available to parents and grandparents.
    """
    try:
        # Check permissions
        if current_member.role not in ["parent", "grandparent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parental access required for cleanup operations"
            )

        # Verify family ownership
        if current_member.family_id != family_id and current_member.role != "grandparent":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only clean up recordings for your own family"
            )

        # Perform cleanup
        deleted_count = await voice_service.cleanup_old_recordings(family_id, days_old)

        return {
            "message": f"Cleanup completed",
            "deleted_count": deleted_count,
            "family_id": family_id,
            "days_old": days_old
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old recordings"
        )

@router.get("/analytics/{family_id}")
async def get_voice_analytics(
    family_id: str,
    days: int = 30,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get voice interaction analytics for a family.
    Only available to parents and grandparents.
    """
    try:
        # Check permissions
        if current_member.role not in ["parent", "grandparent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parental access required for analytics"
            )

        # Verify family access
        if current_member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get voice analytics from database
        from models.database import FamilyInteraction
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        # Voice interactions by language
        voice_by_language = db.query(
            FamilyInteraction.language,
            func.count(FamilyInteraction.id).label('count')
        ).filter(
            FamilyInteraction.family_id == family_id,
            FamilyInteraction.interaction_type == "voice",
            FamilyInteraction.timestamp >= start_date
        ).group_by(FamilyInteraction.language).all()

        # Voice interactions by member
        voice_by_member = db.query(
            FamilyInteraction.family_member_id,
            func.count(FamilyInteraction.id).label('count')
        ).filter(
            FamilyInteraction.family_id == family_id,
            FamilyInteraction.interaction_type == "voice",
            FamilyInteraction.timestamp >= start_date
        ).group_by(FamilyInteraction.family_member_id).all()

        # Daily voice activity
        daily_activity = db.query(
            extract('day', FamilyInteraction.timestamp).label('day'),
            extract('month', FamilyInteraction.timestamp).label('month'),
            func.count(FamilyInteraction.id).label('count')
        ).filter(
            FamilyInteraction.family_id == family_id,
            FamilyInteraction.interaction_type == "voice",
            FamilyInteraction.timestamp >= start_date
        ).group_by(
            extract('day', FamilyInteraction.timestamp),
            extract('month', FamilyInteraction.timestamp)
        ).all()

        return {
            "period_days": days,
            "total_voice_interactions": sum(count for _, count in voice_by_member),
            "by_language": [{"language": lang, "count": count} for lang, count in voice_by_language],
            "by_member": [{"member_id": member_id, "count": count} for member_id, count in voice_by_member],
            "daily_activity": [
                {"day": f"{int(month)}/{int(day)}", "count": count}
                for day, month, count in daily_activity
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice analytics"
        )