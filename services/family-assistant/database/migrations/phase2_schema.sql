-- ============================================================================
-- Phase 2 Database Migration: System Prompts & Memory Architecture
-- ============================================================================
--
-- This migration adds schema extensions for Phase 2 features:
-- - User role and preferences
-- - Conversation memory with embeddings
-- - User preferences table
-- - Family knowledge base
--
-- Run this migration after Phase 2 deployment
--
-- ============================================================================

-- Enable pgvector extension for embeddings (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Table: family_members (Extensions)
-- ============================================================================

-- Add Phase 2 columns to existing family_members table
ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'member'
    CHECK (role IN ('parent', 'teenager', 'child', 'grandparent', 'member'));

ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS age_group VARCHAR(20)
    CHECK (age_group IN ('child', 'teen', 'adult', 'elder'));

ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) DEFAULT 'en'
    CHECK (language_preference IN ('en', 'es', 'bilingual'));

ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS active_skills JSONB DEFAULT '[]'::jsonb;

ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS privacy_level VARCHAR(20) DEFAULT 'family'
    CHECK (privacy_level IN ('private', 'family', 'parental_only'));

ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS safety_level VARCHAR(20) DEFAULT 'adult'
    CHECK (safety_level IN ('child', 'teen', 'adult'));

-- Add indexes for Phase 2 queries
CREATE INDEX IF NOT EXISTS idx_family_members_role ON family_members(role);
CREATE INDEX IF NOT EXISTS idx_family_members_language ON family_members(language_preference);

