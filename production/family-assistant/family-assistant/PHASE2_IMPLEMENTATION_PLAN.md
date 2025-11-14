# Phase 2: System Prompts & Memory Architecture - Implementation Plan

## Overview

This phase implements a sophisticated hierarchical system prompt architecture and 5-layer memory system inspired by Claude Code's memory and skills framework, adapted for family-centric AI interactions.

## Architecture Components

### 1. Hierarchical System Prompt Structure

```
prompts/
├── core/                    # Core system instructions (like CLAUDE.md)
│   ├── FAMILY_ASSISTANT.md  # Base system prompt
│   ├── PRINCIPLES.md        # Behavioral principles
│   ├── RULES.md             # Safety and operational rules
│   └── SYMBOLS.md           # Communication symbols for efficiency
│
├── roles/                   # Role-based personas (like MODE_*.md)
│   ├── parent.md            # Parent interaction mode
│   ├── teenager.md          # Teenage interaction mode
│   ├── child.md             # Child-safe interaction mode
│   └── grandparent.md       # Elder-friendly interaction mode
│
├── skills/                  # Specialized capabilities (like skills/)
│   ├── calendar.md          # Calendar management skill
│   ├── reminders.md         # Reminder system skill
│   ├── homework_help.md     # Educational assistance skill
│   └── family_chat.md       # Family communication skill
│
└── context/                 # Dynamic context templates
    ├── conversation.md      # Conversation context format
    ├── family_history.md    # Family memory context
    └── preferences.md       # User preference context
```

### 2. Five-Layer Memory Architecture

```python
Layer 1: Redis (Hot Cache)
- Purpose: Immediate conversation context
- TTL: 1 hour
- Data: Current conversation state, active tool calls
- Size: ~100 messages per user

Layer 2: Mem0 (Working Memory)
- Purpose: Session-aware semantic memory
- TTL: 24 hours
- Data: Recent interactions, user preferences
- Integration: Existing Mem0 service (port 30880)

Layer 3: PostgreSQL (Structured Storage)
- Purpose: Relational family data
- Persistence: Permanent
- Data: User profiles, family relationships, permissions
- Schema: family_members, conversations, preferences

Layer 4: Qdrant (Vector Search)
- Purpose: Semantic search across family knowledge
- Persistence: Permanent
- Data: Conversation embeddings, family memories
- Integration: Existing Qdrant service (port 30633)

Layer 5: Persistent Storage (Long-term Archive)
- Purpose: Historical data and audit logs
- Persistence: Permanent with retention policy
- Data: Conversation archives, system logs
- Location: PostgreSQL with compression
```

### 3. Dynamic Prompt Assembly System

```python
class PromptBuilder:
    """
    Assembles prompts dynamically based on:
    - User role (parent/teen/child)
    - Active skills (calendar, reminders, etc.)
    - Conversation context
    - Family preferences
    - Language (Spanish/English)
    """

    def build_system_prompt(
        user_context: UserContext,
        active_skills: List[str],
        memory_context: MemoryContext
    ) -> str:
        """
        Constructs hierarchical prompt:
        1. Load core system prompt (FAMILY_ASSISTANT.md)
        2. Inject role-specific behavior (parent.md/child.md)
        3. Add active skills context
        4. Include relevant memory context
        5. Apply language preferences
        """
        pass
```

## Implementation Tasks

### Task 1: Create Prompt Directory Structure

**Files to Create:**
- `prompts/core/FAMILY_ASSISTANT.md` - Base system instructions
- `prompts/core/PRINCIPLES.md` - Core behavioral principles
- `prompts/core/RULES.md` - Safety and operational rules
- `prompts/roles/parent.md` - Parent interaction mode
- `prompts/roles/teenager.md` - Teen interaction mode
- `prompts/roles/child.md` - Child interaction mode

### Task 2: Implement Memory Layer Integration

**Files to Create:**
- `api/services/memory_manager.py` - Five-layer memory orchestration
- `api/services/prompt_builder.py` - Dynamic prompt assembly
- `api/models/memory.py` - Memory data models

**Integration Points:**
- Redis client configuration
- Mem0 API integration (existing service)
- PostgreSQL schema extensions
- Qdrant collection setup (existing service)

