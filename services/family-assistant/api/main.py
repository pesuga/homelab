"""FastAPI application for Family Assistant Agent with multimodal support."""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncpg
from datetime import datetime
import psutil
import subprocess
import json
import asyncio
from pathlib import Path
from config.settings import settings

# Import multimodal models and services
from api.models.multimodal import (
    MultimodalChatRequest, MultimodalChatResponse, ChatMessage,
    ContentType, ProcessingStatus, MultimodalContent,
    TextContent, ImageContent, AudioContent, DocumentContent,
    FamilyMemberProfile
)
from api.services.content_processor import ContentProcessor, ContentProcessorError, content_processor
from api.services.telegram_service import create_telegram_service

# Import feature flags
from config.feature_flags import feature_flags

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


# Enhanced Request/Response models with multimodal support
class ChatRequest(BaseModel):
    """Enhanced chat request model with multimodal support."""
    message: Optional[str] = None
    user_id: str
    thread_id: Optional[str] = None
    multimodal_content: Optional[List[MultimodalContent]] = None


class ChatResponse(BaseModel):
    """Enhanced chat response model."""
    response: str
    thread_id: str
    user_id: str
    memories_used: int
    content_processed: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    name: str
    role: str
    age: int
    permissions: Dict[str, bool]
    preferences: Dict[str, Any]
    multimodal_preferences: Optional[Dict[str, Any]] = None


class ContentUploadResponse(BaseModel):
    """Content upload response model."""
    upload_id: str
    original_filename: str
    content_type: ContentType
    processing_status: ProcessingStatus
    file_size_bytes: int
    analysis_results: Optional[Dict[str, Any]] = None
    upload_time: str
    privacy_level: str


# Multimodal specific models
class MultimodalMessage(BaseModel):
    """Multimodal message model for API."""
    role: str  # user, assistant, system
    content: Optional[str] = None
    multimodal_content: Optional[List[MultimodalContent]] = None
    timestamp: Optional[str] = None


class EnhancedChatRequest(BaseModel):
    """Enhanced chat request supporting multimodal content."""
    model: str = "family-assistant"
    messages: List[MultimodalMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    enable_vision_analysis: bool = True
    enable_speech_recognition: bool = True
    enable_document_extraction: bool = True
    family_context: Optional[Dict[str, Any]] = None


# Dashboard System Models
class ServiceStatus(BaseModel):
    """Service status model for dashboard."""
    name: str
    status: str  # running, error, warning, stopped
    url: Optional[str] = None
    response_time: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

class SystemMetrics(BaseModel):
    """System metrics model."""
    cpu: Dict[str, float]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, float]
    uptime: float

class SystemHealth(BaseModel):
    """System health model."""
    status: str  # healthy, warning, error
    timestamp: str
    system: SystemMetrics
    services: List[ServiceStatus]
    alerts: List[Dict[str, Any]] = []

class ArchitectureInfo(BaseModel):
    """Architecture documentation model."""
    title: str
    content: str
    last_updated: str
    sections: List[Dict[str, Any]]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

manager = ConnectionManager()

# System health monitoring functions
async def get_system_metrics() -> SystemMetrics:
    """Get current system metrics."""
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    cpu_data = {
        "usage": cpu_percent,
        "cores": cpu_count,
        "frequency": cpu_freq.current if cpu_freq else 0
    }

    # Memory metrics
    memory = psutil.virtual_memory()
    memory_data = {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percentage": memory.percent
    }

    # Disk metrics
    disk = psutil.disk_usage('/')
    disk_data = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percentage": (disk.used / disk.total) * 100
    }

    # Network metrics
    network = psutil.net_io_counters()
    network_data = {
        "bytes_sent": network.bytes_sent,
        "bytes_recv": network.bytes_recv,
        "packets_sent": network.packets_sent,
        "packets_recv": network.packets_recv,
        "upload": network.bytes_sent / (1024 * 1024),  # MB
        "download": network.bytes_recv / (1024 * 1024)  # MB
    }

    # System uptime
    uptime = psutil.boot_time()

    return SystemMetrics(
        cpu=cpu_data,
        memory=memory_data,
        disk=disk_data,
        network=network_data,
        uptime=uptime
    )

