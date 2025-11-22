"""
Mem0 API Service
FastAPI wrapper for Mem0 AI memory layer
Provides REST endpoints for memory operations with Ollama + Qdrant integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
from mem0 import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mem0 Memory Service",
    description="AI Memory Layer for Homelab Agentic Workflows",
    version="1.0.0"
)

# CORS middleware for N8n integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on security needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
# Environment configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://100.72.98.106:11434")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-dummy")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant.homelab.svc.cluster.local")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mem0_memories")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b-instruct-q4_K_M")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")

# Configure LLM
llm_config = {
    "model": LLM_MODEL,
    "temperature": 0.1,
}
if LLM_PROVIDER == "ollama":
    llm_config["ollama_base_url"] = OLLAMA_BASE_URL
elif LLM_PROVIDER == "openai":
    llm_config["openai_base_url"] = OPENAI_BASE_URL
    llm_config["api_key"] = OPENAI_API_KEY

# Configure Embedder
embedder_config = {
    "model": EMBEDDING_MODEL,
}
if EMBEDDING_PROVIDER == "ollama":
    embedder_config["ollama_base_url"] = OLLAMA_BASE_URL
elif EMBEDDING_PROVIDER == "openai":
    embedder_config["openai_base_url"] = OPENAI_BASE_URL
    embedder_config["api_key"] = OPENAI_API_KEY

# Mem0 configuration
mem0_config = {
    "llm": {
        "provider": LLM_PROVIDER,
        "config": llm_config
    },
    "embedder": {
        "provider": EMBEDDING_PROVIDER,
        "config": embedder_config
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": COLLECTION_NAME,
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
        }
    }
}

# Initialize Memory instance
try:
    memory = Memory.from_config(mem0_config)
    logger.info("Mem0 Memory initialized successfully")
    logger.info(f"LLM: {LLM_MODEL} @ {OLLAMA_BASE_URL}")
    logger.info(f"Embeddings: {EMBEDDING_MODEL}")
    logger.info(f"Vector Store: Qdrant @ {QDRANT_HOST}:{QDRANT_PORT}")
except Exception as e:
    logger.error(f"Failed to initialize Mem0: {e}")
    memory = None

# Request/Response Models
class AddMemoryRequest(BaseModel):
    messages: str = Field(..., description="Text content to store in memory")
    user_id: Optional[str] = Field(None, description="User identifier for scoped memories")
    agent_id: Optional[str] = Field(None, description="Agent identifier for scoped memories")
    run_id: Optional[str] = Field(None, description="Run/session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SearchMemoryRequest(BaseModel):
    query: str = Field(..., description="Search query for memory retrieval")
    user_id: Optional[str] = Field(None, description="User identifier for scoped search")
    agent_id: Optional[str] = Field(None, description="Agent identifier for scoped search")
    run_id: Optional[str] = Field(None, description="Run/session identifier")
    limit: int = Field(10, description="Maximum number of memories to return", ge=1, le=100)

class UpdateMemoryRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID to update")
    data: str = Field(..., description="New memory content")

class MemoryResponse(BaseModel):
    id: str
    memory: str
    metadata: Optional[Dict[str, Any]] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    return {
        "status": "healthy",
        "service": "mem0-api",
        "version": "1.0.0",
        "config": {
            "llm_model": LLM_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "vector_store": f"qdrant://{QDRANT_HOST}:{QDRANT_PORT}",
            "collection": COLLECTION_NAME
        }
    }

# Add memory endpoint
@app.post("/memories", response_model=Dict[str, Any])
async def add_memory(request: AddMemoryRequest):
    """
    Add a new memory

    Extracts and stores salient information from the provided text.
    Memories can be scoped to users, agents, or runs.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        result = memory.add(
            messages=request.messages,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            metadata=request.metadata
        )
        logger.info(f"Added memory: {result}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search memories endpoint
@app.post("/memories/search", response_model=Dict[str, Any])
async def search_memories(request: SearchMemoryRequest):
    """
    Search memories using semantic similarity

    Retrieves relevant memories based on the query and optional scoping.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        results = memory.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            limit=request.limit
        )
        logger.info(f"Search returned {len(results) if results else 0} memories")
        return {"success": True, "memories": results}
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all memories endpoint
@app.get("/memories", response_model=Dict[str, Any])
async def get_all_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None
):
    """
    Get all memories for a given scope

    Retrieves all stored memories, optionally filtered by user, agent, or run.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        results = memory.get_all(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id
        )
        logger.info(f"Retrieved {len(results) if results else 0} memories")
        return {"success": True, "memories": results}
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Update memory endpoint
@app.put("/memories/{memory_id}", response_model=Dict[str, Any])
async def update_memory(memory_id: str, data: str):
    """
    Update an existing memory

    Modifies the content of a stored memory.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        result = memory.update(memory_id=memory_id, data=data)
        logger.info(f"Updated memory {memory_id}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete memory endpoint
@app.delete("/memories/{memory_id}", response_model=Dict[str, Any])
async def delete_memory(memory_id: str):
    """
    Delete a memory

    Permanently removes a memory from storage.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        memory.delete(memory_id=memory_id)
        logger.info(f"Deleted memory {memory_id}")
        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory history endpoint
@app.get("/memories/{memory_id}/history", response_model=Dict[str, Any])
async def get_memory_history(memory_id: str):
    """
    Get update history for a memory

    Retrieves the modification history of a specific memory.
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        history = memory.history(memory_id=memory_id)
        logger.info(f"Retrieved history for memory {memory_id}")
        return {"success": True, "history": history}
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reset memories endpoint (use with caution!)
@app.post("/memories/reset", response_model=Dict[str, Any])
async def reset_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None
):
    """
    Reset (delete) all memories for a scope

    WARNING: This permanently deletes memories. Use with caution!
    """
    if memory is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")

    try:
        memory.reset(user_id=user_id, agent_id=agent_id, run_id=run_id)
        scope = f"user={user_id}, agent={agent_id}, run={run_id}"
        logger.warning(f"Reset memories for scope: {scope}")
        return {"success": True, "message": f"Memories reset for scope: {scope}"}
    except Exception as e:
        logger.error(f"Error resetting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
