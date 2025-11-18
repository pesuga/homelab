"""
Database connection and session management for Family Assistant.

Provides async database session creation and checkpoint schema management.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://homelab:homelab@postgres.homelab.svc.cluster.local:5432/homelab"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(text("SELECT * FROM users"))
            return result.fetchall()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_checkpoint_schema():
    """
    Create LangGraph checkpoint tables if they don't exist.

    This is called during application startup to ensure
    checkpoint tables are available for conversation memory.
    """
    async with engine.begin() as conn:
        # Create checkpoint tables for LangGraph
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT NOT NULL,
                checkpoint_id TEXT NOT NULL,
                parent_id TEXT,
                checkpoint BYTEA NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (thread_id, checkpoint_id)
            )
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_thread
            ON checkpoints(thread_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_parent
            ON checkpoints(parent_id)
        """))


async def init_database():
    """
    Initialize database schema and tables.

    Called during application startup.
    """
    await create_checkpoint_schema()


async def close_database():
    """
    Close database connections.

    Called during application shutdown.
    """
    await engine.dispose()