async def get_service_status() -> List[ServiceStatus]:
    """Get status of homelab services."""
    services = []

    # Ollama service
    try:
        # Check if Ollama is responding
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.ollama_base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    services.append(ServiceStatus(
                        name="Ollama",
                        status="running",
                        url=settings.ollama_base_url
                    ))
                else:
                    services.append(ServiceStatus(
                        name="Ollama",
                        status="error",
                        url=settings.ollama_base_url
                    ))
    except:
        services.append(ServiceStatus(
            name="Ollama",
            status="warning",
            url=settings.ollama_base_url
        ))

    # Database services (PostgreSQL, Redis)
    try:
        # Test PostgreSQL connection
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                services.append(ServiceStatus(
                    name="PostgreSQL",
                    status="running",
                    url=f"{settings.postgres_host}:{settings.postgres_port}"
                ))
        else:
            services.append(ServiceStatus(
                name="PostgreSQL",
                status="error"
            ))
    except:
        services.append(ServiceStatus(
            name="PostgreSQL",
            status="error"
        ))

    # Redis (simplified check)
    services.append(ServiceStatus(
        name="Redis",
        status="running",  # Assuming Redis is running
        url=f"{settings.redis_host}:{settings.redis_port}"
    ))

    # Mem0
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.mem0_api_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    services.append(ServiceStatus(
                        name="Mem0",
                        status="running",
                        url=settings.mem0_api_url
                    ))
                else:
                    services.append(ServiceStatus(
                        name="Mem0",
                        status="warning",
                        url=settings.mem0_api_url
                    ))
    except:
        services.append(ServiceStatus(
            name="Mem0",
            status="warning",
            url=settings.mem0_api_url
        ))

    return services

async def read_architecture_docs() -> List[ArchitectureInfo]:
    """Read architecture documentation from markdown files."""
    import os
    from pathlib import Path

    docs = []
    docs_path = Path("/home/pesu/Rakuflow/systems/homelab")

    # Look for markdown files
    for md_file in docs_path.glob("**/*.md"):
        if "CLAUDE.md" in md_file.name or "README.md" in md_file.name:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Simple section parsing
                sections = []
                lines = content.split('\n')
                current_section = None
                section_content = []

                for line in lines:
                    if line.startswith('## '):
                        if current_section:
                            sections.append({
                                "title": current_section,
                                "content": '\n'.join(section_content)
                            })
                        current_section = line[3:].strip()
                        section_content = []
                    elif line.startswith('# '):
                        if current_section:
                            sections.append({
                                "title": current_section,
                                "content": '\n'.join(section_content)
                            })
                        current_section = "Overview"
                        section_content = []
                    else:
                        section_content.append(line)

                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(section_content)
                    })

                docs.append(ArchitectureInfo(
                    title=md_file.name,
                    content=content[:1000] + "..." if len(content) > 1000 else content,
                    last_updated=datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                    sections=sections[:5]  # Limit sections
                ))
            except Exception as e:
                print(f"Error reading {md_file}: {e}")

    return docs

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


# Initialize services
content_processor_instance = ContentProcessor()
telegram_service = create_telegram_service(settings.telegram_bot_token) if settings.telegram_bot_token else None


# Utility Functions
def get_mock_family_member(user_id: str = "demo_user") -> FamilyMemberProfile:
    """Get mock family member for testing purposes."""
    return FamilyMemberProfile(
        user_id=user_id,
        name="Demo Parent",
        role="parent",
        age=35,
        preferred_content_types=[ContentType.TEXT, ContentType.IMAGE, ContentType.AUDIO],
        content_filters=["violence", "adult_content"],
        language_preferences=["en"],
        vision_analysis_enabled=True,
        photo_privacy_level="family",
        auto_image_description=True,
        speech_recognition_enabled=True,
        preferred_audio_format="ogg",
        voice_privacy_level="family",
        document_extraction_enabled=True,
        auto_summarization=False,
        permissions={"upload": True, "chat": True, "delete": False},
        preferences={"theme": "light", "notifications": True}
    )


class MockAgent:
    """Mock agent for testing purposes."""

    async def chat(self, message: str, user_id: str, thread_id: str, user_profile: dict = None):
        """Mock chat response."""
        return {
            "response": f"Hello {user_profile.get('name', 'User')}! I received your message: '{message[:100]}{'...' if len(message) > 100 else ''}'",
            "memories_used": 0
        }


