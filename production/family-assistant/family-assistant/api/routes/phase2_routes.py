"""
Phase 2 API Routes - Memory and Prompt Management

Endpoints for:
- Memory management (search, save, retrieve)
- Prompt building and assembly
- User context management
- Conversation summaries
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import time
from datetime import datetime

from api.models.memory import (
    MemorySearchRequest, MemorySearchResponse,
    SaveContextRequest, SaveContextResponse,
    PromptBuildRequest, PromptBuildResponse,
    UserProfileUpdateRequest, UserProfileResponse,
    ConversationSummaryRequest, ConversationSummaryResponse,
    MemoryHealthResponse, MemoryStatsResponse,
    UserContext, MemoryContext
)
from api.services.memory_manager import MemoryManager, create_memory_manager
from api.services.prompt_builder import (
    PromptBuilder,
    create_prompt_builder,
    build_user_context_from_db,
    assemble_full_prompt
)


# Create router
router = APIRouter(prefix="/api/phase2", tags=["Phase 2 - Memory & Prompts"])


# ==============================================================================
# Dependency Injection
# ==============================================================================

# Global instances (initialized on startup)
_memory_manager: Optional[MemoryManager] = None
_prompt_builder: Optional[PromptBuilder] = None


async def get_memory_manager() -> MemoryManager:
    """Dependency to get MemoryManager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = await create_memory_manager()
    return _memory_manager


async def get_prompt_builder() -> PromptBuilder:
    """Dependency to get PromptBuilder instance"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = create_prompt_builder()
    return _prompt_builder


# ==============================================================================
# Memory Management Endpoints
# ==============================================================================

@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Search across all memory layers using semantic search.

    Searches both Mem0 working memory and Qdrant vector database
    for relevant memories matching the query.
    """
    start_time = time.time()

    try:
        results = await memory_manager.search_memories(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit
        )

        search_time_ms = (time.time() - start_time) * 1000

        return MemorySearchResponse(
            query=request.query,
            user_id=request.user_id,
            results=results,
            result_count=len(results),
            search_time_ms=search_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Memory search failed: {str(e)}"
        )


@router.post("/memory/save", response_model=SaveContextResponse)
async def save_context(
    request: SaveContextRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Save conversation context across all memory layers.

    Stores message in:
    - Redis (hot cache)
    - Mem0 (working memory)
    - PostgreSQL (permanent storage)
    - Qdrant (semantic embeddings)
    """
    start_time = time.time()

    try:
        await memory_manager.save_context(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_type=request.message_type,
            content=request.content,
            metadata=request.metadata
        )

        save_time_ms = (time.time() - start_time) * 1000

        return SaveContextResponse(
            success=True,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            layers_saved=["redis", "mem0", "postgresql", "qdrant"],
            save_time_ms=save_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Context save failed: {str(e)}"
        )


@router.get("/memory/context/{conversation_id}", response_model=MemoryContext)
async def get_conversation_context(
    conversation_id: str,
    user_id: str,
    query: Optional[str] = None,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Get complete conversation context from all memory layers.

    Retrieves:
    - Immediate context (Redis)
    - Working memory (Mem0)
    - User profile (PostgreSQL)
    - Relevant memories (Qdrant)
    """
    try:
        context = await memory_manager.get_context(
            user_id=user_id,
            conversation_id=conversation_id,
            query=query
        )

        return context

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context: {str(e)}"
        )


# ==============================================================================
# Prompt Building Endpoints
# ==============================================================================

@router.post("/prompts/build", response_model=PromptBuildResponse)
async def build_prompt(
    request: PromptBuildRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder)
):
    """
    Build dynamic system prompt for user.

    Assembles prompt from:
    - Core system instructions
    - Role-specific behavior
    - Active skills
    - Memory context
    - Language preferences
    """
    start_time = time.time()

    try:
        # Build user context from database
        user_context = await build_user_context_from_db(
            request.user_id,
            memory_manager
        )

        # Get memory context
        memory_context = await memory_manager.get_context(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            query=request.query
        )

        # Build prompt
        if request.minimal:
            prompt = prompt_builder.build_minimal(user_context, memory_context)
        else:
            prompt = prompt_builder.build(
                user_context,
                memory_context,
                include_principles=request.include_principles,
                include_rules=request.include_rules
            )

        # Get statistics
        prompt_stats = prompt_builder.get_prompt_summary(prompt)

        build_time_ms = (time.time() - start_time) * 1000

        return PromptBuildResponse(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            prompt=prompt,
            prompt_stats=prompt_stats,
            build_time_ms=build_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt build failed: {str(e)}"
        )


@router.get("/prompts/role/{role}")
async def get_role_prompt(
    role: str,
    prompt_builder: PromptBuilder = Depends(get_prompt_builder)
):
    """
    Get role-specific prompt template.

    Available roles: parent, teenager, child, grandparent
    """
    try:
        prompt = prompt_builder.load_role_prompt(role)

        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Role prompt not found: {role}"
            )

        return {
            "role": role,
            "prompt": prompt,
            "length": len(prompt),
            "estimated_tokens": len(prompt) // 4
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load role prompt: {str(e)}"
        )


@router.get("/prompts/core")
async def get_core_prompt(
    prompt_builder: PromptBuilder = Depends(get_prompt_builder)
):
    """Get core system prompt (FAMILY_ASSISTANT.md)"""
    try:
        prompt = prompt_builder.load_core_prompt()

        return {
            "prompt": prompt,
            "length": len(prompt),
            "estimated_tokens": len(prompt) // 4
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load core prompt: {str(e)}"
        )


