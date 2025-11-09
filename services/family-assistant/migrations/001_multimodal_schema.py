"""Database migration scripts for multimodal content support."""

import asyncio
import asyncpg
from datetime import datetime
import json
from typing import Optional, Dict, Any

from config.settings import settings


async def create_multimodal_tables(conn):
    """Create multimodal database tables."""

    # Create content_types enum if not exists
    await conn.execute("""
        DO $$ BEGIN
            CREATE TYPE content_type AS ENUM (
                'text', 'image', 'audio', 'video', 'document', 'file'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create processing_status enum if not exists
    await conn.execute("""
        DO $$ BEGIN
            CREATE TYPE processing_status AS ENUM (
                'pending', 'processing', 'completed', 'failed', 'skipped'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create message_role enum if not exists
    await conn.execute("""
        DO $$ BEGIN
            CREATE TYPE message_role AS ENUM (
                'user', 'assistant', 'system'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Enhanced family_members table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(100) UNIQUE NOT NULL,
            telegram_id BIGINT UNIQUE,
            username VARCHAR(100),
            name VARCHAR(200) NOT NULL,
            role VARCHAR(50) NOT NULL,
            age INTEGER,
            is_active BOOLEAN DEFAULT true,

            -- Multimodal preferences
            preferred_content_types TEXT[] DEFAULT '{}',
            content_filters TEXT[] DEFAULT '{}',
            language_preferences TEXT[] DEFAULT ARRAY['en'],

            -- Vision preferences
            vision_analysis_enabled BOOLEAN DEFAULT true,
            photo_privacy_level VARCHAR(20) DEFAULT 'family',
            auto_image_description BOOLEAN DEFAULT true,

            -- Audio preferences
            speech_recognition_enabled BOOLEAN DEFAULT true,
            preferred_audio_format VARCHAR(10) DEFAULT 'ogg',
            voice_privacy_level VARCHAR(20) DEFAULT 'family',

            -- Document preferences
            document_extraction_enabled BOOLEAN DEFAULT true,
            auto_summarization BOOLEAN DEFAULT false,

            -- Legacy compatibility
            permissions JSONB DEFAULT '{}',
            preferences JSONB DEFAULT '{}',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Enhanced conversations table with multimodal support
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            thread_id VARCHAR(100) NOT NULL,
            family_member_id UUID REFERENCES family_members(id),

            role message_role NOT NULL,
            content TEXT,
            multimodal_content JSONB,

            processing_time_ms FLOAT,
            tokens_used INTEGER,
            model_used VARCHAR(100),

            reply_to_id UUID,
            reactions JSONB DEFAULT '[]'::jsonb,
            edited BOOLEAN DEFAULT false,
            edit_history JSONB DEFAULT '[]'::jsonb,

            content_analysis JSONB,
            safety_analysis JSONB,
            sentiment_analysis JSONB,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Content uploads table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS content_uploads (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            original_filename VARCHAR(500) NOT NULL,
            stored_filename VARCHAR(500) UNIQUE NOT NULL,
            file_path VARCHAR(1000) NOT NULL,

            content_type content_type NOT NULL,
            mime_type VARCHAR(100),
            file_size_bytes BIGINT NOT NULL,

            uploaded_by_id UUID REFERENCES family_members(id) NOT NULL,
            conversation_id UUID REFERENCES conversations(id),
            upload_source VARCHAR(50) DEFAULT 'telegram',

            width INTEGER,
            height INTEGER,
            duration_seconds FLOAT,
            codec VARCHAR(50),

            processing_status processing_status DEFAULT 'pending',
            processing_started_at TIMESTAMP,
            processing_completed_at TIMESTAMP,
            processing_error TEXT,

            extracted_data JSONB,
            analysis_results JSONB,
            safety_score FLOAT,

            privacy_level VARCHAR(20) DEFAULT 'family',
            download_count INTEGER DEFAULT 0,
            last_accessed_at TIMESTAMP,

            storage_backend VARCHAR(50) DEFAULT 'local',
            storage_url VARCHAR(1000),
            checksum_md5 VARCHAR(32),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
    """)

    # Content processing jobs table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS content_processing_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id VARCHAR(100) UNIQUE NOT NULL,

            content_upload_id UUID REFERENCES content_uploads(id) NOT NULL,
            job_type VARCHAR(50) NOT NULL,
            job_parameters JSONB,

            status processing_status DEFAULT 'pending',
            progress_percentage FLOAT DEFAULT 0.0,
            current_step VARCHAR(100),

            queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,

            result_data JSONB,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,

            processing_time_ms FLOAT,
            memory_used_mb FLOAT,
            cpu_usage_percent FLOAT,

            worker_id VARCHAR(100),
            worker_version VARCHAR(50),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Family context table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS family_context (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            family_member_id UUID REFERENCES family_members(id) NOT NULL,

            context_type VARCHAR(50) NOT NULL,
            context_key VARCHAR(100) NOT NULL,
            context_value JSONB NOT NULL,

            valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valid_until TIMESTAMP,
            is_active BOOLEAN DEFAULT true,

            source VARCHAR(50),
            confidence_score FLOAT,
            tags TEXT[] DEFAULT '{}',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(family_member_id, context_type, context_key, is_active)
        );
    """)

    # Enhanced audit log table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            family_member_id UUID REFERENCES family_members(id),

            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),

            details JSONB,
            old_values JSONB,
            new_values JSONB,

            request_ip INET,
            user_agent VARCHAR(500),
            request_method VARCHAR(10),
            request_path VARCHAR(500),

            session_id VARCHAR(100),
            conversation_id UUID REFERENCES conversations(id),
            content_upload_id UUID REFERENCES content_uploads(id),

            security_level VARCHAR(20) DEFAULT 'normal',
            compliance_tags TEXT[] DEFAULT '{}',
            retention_days INTEGER DEFAULT 365,

            status VARCHAR(20) DEFAULT 'success',
            error_code VARCHAR(50),
            error_message TEXT,

            processing_time_ms FLOAT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("✅ Multimodal database tables created successfully!")


async def create_indexes(conn):
    """Create performance indexes for multimodal tables."""

    # Family members indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_members_user_id
        ON family_members(user_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_members_telegram_id
        ON family_members(telegram_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_members_role
        ON family_members(role);
    """)

    # Conversations indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_thread_id
        ON conversations(thread_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_family_member
        ON conversations(family_member_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_created_at
        ON conversations(created_at);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_thread_member
        ON conversations(thread_id, family_member_id);
    """)

    # Content uploads indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_uploads_content_type
        ON content_uploads(content_type);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_uploads_uploaded_by
        ON content_uploads(uploaded_by_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_uploads_status
        ON content_uploads(processing_status);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_uploads_created_at
        ON content_uploads(created_at);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_uploads_privacy
        ON content_uploads(privacy_level);
    """)

    # Content processing jobs indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_jobs_job_id
        ON content_processing_jobs(job_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_jobs_upload_id
        ON content_processing_jobs(content_upload_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_jobs_status
        ON content_processing_jobs(status);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_jobs_queued_at
        ON content_processing_jobs(queued_at);
    """)

    # Family context indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_context_member_id
        ON family_context(family_member_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_context_type
        ON family_context(context_type);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_family_context_active
        ON family_context(is_active);
    """)

    # Audit log indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_member_id
        ON audit_log(family_member_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_action
        ON audit_log(action);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_created_at
        ON audit_log(created_at);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_security
        ON audit_log(security_level);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_status
        ON audit_log(status);
    """)

    print("✅ Database indexes created successfully!")


async def migrate_existing_data(conn):
    """Migrate existing data to multimodal schema."""

    # Check if legacy user_profiles table exists
    table_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'user_profiles'
        );
    """)

    if table_exists:
        # Migrate user profiles to family_members
        existing_profiles = await conn.fetch("""
            SELECT * FROM user_profiles;
        """)

        for profile in existing_profiles:
            await conn.execute("""
                INSERT INTO family_members (
                    user_id, name, role, age, permissions, preferences,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    age = EXCLUDED.age,
                    permissions = EXCLUDED.permissions,
                    preferences = EXCLUDED.preferences,
                    updated_at = EXCLUDED.updated_at;
            """,
                profile['user_id'],
                profile['name'],
                profile['role'],
                profile['age'],
                profile['permissions'],
                profile['preferences'],
                profile.get('created_at', datetime.utcnow()),
                profile.get('updated_at', datetime.utcnow())
            )

        print(f"✅ Migrated {len(existing_profiles)} user profiles to family_members")

    # Check if legacy conversation_history table exists
    conv_table_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'conversation_history'
        );
    """)

    if conv_table_exists:
        # Migrate conversation history
        existing_convs = await conn.fetch("""
            SELECT * FROM conversation_history;
        """)

        for conv in existing_convs:
            # Map legacy role to new message_role enum
            role_map = {'user': 'user', 'assistant': 'assistant', 'system': 'system'}
            role = role_map.get(conv['role'], 'user')

            await conn.execute("""
                INSERT INTO conversations (
                    thread_id, role, content, created_at
                ) VALUES ($1, $2, $3, $4);
            """,
                conv['thread_id'],
                role,
                conv['content'],
                conv.get('created_at', datetime.utcnow())
            )

        print(f"✅ Migrated {len(existing_convs)} conversation history entries")

    print("✅ Data migration completed!")


async def create_triggers_and_functions(conn):
    """Create triggers and stored procedures."""

    # Update timestamp trigger
    await conn.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Apply trigger to tables with updated_at columns
    for table in ['family_members', 'conversations', 'content_uploads', 'content_processing_jobs', 'family_context']:
        await conn.execute(f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)

    print("✅ Database triggers and functions created!")


async def run_migration():
    """Run the complete multimodal migration."""

    print("🚀 Starting multimodal database migration...")

    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )

    try:
        # Run migration steps
        await create_multimodal_tables(conn)
        await create_indexes(conn)
        await migrate_existing_data(conn)
        await create_triggers_and_functions(conn)

        print("✅ Multimodal database migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())