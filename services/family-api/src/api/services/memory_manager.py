"""
Memory Manager - Five-Layer Memory Architecture

Orchestrates memory across:
- Layer 1: Redis (Hot Cache) - Immediate conversation context
- Layer 2: Mem0 (Working Memory) - Session-aware semantic memory
- Layer 3: PostgreSQL (Structured Data) - Relational family data
- Layer 4: Qdrant (Vector Search) - Semantic memory retrieval
- Layer 5: Persistent Storage (Archive) - Long-term historical data
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import redis.asyncio as redis
from pydantic import BaseModel
from config.settings import settings

# Import database client (assuming exists from existing code)
try:
    from api.database import get_db_connection
except ImportError:
    # Fallback for development
    get_db_connection = None


class MemoryContext(BaseModel):
    """Memory context retrieved from all layers"""
    user_id: str
    conversation_id: str
    immediate_context: List[Dict[str, Any]] = []  # Layer 1: Redis
    working_memory: List[Dict[str, Any]] = []     # Layer 2: Mem0
    structured_data: Dict[str, Any] = {}          # Layer 3: PostgreSQL
    semantic_memories: List[Dict[str, Any]] = []  # Layer 4: Qdrant
    conversation_summary: Optional[str] = None
    user_preferences: Dict[str, Any] = {}


class UserContext(BaseModel):
    """User context for prompt building"""
    user_id: str
    role: str  # parent, teenager, child, grandparent
    age_group: Optional[str] = None
    language_preference: str = "en"
    active_skills: List[str] = []
    privacy_level: str = "family"


class MemoryManager:
    """Orchestrates five-layer memory architecture"""

    def __init__(
        self,
        redis_url: str = "redis://redis.homelab.svc.cluster.local:6379",
        mem0_url: str = "http://mem0.homelab.svc.cluster.local:8080",
        qdrant_url: str = "http://qdrant.homelab.svc.cluster.local:6333",
        ollama_url: str = "http://llamacpp-service.default.svc.cluster.local:8081"
    ):
        # Layer 1: Redis client
        self.redis_client = None  # Initialized async
        self.redis_url = redis_url

        # Layer 2: Mem0 client
        self.mem0_client = httpx.AsyncClient(base_url=mem0_url, timeout=30.0)

        # Layer 3: PostgreSQL (using existing connection)
        self.db_connection = get_db_connection

        # Layer 4: Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url)

        # Ollama for embeddings
        self.ollama_client = httpx.AsyncClient(base_url=ollama_url, timeout=60.0)

        # Memory TTLs
        self.REDIS_TTL = 3600  # 1 hour
        self.MEM0_TTL = 86400  # 24 hours

    async def initialize(self):
        """Initialize async clients"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        # Initialize Qdrant collections if they don't exist
        await self._initialize_qdrant_collections()
        
        # Ensure database tables exist
        await self._ensure_tables_exist()

    async def _initialize_qdrant_collections(self):
        """Create Qdrant collections for family memories"""
        collections = ["family_memories", "family_knowledge"]

        for collection_name in collections:
            try:
                self.qdrant_client.get_collection(collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=768,  # nomic-embed-text dimension
                        distance=Distance.COSINE
                    )
                )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama (nomic-embed-text)"""
        try:
            response = await self.ollama_client.post(
                "/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
            )
            result = response.json()
            return result["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 768

    # =========================================================================
    # Layer 1: Redis (Hot Cache) - Immediate Conversation Context
    # =========================================================================

    async def get_immediate_context(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get immediate conversation context from Redis"""
        if not self.redis_client:
            return []

        key = f"conversation:{conversation_id}:messages"
        messages = await self.redis_client.lrange(key, 0, limit - 1)

        return [json.loads(msg) for msg in messages]

    async def save_to_redis(
        self,
        conversation_id: str,
        message: Dict[str, Any]
    ):
        """Save message to Redis hot cache"""
        if not self.redis_client:
            return

        key = f"conversation:{conversation_id}:messages"
        await self.redis_client.lpush(key, json.dumps(message))
        await self.redis_client.ltrim(key, 0, 99)  # Keep last 100 messages
        await self.redis_client.expire(key, self.REDIS_TTL)

    async def cache_user_context(
        self,
        user_id: str,
        context: Dict[str, Any]
    ):
        """Cache user context in Redis"""
        if not self.redis_client:
            return

        key = f"user:{user_id}:context"
        await self.redis_client.set(
            key,
            json.dumps(context),
            ex=self.REDIS_TTL
        )

    async def get_cached_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user context from Redis"""
        if not self.redis_client:
            return None

        key = f"user:{user_id}:context"
        data = await self.redis_client.get(key)

        return json.loads(data) if data else None

    # =========================================================================
    # Layer 2: Mem0 (Working Memory) - Session-Aware Semantic Memory
    # =========================================================================

    async def add_to_mem0(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add memory to Mem0 working memory"""
        try:
            response = await self.mem0_client.post(
                "/v1/memories/",
                json={
                    "user_id": user_id,
                    "messages": messages,
                    "metadata": metadata or {}
                }
            )
            return response.json()
        except Exception as e:
            print(f"Error adding to Mem0: {e}")
            return None

    async def search_mem0(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search Mem0 working memory"""
        try:
            response = await self.mem0_client.post(
                "/v1/memories/search/",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                }
            )
            return response.json().get("memories", [])
        except Exception as e:
            print(f"Error searching Mem0: {e}")
            return []

    async def get_mem0_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all Mem0 memories for user"""
        try:
            response = await self.mem0_client.get(
                f"/v1/memories/?user_id={user_id}"
            )
            return response.json().get("memories", [])
        except Exception as e:
            print(f"Error getting Mem0 memories: {e}")
            return []

    # =========================================================================
    # Layer 3: PostgreSQL (Structured Data) - Relational Family Data
    # =========================================================================

    async def _ensure_tables_exist(self):
        """Ensure necessary tables exist"""
        from api.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            try:
                # Family Members table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS family_members (
                        id TEXT PRIMARY KEY,
                        role TEXT NOT NULL,
                        age_group TEXT,
                        language_preference TEXT DEFAULT 'en',
                        active_skills TEXT[] DEFAULT '{}',
                        preferences JSONB DEFAULT '{}'::jsonb,
                        first_name TEXT,
                        last_name TEXT,
                        nickname TEXT,
                        email TEXT,
                        phone TEXT,
                        bio TEXT,
                        social_links JSONB DEFAULT '{}'::jsonb,
                        address JSONB DEFAULT '{}'::jsonb,
                        date_of_birth TIMESTAMP,
                        job_title TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))

                # Add columns if they don't exist (for existing deployments)
                await session.execute(text("""
                    ALTER TABLE family_members 
                    ADD COLUMN IF NOT EXISTS first_name TEXT,
                    ADD COLUMN IF NOT EXISTS last_name TEXT,
                    ADD COLUMN IF NOT EXISTS nickname TEXT,
                    ADD COLUMN IF NOT EXISTS email TEXT,
                    ADD COLUMN IF NOT EXISTS phone TEXT,
                    ADD COLUMN IF NOT EXISTS bio TEXT,
                    ADD COLUMN IF NOT EXISTS social_links JSONB DEFAULT '{}'::jsonb,
                    ADD COLUMN IF NOT EXISTS address JSONB DEFAULT '{}'::jsonb,
                    ADD COLUMN IF NOT EXISTS date_of_birth TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS job_title TEXT;
                """))
                
                # User Preferences table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id TEXT PRIMARY KEY REFERENCES family_members(id),
                        preferences JSONB DEFAULT '{}'::jsonb,
                        prompt_style TEXT,
                        response_length TEXT,
                        safety_level TEXT,
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Conversation Memory table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS conversation_memory (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT,
                        conversation_id TEXT,
                        message_type TEXT,
                        content TEXT,
                        embedding VECTOR(768),
                        metadata JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                await session.commit()
            except Exception as e:
                print(f"Error creating tables: {e}")
                await session.rollback()

    async def save_conversation_to_db(
        self,
        user_id: str,
        conversation_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save conversation to PostgreSQL"""
        from api.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            try:
                # Generate embedding for semantic search
                embedding = await self.generate_embedding(content)
                
                query = text("""
                INSERT INTO conversation_memory
                (user_id, conversation_id, message_type, content, embedding, metadata)
                VALUES (:user_id, :conversation_id, :message_type, :content, :embedding, :metadata)
                """)
                
                await session.execute(query, {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "message_type": message_type,
                    "content": content,
                    "embedding": str(embedding), # pgvector expects string or list
                    "metadata": json.dumps(metadata or {})
                })
                await session.commit()
            except Exception as e:
                print(f"Error saving to DB: {e}")
                await session.rollback()

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from PostgreSQL"""
        from api.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                SELECT 
                    id, role, age_group, language_preference, active_skills, preferences,
                    first_name, last_name, nickname, email, phone, bio, social_links, address,
                    date_of_birth, job_title,
                    created_at, updated_at
                FROM family_members
                WHERE id = :user_id
                """)
                
                result = await session.execute(query, {"user_id": user_id})
                row = result.mappings().first()
                
                if not row:
                    # Create default profile if not exists
                    default_role = "parent"  # Default to parent
                    await session.execute(
                        text("""
                            INSERT INTO family_members (id, role)
                            VALUES (:id, :role)
                        """),
                        {"id": user_id, "role": default_role}
                    )
                    await session.commit()
                    return {
                        "id": user_id,
                        "role": default_role,
                        "active_skills": [],
                        "preferences": {}
                    }
                    
                return dict(row)
                
            except Exception as e:
                print(f"Error getting user profile: {e}")
                # Fallback
                return {
                    "id": user_id,
                    "role": "parent",
                    "language_preference": "en",
                    "active_skills": []
                }

    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile in PostgreSQL"""
        from api.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            try:
                # Build update query dynamically
                set_clauses = []
                params = {"user_id": user_id}
                
                for key, value in updates.items():
                    if key == "active_skills":
                        set_clauses.append("active_skills = :active_skills")
                        params["active_skills"] = value
                    elif key == "preferences":
                        set_clauses.append("preferences = :preferences")
                        params["preferences"] = json.dumps(value)
                    elif key == "social_links":
                        set_clauses.append("social_links = :social_links")
                        params["social_links"] = json.dumps(value)
                    elif key == "address":
                        set_clauses.append("address = :address")
                        params["address"] = json.dumps(value)
                    else:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return False
                    
                set_clauses.append("updated_at = NOW()")
                
                query = text(f"""
                UPDATE family_members
                SET {', '.join(set_clauses)}
                WHERE id = :user_id
                """)
                
                result = await session.execute(query, params)
                await session.commit()
                
                return result.rowcount > 0
            except Exception as e:
                print(f"Error updating user profile: {e}")
                await session.rollback()
                return False

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from PostgreSQL"""
        from api.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                SELECT preferences
                FROM family_members
                WHERE id = :user_id
                """)
                
                result = await session.execute(query, {"user_id": user_id})
                row = result.mappings().first()
                
                return row["preferences"] if row and row["preferences"] else {}
            except Exception as e:
                print(f"Error getting preferences: {e}")
                return {}

    # =========================================================================
    # Layer 4: Qdrant (Vector Search) - Semantic Memory Retrieval
    # =========================================================================

    async def store_in_qdrant(
        self,
        collection: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """Store text with embedding in Qdrant"""
        embedding = await self.generate_embedding(text)

        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "content": text,
                **metadata
            }
        )

        self.qdrant_client.upsert(
            collection_name=collection,
            points=[point]
        )

    async def search_qdrant(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search in Qdrant"""
        query_embedding = await self.generate_embedding(query)

        # Convert filter_conditions dict to proper Qdrant Filter object
        qdrant_filter = None
        if filter_conditions:
            field_conditions = []
            for key, value in filter_conditions.items():
                field_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            qdrant_filter = Filter(must=field_conditions)

        search_result = self.qdrant_client.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=limit,
            query_filter=qdrant_filter
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                **hit.payload
            }
            for hit in search_result
        ]

    # =========================================================================
    # Orchestration: Full Memory Context Assembly
    # =========================================================================

    async def get_context(
        self,
        user_id: str,
        conversation_id: str,
        query: Optional[str] = None
    ) -> MemoryContext:
        """
        Get complete memory context from all layers:
        1. Redis - immediate conversation
        2. Mem0 - working memory
        3. PostgreSQL - structured data
        4. Qdrant - semantic memories
        """

        # Layer 1: Immediate context from Redis
        immediate_context = await self.get_immediate_context(conversation_id)

        # Layer 2: Working memory from Mem0
        working_memory = []
        if query:
            working_memory = await self.search_mem0(query, user_id)
        else:
            working_memory = await self.get_mem0_memories(user_id)

        # Layer 3: User profile and preferences from PostgreSQL
        user_profile = await self.get_user_profile(user_id)
        user_preferences = await self.get_user_preferences(user_id)

        # Layer 4: Semantic search from Qdrant
        semantic_memories = []
        if query:
            semantic_memories = await self.search_qdrant(
                "family_memories",
                query,
                limit=5,
                filter_conditions={"user_id": user_id}
            )

        return MemoryContext(
            user_id=user_id,
            conversation_id=conversation_id,
            immediate_context=immediate_context,
            working_memory=working_memory,
            structured_data=user_profile or {},
            semantic_memories=semantic_memories,
            user_preferences=user_preferences
        )

    async def save_context(
        self,
        user_id: str,
        conversation_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save context across all appropriate memory layers:
        1. Redis - hot cache
        2. Mem0 - working memory
        3. PostgreSQL - permanent storage
        4. Qdrant - semantic embeddings
        """

        message = {
            "role": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        # Layer 1: Save to Redis cache
        await self.save_to_redis(conversation_id, message)

        # Layer 2: Save to Mem0 working memory
        await self.add_to_mem0(
            user_id,
            [{"role": message_type, "content": content}],
            metadata
        )

        # Layer 3: Save to PostgreSQL
        await self.save_conversation_to_db(
            user_id,
            conversation_id,
            message_type,
            content,
            metadata
        )

        # Layer 4: Save to Qdrant for semantic search
        await self.store_in_qdrant(
            "family_memories",
            content,
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message_type": message_type,
                "timestamp": datetime.now().timestamp(),
                **(metadata or {})
            }
        )

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search across all memory layers and combine results
        """

        # Search Mem0 working memory
        mem0_results = await self.search_mem0(query, user_id, limit=5)

        # Search Qdrant semantic memory
        qdrant_results = await self.search_qdrant(
            "family_memories",
            query,
            limit=5,
            filter_conditions={"user_id": user_id}
        )

        # Combine and deduplicate results
        all_results = []
        all_results.extend([
            {"source": "mem0", **result}
            for result in mem0_results
        ])
        all_results.extend([
            {"source": "qdrant", **result}
            for result in qdrant_results
        ])

        return all_results[:limit]

    async def cleanup_old_memories(self, days_old: int = 90):
        """
        Clean up old memories from cache layers
        (PostgreSQL and Qdrant retain for archival)
        """

        # Redis automatically expires based on TTL

        # TODO: Implement Mem0 cleanup if API supports it
        # TODO: Archive old PostgreSQL data to compressed storage

        pass

    async def close(self):
        """Close all connections"""
        if self.redis_client:
            await self.redis_client.close()
        await self.mem0_client.aclose()
        await self.ollama_client.aclose()


# ============================================================================
# Helper Functions
# ============================================================================

async def create_memory_manager() -> MemoryManager:
    """Factory function to create and initialize MemoryManager"""
    manager = MemoryManager(qdrant_url=settings.qdrant_url)
    await manager.initialize()
    return manager
