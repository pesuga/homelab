"""Database migration for sub-agent analytics tables."""

import asyncio
import asyncpg
from datetime import datetime

from config.settings import settings


async def create_analytics_tables(conn):
    """Create sub-agent analytics tables."""

    # Table 1: sub_agent_executions - Primary trace storage
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sub_agent_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            execution_id UUID UNIQUE NOT NULL,

            -- Request metadata
            user_id UUID,
            conversation_id VARCHAR(100),
            request_text TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

            -- Intent classification data
            agent_id VARCHAR(50) NOT NULL,
            confidence FLOAT NOT NULL,
            keywords JSONB,
            intent_duration_ms INTEGER,

            -- Agent execution data
            skill_prompt_size INTEGER,
            skill_prompt_tokens INTEGER,
            agent_duration_ms INTEGER,

            -- Token breakdown
            total_tokens INTEGER,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,

            -- Performance metrics
            total_duration_ms INTEGER NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,

            -- Additional metadata
            metadata JSONB,

            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Table 2: sub_agent_tool_calls - Individual tool invocations
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sub_agent_tool_calls (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            execution_id UUID NOT NULL REFERENCES sub_agent_executions(execution_id) ON DELETE CASCADE,

            -- Tool metadata
            tool_name VARCHAR(100) NOT NULL,
            agent_id VARCHAR(50) NOT NULL,
            call_index INTEGER NOT NULL,

            -- Tool invocation data
            parameters JSONB,
            result JSONB,

            -- Timing
            duration_ms INTEGER,
            success BOOLEAN NOT NULL,
            error_message TEXT,

            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

            -- Ensure ordering within execution
            CONSTRAINT unique_execution_call UNIQUE (execution_id, call_index)
        );
    """)

    # Table 3: sub_agent_metrics - Pre-aggregated time-series
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sub_agent_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Time bucket
            bucket_time TIMESTAMPTZ NOT NULL,
            bucket_granularity VARCHAR(20) NOT NULL,  -- 1min, 5min, 1hour, 1day
            agent_id VARCHAR(50) NOT NULL,

            -- Aggregate stats
            total_executions INTEGER DEFAULT 0,
            successful_executions INTEGER DEFAULT 0,
            failed_executions INTEGER DEFAULT 0,

            -- Performance percentiles (ms)
            avg_duration_ms INTEGER,
            p50_duration_ms INTEGER,
            p95_duration_ms INTEGER,
            p99_duration_ms INTEGER,
            min_duration_ms INTEGER,
            max_duration_ms INTEGER,

            -- Token statistics
            total_tokens INTEGER DEFAULT 0,
            avg_tokens INTEGER,
            total_prompt_tokens INTEGER DEFAULT 0,
            total_completion_tokens INTEGER DEFAULT 0,

            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

            -- Ensure one row per time bucket/granularity/agent
            CONSTRAINT unique_metric_bucket UNIQUE (bucket_time, bucket_granularity, agent_id)
        );
    """)

    # Table 4: llamacpp_metrics - LLM telemetry
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS llamacpp_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Timing
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

            -- TPS (tokens per second)
            tps_prompt FLOAT,
            tps_generation FLOAT,

            -- Slot utilization
            slots_total INTEGER,
            slots_used INTEGER,
            slots_processing INTEGER,
            utilization_percent FLOAT,

            -- Model info
            model_name VARCHAR(200),
            model_size_gb FLOAT,
            context_size INTEGER,

            -- GPU metrics (optional)
            gpu_utilization_percent FLOAT,
            gpu_memory_used_mb INTEGER,
            gpu_memory_total_mb INTEGER,
            gpu_temperature_c FLOAT,

            -- Additional metadata
            metadata JSONB
        );
    """)

    print("✅ Sub-agent analytics tables created successfully!")


async def create_analytics_indexes(conn):
    """Create performance indexes for analytics tables."""

    # sub_agent_executions indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_executions_execution_id
        ON sub_agent_executions(execution_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_executions_agent_id
        ON sub_agent_executions(agent_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_executions_timestamp
        ON sub_agent_executions(timestamp);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_executions_success
        ON sub_agent_executions(success);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_executions_user_id
        ON sub_agent_executions(user_id);
    """)

    # sub_agent_tool_calls indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_calls_execution_id
        ON sub_agent_tool_calls(execution_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_calls_agent_id
        ON sub_agent_tool_calls(agent_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_name
        ON sub_agent_tool_calls(tool_name);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_calls_timestamp
        ON sub_agent_tool_calls(timestamp);
    """)

    # sub_agent_metrics indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_bucket_time
        ON sub_agent_metrics(bucket_time);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_agent_id
        ON sub_agent_metrics(agent_id);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_granularity
        ON sub_agent_metrics(bucket_granularity);
    """)

    # llamacpp_metrics indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_llamacpp_timestamp
        ON llamacpp_metrics(timestamp);
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_llamacpp_model
        ON llamacpp_metrics(model_name);
    """)

    print("✅ Analytics indexes created successfully!")


async def run_migration():
    """Run the complete analytics migration."""

    print("🚀 Starting sub-agent analytics database migration...")

    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )

    try:
        await create_analytics_tables(conn)
        await create_analytics_indexes(conn)

        print("✅ Sub-agent analytics migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
