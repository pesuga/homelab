"""
Helper utilities for testing Family Assistant functionality.

Provides:
- Assertion helpers for API responses
- Database helpers for test data setup
- Mock helpers for external service responses
- Performance measurement utilities
- File and multimodal content helpers
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock
import aiofiles
import pytest


class APIResponseAsserts:
    """Assertion helpers for API responses."""

    @staticmethod
    def assert_success_response(response: Dict[str, Any], expected_status: int = 200):
        """Assert that API response is successful."""
        assert response.get("status") == "success" or "error" not in response
        if "status_code" in response:
            assert response["status_code"] == expected_status

    @staticmethod
    def assert_error_response(response: Dict[str, Any], expected_error: Optional[str] = None):
        """Assert that API response contains an error."""
        assert "error" in response or response.get("status") == "error"
        if expected_error:
            assert expected_error.lower() in str(response).lower()

    @staticmethod
    def assert_family_data_structure(data: Dict[str, Any]):
        """Assert family member data structure is correct."""
        required_fields = ["telegram_id", "username", "role", "permissions"]
        for field in required_fields:
            assert field in data

    @staticmethod
    def assert_chat_completion_structure(data: Dict[str, Any]):
        """Assert chat completion response structure is correct."""
        required_fields = ["id", "object", "created", "model", "choices"]
        for field in required_fields:
            assert field in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]


class DatabaseHelpers:
    """Helpers for database test setup and verification."""

    @staticmethod
    async def create_test_family_member(db: Any, member_data: Dict[str, Any]) -> int:
        """Create a test family member in database."""
        query = """
        INSERT INTO family_members (telegram_id, username, full_name, role, permissions, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING id
        """
        cursor = await db.execute(query, (
            member_data["telegram_id"],
            member_data["username"],
            member_data.get("full_name", ""),
            member_data["role"],
            json.dumps(member_data["permissions"]),
            member_data.get("is_active", True)
        ))
        result = await cursor.fetchone()
        await db.commit()
        return result[0] if result else None

    @staticmethod
    async def create_test_conversation(db: Any, conversation_data: Dict[str, Any]) -> int:
        """Create a test conversation in database."""
        query = """
        INSERT INTO conversations (family_member_id, message_type, content, file_path, metadata)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
        """
        cursor = await db.execute(query, (
            conversation_data["family_member_id"],
            conversation_data["message_type"],
            conversation_data.get("content", ""),
            conversation_data.get("file_path"),
            json.dumps(conversation_data.get("metadata", {}))
        ))
        result = await cursor.fetchone()
        await db.commit()
        return result[0] if result else None

    @staticmethod
    async def get_family_member_count(db: Any) -> int:
        """Get count of family members in database."""
        cursor = await db.execute("SELECT COUNT(*) FROM family_members")
        result = await cursor.fetchone()
        return result[0] if result else 0

    @staticmethod
    async def cleanup_test_data(db: Any, telegram_ids: List[int]):
        """Clean up test data by telegram IDs."""
        placeholders = ",".join("?" * len(telegram_ids))
        await db.execute(f"DELETE FROM conversations WHERE family_member_id IN (SELECT id FROM family_members WHERE telegram_id IN ({placeholders}))", telegram_ids)
        await db.execute(f"DELETE FROM agent_memories WHERE family_member_id IN (SELECT id FROM family_members WHERE telegram_id IN ({placeholders}))", telegram_ids)
        await db.execute(f"DELETE FROM family_members WHERE telegram_id IN ({placeholders})", telegram_ids)
        await db.commit()


class MockHelpers:
    """Helpers for creating comprehensive mocks."""

    @staticmethod
    def create_mock_telegram_message(text: str, user_id: int = 123456789, **kwargs) -> Dict[str, Any]:
        """Create a mock Telegram message."""
        return {
            "message_id": kwargs.get("message_id", 1),
            "from": {
                "id": user_id,
                "first_name": kwargs.get("first_name", "Test"),
                "last_name": kwargs.get("last_name", "User"),
                "username": kwargs.get("username", "testuser")
            },
            "chat": {
                "id": user_id,
                "first_name": kwargs.get("first_name", "Test"),
                "last_name": kwargs.get("last_name", "User"),
                "username": kwargs.get("username", "testuser"),
                "type": "private"
            },
            "date": kwargs.get("date", 1640995200),
            "text": text
        }

    @staticmethod
    def create_mock_telegram_photo(caption: str = "Test photo", user_id: int = 123456789, **kwargs) -> Dict[str, Any]:
        """Create a mock Telegram photo message."""
        base_msg = MockHelpers.create_mock_telegram_message("", user_id, **kwargs)
        base_msg.update({
            "photo": [
                {
                    "file_id": "test_file_id",
                    "file_unique_id": "test_unique_id",
                    "file_size": 12345,
                    "width": 800,
                    "height": 600
                }
            ],
            "caption": caption
        })
        return base_msg

    @staticmethod
    def create_mock_telegram_voice(duration: int = 5, user_id: int = 123456789, **kwargs) -> Dict[str, Any]:
        """Create a mock Telegram voice message."""
        base_msg = MockHelpers.create_mock_telegram_message("", user_id, **kwargs)
        base_msg.update({
            "voice": {
                "file_id": "test_voice_file_id",
                "file_unique_id": "test_voice_unique_id",
                "duration": duration,
                "mime_type": "audio/ogg",
                "file_size": 23456
            }
        })
        return base_msg

    @staticmethod
    def create_mock_ollama_response(content: str, model: str = "llama3.1:8b") -> Dict[str, Any]:
        """Create a mock Ollama chat response."""
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00.000Z",
            "message": {
                "role": "assistant",
                "content": content
            },
            "done": True,
            "total_duration": 123456789,
            "prompt_eval_count": 10,
            "eval_count": 15
        }

    @staticmethod
    def create_mock_qdrant_search_results(scores: List[float], texts: List[str]) -> List[Dict[str, Any]]:
        """Create mock Qdrant search results."""
        results = []
        for score, text in zip(scores, texts):
            results.append({
                "id": len(results),
                "score": score,
                "payload": {"text": text}
            })
        return results

    @staticmethod
    def create_mock_mem0_memories(memories: List[str]) -> List[Dict[str, Any]]:
        """Create mock Mem0 memory results."""
        return [
            {
                "id": f"memory_{i}",
                "memory": memory,
                "score": 0.9 - (i * 0.1)
            }
            for i, memory in enumerate(memories)
        ]


class FileHelpers:
    """Helpers for file and multimodal content testing."""

    @staticmethod
    async def create_test_image(filename: str = "test.jpg", size: tuple = (800, 600)) -> Path:
        """Create a test image file."""
        from PIL import Image
        import io

        # Create a simple test image
        img = Image.new('RGB', size, color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        # Save to temporary file
        temp_file = Path(tempfile.gettempdir()) / filename
        async with aiofiles.open(temp_file, 'wb') as f:
            await f.write(img_bytes.getvalue())

        return temp_file

    @staticmethod
    async def create_test_audio(filename: str = "test.ogg", duration: int = 3) -> Path:
        """Create a test audio file."""
        # Create a simple audio file (simplified)
        audio_data = b"fake_audio_ogg_format_data" * (duration * 1000)

        temp_file = Path(tempfile.gettempdir()) / filename
        async with aiofiles.open(temp_file, 'wb') as f:
            await f.write(audio_data)

        return temp_file

    @staticmethod
    async def create_test_document(filename: str = "test.pdf", content: str = "Test document content") -> Path:
        """Create a test document file."""
        temp_file = Path(tempfile.gettempdir()) / filename
        async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
            await f.write(content)

        return temp_file

    @staticmethod
    def get_file_mimetype(filename: str) -> str:
        """Get MIME type for a filename."""
        extension = Path(filename).suffix.lower()
        mimetypes = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.ogg': 'audio/ogg',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mimetypes.get(extension, 'application/octet-stream')

    @staticmethod
    async def read_file_as_bytes(file_path: Path) -> bytes:
        """Read file as bytes."""
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()


class PerformanceHelpers:
    """Helpers for performance testing and measurement."""

    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time."""
        import time
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            return {
                "result": result,
                "execution_time": end_time - start_time
            }

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            return {
                "result": result,
                "execution_time": end_time - start_time
            }

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    @staticmethod
    def assert_response_time(response_time: float, max_allowed: float):
        """Assert response time is within acceptable limits."""
        assert response_time < max_allowed, f"Response time {response_time:.2f}s exceeds maximum {max_allowed:.2f}s"

    @staticmethod
    def calculate_throughput(items_processed: int, time_taken: float) -> float:
        """Calculate throughput (items per second)."""
        return items_processed / time_taken if time_taken > 0 else 0


class FamilyWorkflowHelpers:
    """Helpers for testing family-specific workflows."""

    @staticmethod
    def create_permission_profile(role: str) -> Dict[str, Any]:
        """Create permission profiles for different family roles."""
        profiles = {
            "parent": {
                "can_chat": True,
                "can_send_images": True,
                "can_send_voice": True,
                "can_manage_schedule": True,
                "can_approve_requests": True,
                "time_restrictions": {},
                "content_filters": []
            },
            "teenager": {
                "can_chat": True,
                "can_send_images": True,
                "can_send_voice": True,
                "can_manage_schedule": False,
                "can_approve_requests": False,
                "time_restrictions": {"start": "07:00", "end": "22:00"},
                "content_filters": ["profanity", "adult_content"]
            },
            "child": {
                "can_chat": True,
                "can_send_images": False,
                "can_send_voice": True,
                "can_manage_schedule": False,
                "can_approve_requests": False,
                "time_restrictions": {"start": "08:00", "end": "20:00"},
                "content_filters": ["profanity", "adult_content", "violence"]
            },
            "grandparent": {
                "can_chat": True,
                "can_send_images": True,
                "can_send_voice": True,
                "can_manage_schedule": False,
                "can_approve_requests": False,
                "time_restrictions": {},
                "content_filters": []
            }
        }
        return profiles.get(role, profiles["child"])

    @staticmethod
    def is_within_time_restrictions(restrictions: Dict[str, str], test_time: str = None) -> bool:
        """Check if current time is within family member's time restrictions."""
        if not restrictions:
            return True

        from datetime import datetime, time as dt_time

        current_time = datetime.now().time() if not test_time else datetime.strptime(test_time, "%H:%M").time()

        start_time = dt_time.fromisoformat(restrictions.get("start", "00:00"))
        end_time = dt_time.fromisoformat(restrictions.get("end", "23:59"))

        return start_time <= current_time <= end_time

    @staticmethod
    def should_filter_content(content: str, filters: List[str]) -> bool:
        """Check if content should be filtered based on family member's filters."""
        # Simplified content filtering logic
        content_lower = content.lower()

        filter_keywords = {
            "profanity": ["bad", "worst", "terrible"],  # Simplified for testing
            "adult_content": ["adult", "mature"],
            "violence": ["violence", "fight", "weapon"]
        }

        for filter_type in filters:
            keywords = filter_keywords.get(filter_type, [])
            if any(keyword in content_lower for keyword in keywords):
                return True

        return False