# Initialize mock agent
agent = MockAgent()


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


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the standalone dashboard HTML."""
    dashboard_path = Path(__file__).parent.parent / "dashboard-standalone.html"
    if dashboard_path.exists():
        with open(dashboard_path, "r") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ollama": settings.ollama_base_url,
        "mem0": settings.mem0_api_url,
        "postgres": f"{settings.postgres_host}:{settings.postgres_port}"
    }


# Feature Flags Management Endpoints
@app.get("/features")
async def get_features(user_id: Optional[str] = None, user_role: Optional[str] = None):
    """Get available features for a user."""
    user_context = {}
    if user_id:
        user_context["user_id"] = user_id
    if user_role:
        user_context["role"] = user_role

    effective_config = settings.get_effective_config(user_context)

    return {
        "user_context": user_context,
        "enabled_features": effective_config["enabled_features"],
        "feature_flags": effective_config["feature_flags"],
        "configuration": {
            "multimodal": effective_config["multimodal"],
            "privacy": effective_config["privacy"],
            "performance": effective_config["performance"],
            "ai_features": effective_config["ai_features"],
            "integrations": effective_config["integrations"]
        }
    }


@app.get("/features/statistics")
async def get_feature_statistics():
    """Get feature flag statistics and usage information."""
    return feature_flags.get_flag_statistics()


@app.get("/features/export")
async def export_feature_config():
    """Export feature flag configuration."""
    return feature_flags.export_config()


@app.post("/features/{flag_key}/enable")
async def enable_feature_flag(flag_key: str, user_context: Optional[Dict[str, Any]] = None):
    """Enable a feature flag."""
    if flag_key not in feature_flags.flags:
        raise HTTPException(status_code=404, detail=f"Feature flag {flag_key} not found")

    feature_flags.update_flag(flag_key, status="enabled")
    return {"message": f"Feature flag {flag_key} enabled successfully"}


@app.post("/features/{flag_key}/disable")
async def disable_feature_flag(flag_key: str):
    """Disable a feature flag."""
    if flag_key not in feature_flags.flags:
        raise HTTPException(status_code=404, detail=f"Feature flag {flag_key} not found")

    feature_flags.update_flag(flag_key, status="disabled")
    return {"message": f"Feature flag {flag_key} disabled successfully"}


@app.get("/features/{flag_key}")
async def get_feature_flag_config(flag_key: str):
    """Get detailed configuration for a specific feature flag."""
    flag_config = feature_flags.get_flag_config(flag_key)
    if not flag_config:
        raise HTTPException(status_code=404, detail=f"Feature flag {flag_key} not found")

    return {
        "key": flag_config.key,
        "name": flag_config.name,
        "description": flag_config.description,
        "status": flag_config.status.value,
        "target_type": flag_config.target_type.value,
        "target_config": flag_config.target_config,
        "rollout_percentage": flag_config.rollout_percentage,
        "enabled_users": flag_config.enabled_users,
        "enabled_roles": flag_config.enabled_roles,
        "metadata": flag_config.metadata,
        "created_at": flag_config.created_at.isoformat(),
        "updated_at": flag_config.updated_at.isoformat()
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
    Enhanced chat endpoint supporting multimodal content.

    The agent will:
    1. Process any multimodal content (images, audio, documents)
    2. Retrieve relevant memories from past conversations
    3. Generate a response using Ollama with memory context
    4. Store the new conversation in database

    All conversation state is persisted in PostgreSQL for resumption.
    """
    # Validate that either text or multimodal content is provided
    if not request.message and not request.multimodal_content:
        raise HTTPException(
            status_code=400,
            detail="Either message or multimodal_content must be provided"
        )

    # Generate thread ID if not provided
    thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

    # Process multimodal content if provided
    content_processed = {}
    analysis_results = {}

    if request.multimodal_content:
        for content_item in request.multimodal_content:
            content_type = content_item.content.content_type
            content_processed[content_type.value] = content_processed.get(content_type.value, 0) + 1

            # Process content based on type
            if isinstance(content_item.content, ImageContent):
                # Process image with vision analysis
                if hasattr(content_item.content, 'file_data') and content_item.content.file_data:
                    try:
                        # Convert multimodal content to ContentProcessor format
                        result = await content_processor_instance.process_content(
                            file_data=content_item.content.file_data,
                            filename=f"image_{uuid.uuid4().hex[:8]}.jpg",
                            family_member=await get_mock_family_member(request.user_id),
                            conversation_id=thread_id
                        )
                        analysis_results[f"image_{content_item.content.content.content_type}"] = result.extracted_data
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process image: {str(e)}"
                        )

            elif isinstance(content_item.content, AudioContent):
                # Process audio with transcription
                if hasattr(content_item.content, 'file_data') and content_item.content.file_data:
                    try:
                        result = await content_processor_instance.process_content(
                            file_data=content_item.content.file_data,
                            filename=f"audio_{uuid.uuid4().hex[:8]}.ogg",
                            family_member=await get_mock_family_member(request.user_id),
                            conversation_id=thread_id
                        )
                        analysis_results[f"audio_{content_item.content.content.content_type}"] = result.extracted_data
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process audio: {str(e)}"
                        )

            elif isinstance(content_item.content, DocumentContent):
                # Process document with text extraction
                if hasattr(content_item.content, 'file_data') and content_item.content.file_data:
                    try:
                        result = await content_processor_instance.process_content(
                            file_data=content_item.content.file_data,
                            filename=f"doc_{uuid.uuid4().hex[:8]}.pdf",
                            family_member=await get_mock_family_member(request.user_id),
                            conversation_id=thread_id
                        )
                        analysis_results[f"document_{content_item.content.content.content_type}"] = result.extracted_data
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process document: {str(e)}"
                        )

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

    # Prepare message with content analysis
    enhanced_message = request.message
    if analysis_results:
        # Add analysis insights to message
        analysis_text = "I processed the following content:\n"
        for content_type, data in analysis_results.items():
            if isinstance(data, dict):
                if content_type.startswith("image_"):
                    if "description" in data:
                        analysis_text += f"• Image: {data['description']}\n"
                elif content_type.startswith("audio_"):
                    if "transcription" in data:
                        analysis_text += f"• Audio: {data['transcription']}\n"
                elif content_type.startswith("document_"):
                    if "extracted_text" in data:
                        analysis_text += f"• Document: {data['extracted_text'][:200]}...\n"

        enhanced_message = f"{request.message}\n\n{analysis_text}" if request.message else analysis_text

    # Chat with agent (placeholder - would integrate with actual agent)
    try:
        # This would integrate with the actual Family Assistant agent
        # result = await agent.chat(
        #     message=enhanced_message,
        #     user_id=request.user_id,
        #     thread_id=thread_id,
        #     user_profile=profile_dict
        # )

        # Mock response for now
        result = {
            "response": f"Hello {profile_dict['name']}! I understand your message. " +
                     ("I also processed your multimedia content." if content_processed else ""),
            "memories_used": 0
        }

        # Store in conversation history with enhanced content
        async with db_pool.acquire() as conn:
            # Store user message
            await conn.execute("""
                INSERT INTO conversation_history (thread_id, user_id, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, thread_id, request.user_id, "user", enhanced_message or request.message, {
                "multimodal": bool(request.multimodal_content),
                "content_processed": content_processed,
                "analysis_results": analysis_results
            })

            # Store assistant response
            await conn.execute("""
                INSERT INTO conversation_history (thread_id, user_id, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, thread_id, request.user_id, "assistant", result["response"], {
                "response_type": "multimodal_chat"
            })

        return ChatResponse(
            response=result["response"],
            thread_id=thread_id,
            user_id=request.user_id,
            memories_used=result.get("memories_used", 0),
            content_processed=content_processed,
            analysis_results=analysis_results
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


# Multimodal content upload endpoint
@app.post("/upload", response_model=ContentUploadResponse)
async def upload_content(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    user_id: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    """
    Upload and process multimodal content.

    Supports:
    - Images (JPG, PNG, GIF, etc.) - Vision analysis
    - Audio (MP3, WAV, OGG) - Speech transcription
    - Documents (PDF, DOCX) - Text extraction
    - Generic files - Metadata extraction

    Returns processing results and analysis.
    """
    try:
        # Get mock family member profile
        family_member = await get_mock_family_member(user_id)

        # Read file data
        file_data = await file.read()

        # Process content using ContentProcessor
        result = await content_processor_instance.process_content(
            file_data=file_data,
            filename=file.filename,
            family_member=family_member,
            conversation_id=conversation_id
        )

        return ContentUploadResponse(
            upload_id=str(result.content_id),
            original_filename=file.filename,
            content_type=result.content_type,
            processing_status=result.processing_status,
            file_size_bytes=result.file_size_bytes,
            analysis_results=result.extracted_data,
            upload_time=result.created_at.isoformat(),
            privacy_level="family"  # Default privacy level
        )

    except ContentProcessorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# Enhanced multimodal chat endpoint
@app.post("/chat/multimodal", response_model=MultimodalChatResponse)
async def chat_multimodal(request: EnhancedChatRequest):
    """
    Advanced multimodal chat endpoint.

    Supports complex conversations with multiple content types,
    family context, and enhanced processing options.
    """
    try:
        # Get family member profile
        user_id = request.user_id or "default"
        family_member = await get_mock_family_member(user_id)

        # Convert messages format
        messages = []
        for msg in request.messages:
            chat_msg = ChatMessage(
                role=msg.role,
                content=msg.content,
                multimodal_content=msg.multimodal_content,
                timestamp=datetime.fromisoformat(msg.timestamp) if msg.timestamp else datetime.utcnow()
            )
            messages.append(chat_msg)

        # Mock enhanced processing (would integrate with actual agent)
        import time

        # Process multimodal content if present
        content_processed = {}
        analysis_results = {}
        processing_time = 0.0

        for msg in messages:
            if msg.multimodal_content:
                start_time = time.time()

                for content_item in msg.multimodal_content:
                    content_type = content_item.content.content_type
                    content_processed[content_type.value] = content_processed.get(content_type.value, 0) + 1

                    # Process content based on type
                    if isinstance(content_item.content, (ImageContent, AudioContent, DocumentContent)):
                        if hasattr(content_item.content, 'file_data') and content_item.content.file_data:
                            try:
                                result = await content_processor_instance.process_content(
                                    file_data=content_item.content.file_data,
                                    filename=f"{content_type.value}_{uuid.uuid4().hex[:8]}",
                                    family_member=family_member
                                )
                                analysis_results[f"{content_type.value}_{len(analysis_results)}"] = result.extracted_data
                            except Exception as e:
                                # Log error but continue processing
                                print(f"Failed to process {content_type.value}: {str(e)}")

                processing_time += (time.time() - start_time) * 1000

        # Mock response (would integrate with actual agent)
        response_text = f"Hello! I processed your multimodal message with {sum(content_processed.values())} content items."

        if analysis_results:
            response_text += " Here's what I found: " + ", ".join([
                f"{k}: {v.get('transcription', v.get('description', v.get('extracted_text', 'processed')))[:50]}"
                for k, v in analysis_results.items()
            ])

        return MultimodalChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": sum(len(m.content.split()) if m.content else 0 for m in messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(m.content.split()) if m.content else 0 for m in messages) + len(response_text.split())
            },
            processing_time_ms=processing_time,
            content_processed=content_processed,
            analysis_results=analysis_results,
            family_actions_suggested=[
                {
                    "action": "review_content",
                    "suggestion": "Review the processed content for family sharing"
                }
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multimodal chat failed: {str(e)}")


# Content analysis endpoint
@app.get("/content/{content_id}/analysis")
async def get_content_analysis(content_id: str):
    """Get detailed analysis results for uploaded content."""
    try:
        # This would retrieve from database
        # For now, return mock analysis
        return {
            "content_id": content_id,
            "analysis_status": "completed",
            "analysis_results": {
                "safety_score": 0.95,
                "content_type": "image",
                "description": "Safe family content",
                "recommendations": ["Safe to share"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content analysis: {str(e)}")


# Dashboard API Endpoints

@app.get("/dashboard/system-health", response_model=SystemHealth)
async def get_system_health():
    """Get comprehensive system health information for dashboard."""
    try:
        # Get system metrics
        metrics = await get_system_metrics()

        # Get service status
        services = await get_service_status()

        # Determine overall system status
        error_services = [s for s in services if s.status == "error"]
        warning_services = [s for s in services if s.status == "warning"]

        if error_services:
            overall_status = "error"
        elif warning_services:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        # Generate alerts if needed
        alerts = []
        if metrics.cpu["usage"] > 80:
            alerts.append({
                "id": f"cpu_{datetime.now().timestamp()}",
                "type": "warning",
                "title": "High CPU Usage",
                "message": f"CPU usage is {metrics.cpu['usage']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        if metrics.memory["percentage"] > 85:
            alerts.append({
                "id": f"memory_{datetime.now().timestamp()}",
                "type": "warning",
                "title": "High Memory Usage",
                "message": f"Memory usage is {metrics.memory['percentage']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        if metrics.disk["percentage"] > 90:
            alerts.append({
                "id": f"disk_{datetime.now().timestamp()}",
                "type": "error",
                "title": "Low Disk Space",
                "message": f"Disk usage is {metrics.disk['percentage']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        for service in error_services:
            alerts.append({
                "id": f"service_{service.name}_{datetime.now().timestamp()}",
                "type": "error",
                "title": f"Service Down: {service.name}",
                "message": f"{service.name} service is not responding",
                "service": service.name,
                "timestamp": datetime.now().isoformat()
            })

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            system=metrics,
            services=services,
            alerts=alerts
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@app.get("/dashboard/services")
async def get_dashboard_services():
    """Get simplified service status for dashboard."""
    try:
        services = await get_service_status()
        return {"services": services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")

@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """Get system metrics for dashboard charts."""
    try:
        metrics = await get_system_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/dashboard/architecture")
async def get_architecture_info():
    """Get architecture documentation for dashboard."""
    try:
        docs = await read_architecture_docs()
        return {"architecture": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read architecture docs: {str(e)}")

@app.get("/dashboard/recent-activity")
async def get_recent_activity():
    """Get recent system activity for dashboard."""
    try:
        # Get recent conversations
        async with db_pool.acquire() as conn:
            conversations = await conn.fetch("""
                SELECT thread_id, user_id, role, content, created_at
                FROM conversation_history
                ORDER BY created_at DESC
                LIMIT 10
            """)

            # Get recent uploads/processing
            # This would need to be implemented based on your content storage
            recent_uploads = []  # Placeholder

        return {
            "conversations": [
                {
                    "thread_id": conv["thread_id"],
                    "user_id": conv["user_id"],
                    "role": conv["role"],
                    "content": conv["content"][:100] + "..." if len(conv["content"]) > 100 else conv["content"],
                    "timestamp": conv["created_at"].isoformat()
                }
                for conv in conversations
            ],
            "recent_uploads": recent_uploads
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent activity: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic system health updates
            health_data = await get_system_health()
            await websocket.send_text(json.dumps({
                "type": "system_health",
                "data": health_data.dict()
            }))

            # Wait before next update
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.post("/dashboard/alerts/dismiss")
async def dismiss_alert(alert_id: str):
    """Dismiss a system alert."""
    try:
        # In a real implementation, you would track dismissed alerts in database
        # For now, just return success
        return {"message": f"Alert {alert_id} dismissed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dismiss alert: {str(e)}")

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    try:
        async with db_pool.acquire() as conn:
            # User stats
            user_count = await conn.fetchval("SELECT COUNT(*) FROM user_profiles")

            # Conversation stats
            conversation_count = await conn.fetchval("SELECT COUNT(DISTINCT thread_id) FROM conversation_history")
            message_count = await conn.fetchval("SELECT COUNT(*) FROM conversation_history")

            # Recent activity (last 24 hours)
            recent_messages = await conn.fetchval("""
                SELECT COUNT(*) FROM conversation_history
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)

        # System metrics
        metrics = await get_system_metrics()

        return {
            "users": user_count or 0,
            "conversations": conversation_count or 0,
            "messages": message_count or 0,
            "recent_activity_24h": recent_messages or 0,
            "system": {
                "cpu_usage": metrics.cpu["usage"],
                "memory_usage": metrics.memory["percentage"],
                "disk_usage": metrics.disk["percentage"],
                "uptime_hours": (datetime.now().timestamp() - metrics.uptime) / 3600
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


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