### Task 3: Build Context Management System

**Files to Create:**
- `api/services/context_manager.py` - Context lifecycle management
- `api/models/context.py` - Context data models

**Features:**
- Load conversation history from memory layers
- Inject relevant family context
- Manage context window size
- Handle bilingual context switching

### Task 4: Implement Role-Based Personality System

**Files to Update:**
- `api/services/telegram_service.py` - Add role detection
- `api/main.py` - Add prompt assembly endpoint

**Features:**
- Detect user role from database
- Load appropriate role prompt
- Apply age-appropriate safety filters
- Adjust response style and tone

### Task 5: Create Bilingual Prompt Templates

**Files to Create:**
- `prompts/languages/spanish.md` - Spanish language context
- `prompts/languages/english.md` - English language context

**Features:**
- Natural code-switching support
- Cultural context awareness
- Family-specific terminology

## Technical Specifications

### Memory Manager Architecture

```python
class MemoryManager:
    """Orchestrates five-layer memory architecture"""

    def __init__(self):
        self.redis_client = RedisClient()
        self.mem0_client = Mem0Client(base_url="http://100.81.76.55:30880")
        self.postgres_client = PostgresClient()
        self.qdrant_client = QdrantClient(url="http://100.81.76.55:30633")

    async def get_context(self, user_id: str, conversation_id: str) -> MemoryContext:
        """
        Retrieves context from all memory layers:
        1. Check Redis hot cache (Layer 1)
        2. Fetch Mem0 working memory (Layer 2)
        3. Load PostgreSQL structured data (Layer 3)
        4. Query Qdrant for relevant memories (Layer 4)
        5. Access long-term archive if needed (Layer 5)
        """
        pass

    async def save_context(self, user_id: str, context: MemoryContext):
        """Saves context across appropriate memory layers"""
        pass

    async def search_memories(self, query: str, user_id: str) -> List[Memory]:
        """Semantic search across Qdrant and PostgreSQL"""
        pass
```

### Prompt Builder Architecture

```python
class PromptBuilder:
    """Dynamically assembles system prompts"""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.cache = {}  # Cache loaded prompt files

    def load_core_prompt(self) -> str:
        """Load FAMILY_ASSISTANT.md base prompt"""
        pass

    def load_role_prompt(self, role: str) -> str:
        """Load role-specific prompt (parent/teen/child)"""
        pass

    def load_skill_prompts(self, skills: List[str]) -> str:
        """Load and combine active skill prompts"""
        pass

    def inject_memory_context(self, prompt: str, context: MemoryContext) -> str:
        """Inject relevant memory context into prompt"""
        pass

    def build(self, user_context: UserContext) -> str:
        """Assemble complete system prompt"""
        # 1. Load core prompt
        # 2. Add role-specific behavior
        # 3. Inject active skills
        # 4. Add memory context
        # 5. Apply language preferences
        pass
```

### Database Schema Extensions

```sql
-- Family member role and preferences
ALTER TABLE family_members ADD COLUMN role VARCHAR(20) DEFAULT 'member';
ALTER TABLE family_members ADD COLUMN age_group VARCHAR(20);
ALTER TABLE family_members ADD COLUMN language_preference VARCHAR(10) DEFAULT 'en';
ALTER TABLE family_members ADD COLUMN active_skills JSONB DEFAULT '[]';

-- Conversation memory
CREATE TABLE conversation_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id),
    conversation_id UUID,
    message_type VARCHAR(20),
    content TEXT,
    embedding VECTOR(1536),  -- For semantic search
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- User preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) UNIQUE,
    prompt_style VARCHAR(50),
    response_length VARCHAR(20),
    safety_level VARCHAR(20),
    preferences JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Family knowledge base
CREATE TABLE family_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id UUID,
    knowledge_type VARCHAR(50),
    title VARCHAR(200),
    content TEXT,
    embedding VECTOR(1536),
    created_by UUID REFERENCES family_members(id),
    created_at TIMESTAMP DEFAULT NOW(),
    tags TEXT[]
);
```

### Qdrant Collection Schema

