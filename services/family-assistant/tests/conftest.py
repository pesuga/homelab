"""
Pytest configuration and shared fixtures for the Family Assistant test suite.

Provides comprehensive test infrastructure:
- Database fixtures for isolated test databases
- Mock fixtures for external services (Telegram, Ollama, Qdrant)
- Authentication fixtures for family member testing
- Multimodal content fixtures for file handling tests
- Performance measurement fixtures
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Generator
from unittest.mock import AsyncMock, MagicMock
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import factory
from faker import Faker

# Set test environment before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "true"

from api.main import app
from api.database import create_checkpoint_schema
from config.settings import settings

# Initialize faker
fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings."""
    return settings  # Use existing settings but they'll be overridden by env vars


@pytest_asyncio.fixture
async def test_db():
    """Create and manage test database."""
    # For testing purposes, we'll use an in-memory approach
    # In a real environment, this would create a test PostgreSQL database
    import sqlite3
    import aiosqlite

    db_path = tempfile.mktemp(suffix=".db")

    # Initialize database schema
    async with aiosqlite.connect(db_path) as db:
        # Create tables (simplified for testing)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username VARCHAR(100),
                full_name VARCHAR(200),
                role VARCHAR(50),
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER,
                message_type VARCHAR(20),
                content TEXT,
                file_path VARCHAR(500),
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER,
                agent_type VARCHAR(50),
                memory_type VARCHAR(50),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id)
            )
        """)

        await db.commit()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    bot = AsyncMock()
    bot.get_me.return_value = MagicMock(
        id=123456789,
        username="test_bot",
        first_name="Test Bot"
    )
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_voice = AsyncMock()
    bot.send_document = AsyncMock()
    return bot


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    client = AsyncMock()

    # Mock chat completion response
    client.chat.return_value = {
        "message": {
            "role": "assistant",
            "content": "This is a test response from the assistant."
        }
    }

    # Mock model list
    client.list.return_value = {
        "models": [
            {"name": "llama3.1:8b"},
            {"name": "mistral:7b"},
            {"name": "nomic-embed-text"}
        ]
    }

    # Mock embeddings
    client.embeddings.return_value = {
        "embedding": [0.1] * 768  # Mock 768-dimensional embedding
    }

    return client


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    client = AsyncMock()

    # Mock search response
    client.search.return_value = [
        {
            "id": 1,
            "score": 0.95,
            "payload": {"text": "Similar memory content"}
        }
    ]

    # Mock upsert response
    client.upsert.return_value = {"status": "completed"}

    return client


@pytest.fixture
def mock_mem0_client():
    """Mock Mem0 client for testing."""
    client = AsyncMock()

    client.add.return_value = {
        "id": "test_memory_id",
        "message": "Memory added successfully"
    }

    client.search.return_value = [
        {
            "id": "memory_1",
            "memory": "Relevant memory content",
            "score": 0.89
        }
    ]

    return client


@pytest.fixture
def family_member_factory():
    """Factory for creating test family members."""
    class FamilyMemberFactory(factory.Factory):
        class Meta:
            model = dict
            abstract = True

        telegram_id = factory.Sequence(lambda n: 100000000 + n)
        username = factory.Faker("user_name")
        full_name = factory.Faker("name")
        role = factory.Iterator(["parent", "child", "teenager", "grandparent"])
        permissions = factory.LazyAttribute(lambda obj: {
            "can_chat": True,
            "can_send_images": obj["role"] in ["parent", "teenager"],
            "can_send_voice": True,
            "can_manage_schedule": obj["role"] == "parent",
            "time_restrictions": {} if obj["role"] == "parent" else {
                "start": "08:00",
                "end": "21:00"
            }
        })
        is_active = True

    return FamilyMemberFactory


@pytest.fixture
def sample_family_members(family_member_factory):
    """Create sample family members for testing."""
    return [
        family_member_factory(role="parent", full_name="John Doe"),
        family_member_factory(role="parent", full_name="Jane Doe"),
        family_member_factory(role="teenager", full_name="Teen Doe"),
        family_member_factory(role="child", full_name="Kid Doe")
    ]


@pytest.fixture
def multimodal_content():
    """Sample multimodal content for testing."""
    return {
        "text_message": "Hello family!",
        "image_data": b"fake_image_data_jpeg_format",
        "voice_data": b"fake_voice_data_ogg_format",
        "document_data": b"fake_document_pdf_format",
        "image_filename": "test_photo.jpg",
        "voice_filename": "test_voice.ogg",
        "document_filename": "test_document.pdf"
    }


@pytest.fixture
def performance_monitor():
    """Fixture for monitoring test performance."""
    import time
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class Metric:
        name: str
        duration: float
        timestamp: float

    metrics: List[Metric] = []

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.metric_name = None

        def start(self, name: str):
            self.start_time = time.time()
            self.metric_name = name

        def stop(self) -> float:
            if self.start_time and self.metric_name:
                duration = time.time() - self.start_time
                metrics.append(Metric(
                    name=self.metric_name,
                    duration=duration,
                    timestamp=time.time()
                ))
                self.start_time = None
                self.metric_name = None
                return duration
            return 0.0

        def get_metrics(self) -> List[Metric]:
            return metrics.copy()

    return PerformanceMonitor()


@pytest_asyncio.fixture
async def test_client(test_db):
    """Create test client with basic setup."""
    # Simple test client with mocked dependencies
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def fastapi_test_client():
    """Synchronous FastAPI test client for simple tests."""
    return TestClient(app)


# Helper fixtures for common test scenarios
@pytest.fixture
def authenticated_headers():
    """Headers for authenticated requests."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_chat_request():
    """Sample chat completion request."""
    return {
        "model": "family-assistant",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }


@pytest.fixture
def sample_telegram_update():
    """Sample Telegram update for testing."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "chat": {
                "id": 987654321,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": 1640995200,
            "text": "Hello bot"
        }
    }