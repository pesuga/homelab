"""
Chat and Interaction API Routes

Main endpoints for family AI interactions, chat, and conversation management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging

from ..dependencies import get_db, get_current_member, CurrentMember
from ..schemas.chat import (
    ChatRequest, ChatResponse, ConversationHistoryRequest,
    ConversationHistoryResponse, FamilySummaryResponse
)
from ...services.llm_service import LLMService, LLMMessage
from ...services.family_engine import FamilyEngine, InteractionRequest
from ...services.family_context import FamilyContextService
from ...services.memory_service import MemoryService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global services (in production, use dependency injection)
llm_service = LLMService()
family_context_service = FamilyContextService()
memory_service = MemoryService()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Main chat endpoint for family AI interactions.

    Supports text and voice interactions with bilingual capabilities,
    family context awareness, and memory integration.
    """
    try:
        # Initialize family engine
        family_engine = FamilyEngine(
            llm_service=llm_service,
            family_context_service=family_context_service,
            memory_service=memory_service,
            db=db
        )

        # Check LLM service availability
        if not await llm_service.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is currently unavailable"
            )

        # Process interaction
        interaction_request = InteractionRequest(
            message=request.message,
            interaction_type=request.interaction_type,
            language=request.language,
            context={
                "family_id": current_member.family_id,
                **(request.context or {})
            },
            member_id=current_member.id
        )

        response = await family_engine.process_interaction(interaction_request)

        # Schedule memory cleanup in background
        background_tasks.add_task(
            memory_service.cleanup_expired_memories,
            current_member.family_id
        )

        return ChatResponse(
            interaction_id=response.interaction_id,
            response=response.response,
            timestamp=response.timestamp,
            language=response.language,
            sentiment=response.sentiment,
            memories_accessed=response.memories_accessed,
            follow_up_suggestions=response.follow_up_suggestions,
            processing_time=response.processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat interaction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat interaction"
        )

@router.get("/conversation/history", response_model=List[ConversationHistoryResponse])
async def get_conversation_history(
    limit: int = 20,
    member_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get conversation history for the family or specific family member.
    """
    try:
        # Initialize family engine
        family_engine = FamilyEngine(
            llm_service=llm_service,
            family_context_service=family_context_service,
            memory_service=memory_service,
            db=db
        )

        # Get conversation history
        target_member_id = member_id or current_member.id
        history = await family_engine.get_conversation_history(
            family_id=current_member.family_id,
            member_id=target_member_id,
            limit=limit
        )

        return [
            ConversationHistoryResponse(
                interaction_id=interaction["id"],
                member_id=interaction["member_id"],
                interaction_type=interaction["type"],
                content=interaction["content"],
                response=interaction["response"],
                timestamp=interaction["timestamp"],
                language=interaction["language"],
                sentiment=interaction["sentiment"]
            )
            for interaction in history
        ]

    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )

@router.get("/family/summary", response_model=FamilySummaryResponse)
async def get_family_summary(
    db: Session = Depends(get_db),
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get family interaction summary and insights.
    Only available to parents and grandparents.
    """
    try:
        # Check permissions (only parents and grandparents can see family summary)
        if current_member.role not in ["parent", "grandparent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parental access required for family summary"
            )

        # Initialize family engine
        family_engine = FamilyEngine(
            llm_service=llm_service,
            family_context_service=family_context_service,
            memory_service=memory_service,
            db=db
        )

        # Get family summary
        summary = await family_engine.get_family_summary(current_member.family_id)

        return FamilySummaryResponse(
            total_interactions=summary.get("total_interactions", 0),
            sentiment_distribution=summary.get("sentiment_distribution", {}),
            language_distribution=summary.get("language_distribution", {}),
            active_members=summary.get("active_members", 0),
            last_interaction=summary.get("last_interaction")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get family summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve family summary"
        )

@router.get("/models/available")
async def get_available_models(
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get list of available AI models.
    """
    try:
        models = await llm_service.list_models()
        return {"models": models, "default": llm_service.config.default_model}

    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available models"
        )

@router.get("/models/status")
async def get_model_status(
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get status of AI services.
    """
    try:
        llm_status = await llm_service.health_check()
        memory_status = await memory_service.health_check()

        return {
            "llm_service": "healthy" if llm_status else "unhealthy",
            "memory_service": "healthy" if memory_status else "unhealthy",
            "overall_status": "healthy" if llm_status and memory_status else "degraded"
        }

    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service status"
        )

@router.post("/voice/transcribe")
async def transcribe_voice(
    background_tasks: BackgroundTasks,
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Transcribe voice message using Whisper service.
    Note: This is a placeholder - actual implementation would integrate with Whisper service.
    """
    try:
        # Placeholder for voice transcription
        # In production, this would:
        # 1. Receive audio file
        # 2. Send to Whisper service
        # 3. Return transcription

        return {
            "message": "Voice transcription not yet implemented",
            "note": "This endpoint will integrate with Whisper service for speech-to-text"
        }

    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice transcription failed"
        )

@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db),
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Delete a specific memory.
    Only available to parents and grandparents.
    """
    try:
        # Check permissions
        if current_member.role not in ["parent", "grandparent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parental access required to delete memories"
            )

        # Delete memory
        success = await memory_service.delete_memory(memory_id)

        if success:
            return {"message": "Memory deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )

@router.get("/memory/search")
async def search_memories(
    q: str,
    category: Optional[str] = None,
    limit: int = 10,
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Search family memories.
    """
    try:
        memories = await memory_service.search_memories(
            family_id=current_member.family_id,
            query=q,
            category=category,
            limit=limit
        )

        return {
            "query": q,
            "category": category,
            "memories": memories,
            "count": len(memories)
        }

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory search failed"
        )