-- ============================================================================
-- Table: conversation_memory
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    message_type VARCHAR(20) NOT NULL
        CHECK (message_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    embedding VECTOR(768),  -- nomic-embed-text dimension
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for conversation queries
CREATE INDEX IF NOT EXISTS idx_conversation_memory_user
    ON conversation_memory(user_id);

CREATE INDEX IF NOT EXISTS idx_conversation_memory_conversation
    ON conversation_memory(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_memory_created_at
    ON conversation_memory(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_memory_type
    ON conversation_memory(message_type);

-- Vector similarity search index (using IVFFlat)
CREATE INDEX IF NOT EXISTS idx_conversation_memory_embedding
    ON conversation_memory
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Metadata GIN index for fast JSON queries
CREATE INDEX IF NOT EXISTS idx_conversation_memory_metadata
    ON conversation_memory USING gin(metadata);

-- ============================================================================
-- Table: user_preferences
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES family_members(id) ON DELETE CASCADE,
    prompt_style VARCHAR(50) DEFAULT 'balanced'
        CHECK (prompt_style IN ('minimal', 'balanced', 'comprehensive')),
    response_length VARCHAR(20) DEFAULT 'medium'
        CHECK (response_length IN ('brief', 'medium', 'detailed')),
    safety_level VARCHAR(20) DEFAULT 'adult'
        CHECK (safety_level IN ('child', 'teen', 'adult')),
    tone_preference VARCHAR(30) DEFAULT 'friendly'
        CHECK (tone_preference IN ('professional', 'friendly', 'casual', 'formal')),
    emoji_usage VARCHAR(20) DEFAULT 'moderate'
        CHECK (emoji_usage IN ('none', 'minimal', 'moderate', 'frequent')),
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_user_preferences_user
    ON user_preferences(user_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_timestamp();

-- ============================================================================
-- Table: family_knowledge
-- ============================================================================

CREATE TABLE IF NOT EXISTS family_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id UUID NOT NULL,
    knowledge_type VARCHAR(50) NOT NULL
        CHECK (knowledge_type IN (
            'event', 'contact', 'note', 'reminder',
            'recipe', 'document', 'memory', 'other'
        )),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),  -- nomic-embed-text dimension
    created_by UUID REFERENCES family_members(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for family knowledge queries
CREATE INDEX IF NOT EXISTS idx_family_knowledge_family
    ON family_knowledge(family_id);

CREATE INDEX IF NOT EXISTS idx_family_knowledge_type
    ON family_knowledge(knowledge_type);

CREATE INDEX IF NOT EXISTS idx_family_knowledge_created_by
    ON family_knowledge(created_by);

CREATE INDEX IF NOT EXISTS idx_family_knowledge_created_at
    ON family_knowledge(created_at DESC);

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_family_knowledge_embedding
    ON family_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Tags GIN index for array searches
CREATE INDEX IF NOT EXISTS idx_family_knowledge_tags
    ON family_knowledge USING gin(tags);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_family_knowledge_content_search
    ON family_knowledge USING gin(to_tsvector('english', title || ' ' || content));

-- Trigger to update updated_at timestamp
CREATE TRIGGER trigger_family_knowledge_updated_at
    BEFORE UPDATE ON family_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_timestamp();

-- ============================================================================
-- Table: conversation_summaries (Optional)
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    topics TEXT[] DEFAULT ARRAY[]::TEXT[],
    sentiment VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for conversation summaries
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_conversation
    ON conversation_summaries(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_summaries_user
    ON conversation_summaries(user_id);

CREATE INDEX IF NOT EXISTS idx_conversation_summaries_created_at
    ON conversation_summaries(created_at DESC);

-- ============================================================================
-- Views (Optional - for analytics)
-- ============================================================================

-- View: Active conversations in last 24 hours
CREATE OR REPLACE VIEW active_conversations_24h AS
SELECT
    user_id,
    conversation_id,
    COUNT(*) as message_count,
    MIN(created_at) as start_time,
    MAX(created_at) as last_activity,
    ARRAY_AGG(DISTINCT message_type) as message_types
FROM conversation_memory
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY user_id, conversation_id
ORDER BY last_activity DESC;

-- View: User activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    fm.id as user_id,
    fm.first_name,
    fm.role,
    fm.language_preference,
    COUNT(DISTINCT cm.conversation_id) as total_conversations,
    COUNT(cm.id) as total_messages,
    MAX(cm.created_at) as last_active,
    ARRAY_AGG(DISTINCT cm.message_type) as message_types_used
FROM family_members fm
LEFT JOIN conversation_memory cm ON fm.id = cm.user_id
GROUP BY fm.id, fm.first_name, fm.role, fm.language_preference;

-- ============================================================================
-- Functions (Optional - helper functions)
-- ============================================================================

-- Function: Search conversation memory by similarity
CREATE OR REPLACE FUNCTION search_conversation_memory(
    query_embedding VECTOR(768),
    target_user_id UUID,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    similarity FLOAT,
    created_at TIMESTAMP,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.id,
        cm.content,
        1 - (cm.embedding <=> query_embedding) as similarity,
        cm.created_at,
        cm.metadata
    FROM conversation_memory cm
    WHERE cm.user_id = target_user_id
        AND cm.embedding IS NOT NULL
    ORDER BY cm.embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Get recent conversation context
CREATE OR REPLACE FUNCTION get_recent_context(
    target_conversation_id UUID,
    message_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    message_type VARCHAR,
    content TEXT,
    created_at TIMESTAMP,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.message_type,
        cm.content,
        cm.created_at,
        cm.metadata
    FROM conversation_memory cm
    WHERE cm.conversation_id = target_conversation_id
    ORDER BY cm.created_at DESC
    LIMIT message_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Sample Data (Optional - for testing)
-- ============================================================================

-- Note: Uncomment to insert sample data for testing

/*
-- Sample user preferences
INSERT INTO user_preferences (user_id, prompt_style, response_length, preferences)
SELECT
    id,
    'balanced',
    'medium',
    '{"tone": "friendly", "emoji_usage": "moderate"}'::jsonb
FROM family_members
WHERE role = 'parent'
ON CONFLICT (user_id) DO NOTHING;

-- Sample family knowledge
INSERT INTO family_knowledge (
    family_id,
    knowledge_type,
    title,
    content,
    tags,
    created_by
)
VALUES
    (
        (SELECT family_id FROM family_members LIMIT 1),
        'event',
        'Family Birthday Calendar',
        'December birthdays: María (Dec 15), Pedro (Dec 22)',
        ARRAY['birthday', 'december', 'family'],
        (SELECT id FROM family_members WHERE role = 'parent' LIMIT 1)
    )
ON CONFLICT DO NOTHING;
*/

-- ============================================================================
-- Migration Verification
-- ============================================================================

-- Check that all Phase 2 tables exist
DO $$
DECLARE
    missing_tables TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check required tables
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'conversation_memory') THEN
        missing_tables := array_append(missing_tables, 'conversation_memory');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'user_preferences') THEN
        missing_tables := array_append(missing_tables, 'user_preferences');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'family_knowledge') THEN
        missing_tables := array_append(missing_tables, 'family_knowledge');
    END IF;

    -- Report results
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE NOTICE 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE 'Phase 2 migration completed successfully!';
        RAISE NOTICE 'All required tables created.';
    END IF;
END $$;

-- ============================================================================
-- End of Migration
-- ============================================================================
