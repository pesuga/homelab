"""
Memory Service

Integration with Mem0 for persistent family memories and knowledge management.
"""

import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class MemoryConfig(BaseModel):
    mem0_url: str = "http://localhost:30820"
    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    timeout: int = 30

class MemoryCreate(BaseModel):
    family_id: str
    category: str  # preference, schedule, event, knowledge, interaction
    title: str
    content: str
    importance: int = 5  # 1-10 importance score
    metadata: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None

class MemorySearch(BaseModel):
    family_id: str
    query: str
    category: Optional[str] = None
    limit: int = 10
    threshold: float = 0.7

class MemoryResponse(BaseModel):
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
    relevance_score: float = 0.0

class MemoryService:
    """Service for family memory management using Mem0."""

    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.mem0_url,
            timeout=self.config.timeout
        )

    async def health_check(self) -> bool:
        """Check if Mem0 service is available."""
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Mem0 health check failed: {e}")
            return False

    async def store_memory(self, memory: MemoryCreate) -> str:
        """Store a memory using Mem0."""
        try:
            # Prepare memory data for Mem0
            memory_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": memory.content
                    }
                ],
                "metadata": {
                    "family_id": memory.family_id,
                    "category": memory.category,
                    "title": memory.title,
                    "importance": memory.importance,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
                    **memory.metadata
                }
            }

            # Send to Mem0
            response = await self.client.post(
                "/v1/memories/",
                json=memory_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                memory_id = result.get("id") or result.get("memory_id")
                logger.info(f"Memory stored successfully: {memory_id}")
                return memory_id
            else:
                logger.error(f"Failed to store memory: {response.status_code} - {response.text}")
                raise Exception(f"Memory storage failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Memory storage error: {e}")
            raise

    async def search_memories(
        self,
        family_id: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using Mem0."""
        try:
            # Prepare search query
            search_data = {
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "metadata_filter": {
                    "family_id": family_id
                }
            }

            # Add category filter if specified
            if category:
                search_data["metadata_filter"]["category"] = category

            # Search Mem0
            response = await self.client.post(
                "/v1/memories/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                results = response.json()
                memories = results.get("results", [])

                # Format memories for response
                formatted_memories = []
                for memory in memories:
                    metadata = memory.get("metadata", {})
                    formatted_memories.append({
                        "id": memory.get("id"),
                        "content": memory.get("memory") or memory.get("content", ""),
                        "category": metadata.get("category"),
                        "title": metadata.get("title"),
                        "importance": metadata.get("importance", 5),
                        "created_at": metadata.get("created_at"),
                        "relevance_score": memory.get("score", 0.0),
                        "metadata": metadata
                    })

                return formatted_memories
            else:
                logger.error(f"Memory search failed: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return []

    async def get_family_memories(
        self,
        family_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get memories for a family, optionally filtered by category."""
        try:
            # Calculate date filter
            since_date = datetime.now() - timedelta(days=days_back)

            # Prepare query
            query_data = {
                "metadata_filter": {
                    "family_id": family_id,
                    "created_at": {"$gte": since_date.isoformat()}
                },
                "limit": limit
            }

            if category:
                query_data["metadata_filter"]["category"] = category

            # Get memories from Mem0
            response = await self.client.post(
                "/v1/memories/",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                results = response.json()
                memories = results.get("results", [])

                # Sort by importance and date
                memories.sort(key=lambda m: (
                    m.get("metadata", {}).get("importance", 0),
                    m.get("metadata", {}).get("created_at", "")
                ), reverse=True)

                return memories
            else:
                logger.error(f"Failed to get family memories: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Get family memories error: {e}")
            return []

    async def update_memory(
        self,
        memory_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        importance: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory."""
        try:
            update_data = {"id": memory_id}

            if title is not None:
                update_data["metadata"] = update_data.get("metadata", {})
                update_data["metadata"]["title"] = title

            if content is not None:
                update_data["messages"] = [{"role": "user", "content": content}]

            if importance is not None:
                update_data["metadata"] = update_data.get("metadata", {})
                update_data["metadata"]["importance"] = importance

            if metadata is not None:
                update_data["metadata"] = update_data.get("metadata", {})
                update_data["metadata"].update(metadata)

            update_data["metadata"]["updated_at"] = datetime.now().isoformat()

            response = await self.client.put(
                f"/v1/memories/{memory_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Memory updated successfully: {memory_id}")
                return True
            else:
                logger.error(f"Failed to update memory: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Memory update error: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        try:
            response = await self.client.delete(
                f"/v1/memories/{memory_id}",
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Memory deleted successfully: {memory_id}")
                return True
            else:
                logger.error(f"Failed to delete memory: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Memory deletion error: {e}")
            return False

    async def cleanup_expired_memories(self, family_id: str) -> int:
        """Clean up expired memories for a family."""
        try:
            # Get memories that have expired
            current_time = datetime.now()
            query_data = {
                "metadata_filter": {
                    "family_id": family_id,
                    "expires_at": {"$lte": current_time.isoformat()}
                }
            }

            response = await self.client.post(
                "/v1/memories/",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                results = response.json()
                expired_memories = results.get("results", [])

                # Delete expired memories
                deleted_count = 0
                for memory in expired_memories:
                    memory_id = memory.get("id")
                    if memory_id and await self.delete_memory(memory_id):
                        deleted_count += 1

                logger.info(f"Cleaned up {deleted_count} expired memories for family {family_id}")
                return deleted_count
            else:
                logger.error(f"Failed to get expired memories: {response.status_code}")
                return 0

        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
            return 0

    async def get_memory_statistics(self, family_id: str) -> Dict[str, Any]:
        """Get statistics about family memories."""
        try:
            # Get all memories for the family
            memories = await self.get_family_memories(family_id, limit=1000)

            # Calculate statistics
            total_memories = len(memories)
            categories = {}
            importance_distribution = {i: 0 for i in range(1, 11)}

            for memory in memories:
                metadata = memory.get("metadata", {})

                # Category distribution
                category = metadata.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1

                # Importance distribution
                importance = metadata.get("importance", 5)
                if 1 <= importance <= 10:
                    importance_distribution[importance] += 1

            # Get recent activity
            recent_memories = [m for m in memories if self._is_recent_memory(m)]
            recent_count = len(recent_memories)

            return {
                "total_memories": total_memories,
                "category_distribution": categories,
                "importance_distribution": importance_distribution,
                "recent_memories": recent_count,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Memory statistics error: {e}")
            return {}

    def _is_recent_memory(self, memory: Dict[str, Any]) -> bool:
        """Check if a memory is recent (within last 7 days)."""
        try:
            metadata = memory.get("metadata", {})
            created_at_str = metadata.get("created_at")

            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                seven_days_ago = datetime.now() - timedelta(days=7)
                return created_at > seven_days_ago

            return False
        except:
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()