```python
# Family memories collection
{
    "collection_name": "family_memories",
    "vectors": {
        "size": 1536,  # nomic-embed-text dimension
        "distance": "Cosine"
    },
    "payload_schema": {
        "user_id": "keyword",
        "conversation_id": "keyword",
        "message_type": "keyword",
        "timestamp": "integer",
        "content": "text",
        "language": "keyword",
        "family_id": "keyword"
    }
}

# Family knowledge collection
{
    "collection_name": "family_knowledge",
    "vectors": {
        "size": 1536,
        "distance": "Cosine"
    },
    "payload_schema": {
        "family_id": "keyword",
        "knowledge_type": "keyword",
        "title": "text",
        "content": "text",
        "created_by": "keyword",
        "created_at": "integer",
        "tags": "keyword[]"
    }
}
```

## Integration with Existing Services

### Mem0 Integration

```python
class Mem0Integration:
    """Integration with existing Mem0 service"""

    def __init__(self):
        self.base_url = "http://100.81.76.55:30880"
        self.client = httpx.AsyncClient()

    async def add_memory(self, user_id: str, message: str, metadata: dict):
        """Add memory to Mem0"""
        response = await self.client.post(
            f"{self.base_url}/v1/memories/",
            json={
                "user_id": user_id,
                "messages": [{"role": "user", "content": message}],
                "metadata": metadata
            }
        )
        return response.json()

    async def search_memories(self, query: str, user_id: str):
        """Search Mem0 memories"""
        response = await self.client.post(
            f"{self.base_url}/v1/memories/search/",
            json={"query": query, "user_id": user_id}
        )
        return response.json()
```

### Qdrant Integration

```python
class QdrantIntegration:
    """Integration with existing Qdrant service"""

    def __init__(self):
        self.client = QdrantClient(url="http://100.81.76.55:30633")

    async def create_collections(self):
        """Initialize family memory collections"""
        # Create family_memories collection
        # Create family_knowledge collection
        pass

    async def store_embedding(
        self,
        collection: str,
        text: str,
        metadata: dict
    ):
        """Store text with embedding"""
        # Generate embedding using Ollama (nomic-embed-text)
        # Store in Qdrant with metadata
        pass

    async def search_similar(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        filter_conditions: dict = None
    ):
        """Semantic search"""
        # Generate query embedding
        # Search Qdrant with filters
        pass
```

## API Endpoints

### New Endpoints to Implement

```python
# Prompt management
@app.get("/api/prompts/{role}")
async def get_role_prompt(role: str):
    """Get role-specific prompt template"""
    pass

@app.post("/api/prompts/build")
async def build_prompt(user_context: UserContext):
    """Build dynamic system prompt for user"""
    pass

# Memory management
@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str):
    """Retrieve user memory context"""
    pass

@app.post("/api/memory/search")
async def search_memories(query: SearchQuery):
    """Semantic search across user memories"""
    pass

# Context management
@app.get("/api/context/{conversation_id}")
async def get_conversation_context(conversation_id: str):
    """Get full conversation context"""
    pass
```

## Testing Plan

### Unit Tests
- Test each memory layer independently
- Test prompt assembly with different roles
- Test bilingual prompt generation
- Test memory search and retrieval

### Integration Tests
- Test full memory stack (Redis → Mem0 → PostgreSQL → Qdrant)
- Test prompt assembly with real user contexts
- Test conversation flow with memory persistence
- Test role switching mid-conversation

### Performance Tests
- Memory retrieval latency (target: <500ms)
- Prompt assembly time (target: <100ms)
- Context window management
- Memory search performance

## Success Criteria

1. ✅ Hierarchical prompt system operational
2. ✅ All five memory layers integrated
3. ✅ Role-based personality adaptation working
4. ✅ Bilingual prompt system functional
5. ✅ Memory persistence across sessions
6. ✅ Context retrieval <500ms (P95)
7. ✅ Prompt assembly <100ms (P95)

## Next Steps After Phase 2

Once Phase 2 is complete, we'll have:
- Sophisticated AI personality system
- Multi-layer memory architecture
- Dynamic context management
- Role-based safety controls

This sets the foundation for Phase 3 (Family IAM & Privacy) and Phase 4 (MCP Tool Integration).
