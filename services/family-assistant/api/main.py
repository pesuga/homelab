"""FastAPI application for Family Assistant Agent."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncpg
from config.settings import settings
from agents.memory_agent import agent

# Initialize FastAPI app
app = FastAPI(
    title="Family Assistant API",
    description="Privacy-focused AI assistant with persistent memory",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    thread_id: str
    user_id: str
    memories_used: int


class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    name: str
    role: str
    age: int
    permissions: Dict[str, bool]
    preferences: Dict[str, Any]


# Database connection pool
async def get_db_pool():
    """Get database connection pool."""
    return await asyncpg.create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
        min_size=2,
        max_size=10
    )


db_pool = None


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    global db_pool
    db_pool = await get_db_pool()
    print(f"✅ Family Assistant API started on {settings.api_host}:{settings.api_port}")
    print(f"   - Ollama: {settings.ollama_base_url}")
    print(f"   - Mem0: {settings.mem0_api_url}")
    print(f"   - PostgreSQL: {settings.postgres_host}:{settings.postgres_port}")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    global db_pool
    if db_pool:
        await db_pool.close()
    print("👋 Family Assistant API shut down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Family Assistant API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ollama": settings.ollama_base_url,
        "mem0": settings.mem0_api_url,
        "postgres": f"{settings.postgres_host}:{settings.postgres_port}"
    }


@app.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get user profile."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1",
            user_id
        )

        if not row:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Parse JSON columns if they're strings
        import json
        permissions = row["permissions"]
        if isinstance(permissions, str):
            permissions = json.loads(permissions)

        preferences = row["preferences"]
        if isinstance(preferences, str):
            preferences = json.loads(preferences)

        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "role": row["role"],
            "age": row["age"],
            "permissions": permissions,
            "preferences": preferences
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the family assistant.

    The agent will:
    1. Retrieve relevant memories from past conversations
    2. Generate a response using Ollama with memory context
    3. Store the new conversation in Mem0

    All conversation state is persisted in PostgreSQL for resumption.
    """
    # Generate thread ID if not provided
    thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

    # Get user profile
    async with db_pool.acquire() as conn:
        user_profile = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1",
            request.user_id
        )

        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail=f"User {request.user_id} not found. Please create a user profile first."
            )

        profile_dict = {
            "name": user_profile["name"],
            "role": user_profile["role"],
            "age": user_profile["age"],
            "permissions": user_profile["permissions"],
            "preferences": user_profile["preferences"]
        }

    # Chat with agent
    try:
        result = await agent.chat(
            message=request.message,
            user_id=request.user_id,
            thread_id=thread_id,
            user_profile=profile_dict
        )

        # Log to conversation history
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_history (thread_id, user_id, role, content)
                VALUES ($1, $2, $3, $4), ($5, $6, $7, $8)
            """,
                thread_id, request.user_id, "user", request.message,
                thread_id, request.user_id, "assistant", result["response"]
            )

        return ChatResponse(
            response=result["response"],
            thread_id=thread_id,
            user_id=request.user_id,
            memories_used=result.get("memories_used", 0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with agent: {str(e)}")


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str, user_id: Optional[str] = None):
    """Get conversation history for a thread."""
    async with db_pool.acquire() as conn:
        if user_id:
            rows = await conn.fetch("""
                SELECT role, content, created_at
                FROM conversation_history
                WHERE thread_id = $1 AND user_id = $2
                ORDER BY created_at ASC
            """, thread_id, user_id)
        else:
            rows = await conn.fetch("""
                SELECT role, content, created_at
                FROM conversation_history
                WHERE thread_id = $1
                ORDER BY created_at ASC
            """, thread_id)

        return {
            "thread_id": thread_id,
            "messages": [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["created_at"].isoformat()
                }
                for row in rows
            ]
        }


@app.get("/users/{user_id}/conversations")
async def get_user_conversations(user_id: str, limit: int = 10):
    """Get all conversations for a user."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT thread_id, MIN(created_at) as started_at, MAX(created_at) as last_message_at
            FROM conversation_history
            WHERE user_id = $1
            GROUP BY thread_id
            ORDER BY last_message_at DESC
            LIMIT $2
        """, user_id, limit)

        return {
            "user_id": user_id,
            "conversations": [
                {
                    "thread_id": row["thread_id"],
                    "started_at": row["started_at"].isoformat(),
                    "last_message_at": row["last_message_at"].isoformat()
                }
                for row in rows
            ]
        }


# OpenAI-compatible API endpoints for LobeChat integration
class OpenAIChatMessage(BaseModel):
    """OpenAI chat message format."""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None


class OpenAIChatRequest(BaseModel):
    """OpenAI chat completion request."""
    model: str = "family-assistant"
    messages: list[OpenAIChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    user: Optional[str] = None  # user_id


class OpenAIChatResponse(BaseModel):
    """OpenAI chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Dict[str, Any]]
    usage: Dict[str, int]


@app.post("/v1/chat/completions", response_model=OpenAIChatResponse)
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    This allows LobeChat and other OpenAI-compatible clients to use
    the Family Assistant with full memory and context awareness.
    """
    import time

    # Extract user_id from request.user or default to "default"
    user_id = request.user or "default"

    # Get the last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    last_message = user_messages[-1].content

    # Generate thread_id from user_id
    thread_id = f"thread_{user_id}_{uuid.uuid4().hex[:8]}"

    # Get user profile
    async with db_pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1",
            user_id
        )

        if user_row:
            import json
            permissions = user_row["permissions"]
            if isinstance(permissions, str):
                permissions = json.loads(permissions)
            preferences = user_row["preferences"]
            if isinstance(preferences, str):
                preferences = json.loads(preferences)

            user_profile = {
                "user_id": user_row["user_id"],
                "name": user_row["name"],
                "role": user_row["role"],
                "age": user_row["age"],
                "permissions": permissions,
                "preferences": preferences
            }
        else:
            user_profile = None

        # Chat with agent
        result = await agent.chat(
            message=last_message,
            user_id=user_id,
            thread_id=thread_id,
            user_profile=user_profile
        )

        # Store in conversation history
        await conn.execute("""
            INSERT INTO conversation_history (thread_id, user_id, role, content)
            VALUES ($1, $2, $3, $4), ($5, $6, $7, $8)
        """, thread_id, user_id, "user", last_message,
             thread_id, user_id, "assistant", result["response"])

        # Audit log
        import json
        await conn.execute("""
            INSERT INTO audit_log (user_id, action, resource, details)
            VALUES ($1, $2, $3, $4::jsonb)
        """, user_id, "chat", "openai_api", json.dumps({"model": request.model, "thread_id": thread_id}))

    # Format as OpenAI response
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["response"]
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(last_message.split()),
            "completion_tokens": len(result["response"].split()),
            "total_tokens": len(last_message.split()) + len(result["response"].split())
        }
    }


@app.get("/v1/models")
async def openai_list_models():
    """
    OpenAI-compatible models list endpoint.

    Returns available models for LobeChat model selection.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "family-assistant",
                "object": "model",
                "created": 1699000000,
                "owned_by": "homelab",
                "permission": [],
                "root": "family-assistant",
                "parent": None
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level
    )
