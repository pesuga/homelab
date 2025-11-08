"""Database setup and schema creation for LangGraph checkpoints."""

import asyncio
import asyncpg
from typing import Optional
from config.settings import settings


async def create_checkpoint_schema() -> None:
    """Create PostgreSQL schema for LangGraph checkpoints."""

    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )

    try:
        # Create checkpoints table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                parent_checkpoint_id TEXT,
                type TEXT,
                checkpoint JSONB NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
            );
        """)

        # Create index for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS checkpoints_thread_id_idx
            ON checkpoints(thread_id, checkpoint_ns, checkpoint_id);
        """)

        # Create writes table for tracking checkpoint writes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_writes (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                idx INTEGER NOT NULL,
                channel TEXT NOT NULL,
                type TEXT,
                value JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
            );
        """)

        # Create user profiles table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                age INTEGER NOT NULL,
                permissions JSONB NOT NULL,
                preferences JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create conversation history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create index for conversation history
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS conversation_history_thread_id_idx
            ON conversation_history(thread_id);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS conversation_history_user_id_idx
            ON conversation_history(user_id);
        """)

        # Create audit log table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                details JSONB DEFAULT '{}',
                ip_address TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create index for audit log
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS audit_log_user_id_idx
            ON audit_log(user_id);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS audit_log_created_at_idx
            ON audit_log(created_at);
        """)

        print("✅ Database schema created successfully!")
        print(f"   - checkpoints table")
        print(f"   - checkpoint_writes table")
        print(f"   - user_profiles table")
        print(f"   - conversation_history table")
        print(f"   - audit_log table")

    finally:
        await conn.close()


async def insert_demo_users() -> None:
    """Insert demo user profiles for testing."""

    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )

    try:
        # Check if users already exist
        existing = await conn.fetchval(
            "SELECT COUNT(*) FROM user_profiles"
        )

        if existing > 0:
            print(f"ℹ️  User profiles already exist ({existing} users)")
            return

        # Insert demo users
        await conn.execute("""
            INSERT INTO user_profiles (user_id, name, role, age, permissions, preferences)
            VALUES
            ($1, $2, $3, $4, $5, $6),
            ($7, $8, $9, $10, $11, $12)
        """,
            # Dad (parent)
            "dad", "Dad", "parent", 40,
            '{"finance": true, "calendar": true, "notes": true, "tasks": true, "admin": true, "homework_help": false}',
            '{"morning_briefing_time": "07:00", "budget_alert_threshold": 150}',

            # Kid (child)
            "kid1", "Alice", "child", 12,
            '{"finance": false, "calendar": true, "notes": true, "tasks": true, "admin": false, "homework_help": true}',
            '{"homework_reminder_time": "16:00"}'
        )

        print("✅ Demo users inserted successfully!")
        print("   - dad (parent, full permissions)")
        print("   - kid1 (child, limited permissions)")

    finally:
        await conn.close()


async def verify_schema() -> bool:
    """Verify database schema is correctly set up."""

    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )

    try:
        # Check all required tables exist
        tables = [
            'checkpoints',
            'checkpoint_writes',
            'user_profiles',
            'conversation_history',
            'audit_log'
        ]

        for table in tables:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = $1
                )
            """, table)

            if not exists:
                print(f"❌ Table '{table}' does not exist")
                return False

        print("✅ All database tables verified!")
        return True

    finally:
        await conn.close()


if __name__ == "__main__":
    """Run database setup."""
    print("🚀 Setting up database schema...")

    asyncio.run(create_checkpoint_schema())
    asyncio.run(insert_demo_users())

    if asyncio.run(verify_schema()):
        print("\n✅ Database setup complete!")
    else:
        print("\n❌ Database setup failed!")