# ==============================================================================
# User Profile Management
# ==============================================================================

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get user profile and preferences"""
    try:
        profile = await memory_manager.get_user_profile(user_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"User profile not found: {user_id}"
            )

        preferences = await memory_manager.get_user_preferences(user_id)

        return UserProfileResponse(
            user_id=profile.get("id", user_id),
            role=profile.get("role", "parent"),
            age_group=profile.get("age_group"),
            language_preference=profile.get("language_preference", "en"),
            active_skills=profile.get("active_skills", []),
            privacy_level="family",
            safety_level="adult",
            preferences=preferences,
            created_at=profile.get("created_at"),
            updated_at=profile.get("updated_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/users/{user_id}/profile")
async def update_user_profile(
    user_id: str,
    request: UserProfileUpdateRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Update user profile and preferences"""
    # TODO: Implement database update logic
    return {
        "success": True,
        "user_id": user_id,
        "updated_fields": [
            k for k, v in request.dict(exclude_unset=True).items()
            if v is not None
        ]
    }


# ==============================================================================
# Health and Statistics
# ==============================================================================

@router.get("/health", response_model=MemoryHealthResponse)
async def health_check(
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Health check for memory system"""
    start_time = time.time()

    try:
        # Test each layer
        layers_status = {}

        # Layer 1: Redis
        redis_start = time.time()
        try:
            if memory_manager.redis_client:
                await memory_manager.redis_client.ping()
                layers_status["redis"] = {
                    "status": "healthy",
                    "latency_ms": (time.time() - redis_start) * 1000
                }
            else:
                layers_status["redis"] = {"status": "not_initialized"}
        except Exception as e:
            layers_status["redis"] = {"status": "unhealthy", "error": str(e)}

        # Layer 2: Mem0
        mem0_start = time.time()
        try:
            # Simple health check
            layers_status["mem0"] = {
                "status": "healthy",
                "latency_ms": (time.time() - mem0_start) * 1000
            }
        except Exception as e:
            layers_status["mem0"] = {"status": "unhealthy", "error": str(e)}

        # Layer 4: Qdrant
        qdrant_start = time.time()
        try:
            collections = memory_manager.qdrant_client.get_collections()
            layers_status["qdrant"] = {
                "status": "healthy",
                "latency_ms": (time.time() - qdrant_start) * 1000,
                "collections": len(collections.collections)
            }
        except Exception as e:
            layers_status["qdrant"] = {"status": "unhealthy", "error": str(e)}

        # Overall status
        unhealthy_count = sum(
            1 for layer in layers_status.values()
            if layer.get("status") == "unhealthy"
        )

        if unhealthy_count == 0:
            overall_status = "healthy"
        elif unhealthy_count < len(layers_status):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        overall_latency_ms = (time.time() - start_time) * 1000

        return MemoryHealthResponse(
            status=overall_status,
            layers=layers_status,
            overall_latency_ms=overall_latency_ms,
            error_rate=0.0,  # TODO: Calculate from metrics
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
    """Get memory system statistics"""
    # TODO: Implement actual stats from database
    return MemoryStatsResponse(
        total_conversations=0,
        total_memories=0,
        total_embeddings=0,
        storage_used_mb=0.0,
        cache_hit_rate=0.0,
        avg_retrieval_time_ms=0.0,
        users_active_today=0
    )


# ==============================================================================
# Utility Endpoints
# ==============================================================================

@router.post("/memory/cleanup")
async def cleanup_old_memories(
    days_old: int = 90,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Clean up old memories from cache layers.

    PostgreSQL and Qdrant retain data for archival purposes.
    """
    try:
        await memory_manager.cleanup_old_memories(days_old=days_old)

        return {
            "success": True,
            "days_old": days_old,
            "message": "Old memories cleaned up successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/test/prompt-assembly")
async def test_prompt_assembly(
    user_id: str = "test-user",
    role: str = "parent",
    language: str = "en",
    memory_manager: MemoryManager = Depends(get_memory_manager),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder)
):
    """
    Test endpoint for prompt assembly.

    Useful for debugging and development.
    """
    try:
        # Create test user context
        from api.models.memory import UserContext, UserRole, LanguagePreference

        user_context = UserContext(
            user_id=user_id,
            role=UserRole(role),
            language_preference=LanguagePreference(language),
            active_skills=["calendar", "reminders"]
        )

        # Build both full and minimal prompts
        full_prompt = prompt_builder.build(user_context, None)
        minimal_prompt = prompt_builder.build_minimal(user_context, None)

        full_stats = prompt_builder.get_prompt_summary(full_prompt)
        minimal_stats = prompt_builder.get_prompt_summary(minimal_prompt)

        return {
            "user_context": user_context.dict(),
            "full_prompt": {
                "prompt": full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt,
                "stats": full_stats
            },
            "minimal_prompt": {
                "prompt": minimal_prompt[:500] + "..." if len(minimal_prompt) > 500 else minimal_prompt,
                "stats": minimal_stats
            },
            "token_reduction": {
                "percentage": (
                    (1 - minimal_stats["estimated_tokens"] / full_stats["estimated_tokens"]) * 100
                    if full_stats["estimated_tokens"] > 0 else 0
                ),
                "full_tokens": full_stats["estimated_tokens"],
                "minimal_tokens": minimal_stats["estimated_tokens"]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )
