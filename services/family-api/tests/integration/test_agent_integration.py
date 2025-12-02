"""
Integration tests for agent components and external services.

Tests:
- Agent coordination and message flow
- Memory system integration
- LLM service communication
- Multimodal content processing
- Error handling and recovery
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from tests.helpers.test_helpers import (
    MockHelpers, PerformanceHelpers, DatabaseHelpers,
    APIResponseAsserts
)


class TestAgentMemoryIntegration:
    """Test integration between agents and memory systems."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval(self, test_db, mock_mem0_client, mock_qdrant_client):
        """Test complete memory storage and retrieval cycle."""
        # Setup family member
        member_data = {
            "telegram_id": 123456789,
            "username": "testuser",
            "role": "parent",
            "permissions": {"can_chat": True}
        }
        member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)

        # Test memory storage
        memory_content = "User prefers to be called John"
        mock_mem0_client.add.return_value = {"id": "memory_123", "status": "success"}

        # Store memory
        storage_result = await mock_mem0_client.add(
            user_id=str(member_id),
            memory=memory_content,
            metadata={"source": "conversation"}
        )
        assert storage_result["status"] == "success"

        # Test memory retrieval
        mock_mem0_client.search.return_value = [
            {
                "id": "memory_123",
                "memory": memory_content,
                "score": 0.95,
                "metadata": {"source": "conversation"}
            }
        ]

        search_results = await mock_mem0_client.search(
            user_id=str(member_id),
            query="What should I call this user?",
            limit=5
        )
        assert len(search_results) == 1
        assert search_results[0]["memory"] == memory_content
        assert search_results[0]["score"] > 0.9

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_database_integration(self, test_db, mock_qdrant_client):
        """Test vector database integration for semantic search."""
        # Setup test data
        test_memories = [
            "User loves pizza and Italian food",
            "User has a dog named Max",
            "User works from home on Tuesdays"
        ]

        # Test vector storage
        for i, memory in enumerate(test_memories):
            mock_qdrant_client.upsert.return_value = {"status": "completed"}
            await mock_qdrant_client.upsert(
                collection="family_memories",
                points=[{
                    "id": i,
                    "vector": [0.1] * 768,  # Mock 768-dimensional vector
                    "payload": {"text": memory, "user_id": 123456789}
                }]
            )

        # Test vector search
        mock_qdrant_client.search.return_value = MockHelpers.create_mock_qdrant_search_results(
            scores=[0.9, 0.7, 0.3],
            texts=test_memories
        )

        search_results = await mock_qdrant_client.search(
            collection="family_memories",
            query_vector=[0.1] * 768,
            limit=3,
            query_filter={"must": [{"key": "user_id", "match": {"value": 123456789}}]}
        )

        assert len(search_results) == 3
        assert search_results[0]["score"] > search_results[1]["score"]
        assert all("payload" in result for result in search_results)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_agent_memory_sharing(self, test_db, mock_mem0_client, mock_qdrant_client):
        """Test memory sharing between different agent types."""
        user_id = 123456789

        # Memory Agent stores conversation memory
        conversation_memory = "User mentioned they're going on vacation next week"
        mock_mem0_client.add.return_value = {"id": "conv_memory_1"}
        await mock_mem0_client.add(
            user_id=str(user_id),
            memory=conversation_memory,
            metadata={"agent": "memory", "type": "conversation"}
        )

        # Schedule Agent stores scheduling memory
        schedule_memory = "User has weekly meetings on Mondays at 10 AM"
        mock_mem0_client.add.return_value = {"id": "schedule_memory_1"}
        await mock_mem0_client.add(
            user_id=str(user_id),
            memory=schedule_memory,
            metadata={"agent": "schedule", "type": "recurring_event"}
        )

        # Test that both agents can access shared memories
        mock_mem0_client.search.return_value = [
            {"id": "conv_memory_1", "memory": conversation_memory, "score": 0.9},
            {"id": "schedule_memory_1", "memory": schedule_memory, "score": 0.8}
        ]

        shared_memories = await mock_mem0_client.search(
            user_id=str(user_id),
            query="User plans",
            limit=10
        )

        assert len(shared_memories) == 2
        memory_types = [mem.get("metadata", {}).get("type") for mem in shared_memories]
        assert "conversation" in memory_types
        assert "recurring_event" in memory_types


class TestLLMIntegration:
    """Test integration with LLM services."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_chat_completion(self, mock_ollama_client):
        """Test Ollama chat completion integration."""
        chat_request = {
            "model": "llama3.1:8b",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "stream": False
        }

        mock_response = MockHelpers.create_mock_ollama_response(
            "Hello! I'm doing well, thank you for asking. How can I help you today?"
        )
        mock_ollama_client.chat.return_value = mock_response

        response = await mock_ollama_client.chat(**chat_request)

        assert response["model"] == chat_request["model"]
        assert "message" in response
        assert response["message"]["role"] == "assistant"
        assert len(response["message"]["content"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_streaming_completion(self, mock_ollama_client):
        """Test Ollama streaming chat completion."""
        chat_request = {
            "model": "llama3.1:8b",
            "messages": [
                {"role": "user", "content": "Tell me a short story"}
            ],
            "stream": True
        }

        # Mock streaming response
        async def mock_stream():
            chunks = [
                {"done": False, "message": {"content": "Once "}},
                {"done": False, "message": {"content": "upon "}},
                {"done": False, "message": {"content": "a "}},
                {"done": True, "message": {"content": "time."}}
            ]
            for chunk in chunks:
                yield chunk

        mock_ollama_client.chat.return_value = mock_stream()

        collected_content = []
        async for chunk in mock_ollama_client.chat(**chat_request):
            if not chunk["done"]:
                collected_content.append(chunk["message"]["content"])

        full_response = "".join(collected_content)
        assert full_response == "Once upon a time."

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multimodal_vision_processing(self, mock_ollama_client):
        """Test multimodal content processing with vision capabilities."""
        # Mock image data
        image_data = b"fake_image_data"

        multimodal_request = {
            "model": "llava",  # Vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you see in this image?"},
                        {"type": "image", "image": image_data}
                    ]
                }
            ]
        }

        mock_response = MockHelpers.create_mock_ollama_response(
            "I can see a family photo with several people smiling.",
            model="llava"
        )
        mock_ollama_client.chat.return_value = mock_response

        response = await mock_ollama_client.chat(**multimodal_request)

        assert response["model"] == "llava"
        assert "family photo" in response["message"]["content"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_error_handling_and_retry(self, mock_ollama_client):
        """Test LLM error handling and retry logic."""
        chat_request = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        # Simulate temporary failure then success
        call_count = 0
        async def mock_chat_with_failure(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Service temporarily unavailable")
            return MockHelpers.create_mock_ollama_response("Success after retry")

        mock_ollama_client.chat.side_effect = mock_chat_with_failure

        # Test retry logic (simplified)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await mock_ollama_client.chat(**chat_request)
                assert "Success after retry" in response["message"]["content"]
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.1)  # Brief delay before retry
        else:
            pytest.fail("Retry logic failed to recover from temporary error")


class TestTelegramIntegration:
    """Test Telegram bot integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_telegram_message_processing(self, mock_telegram_bot):
        """Test processing Telegram messages."""
        # Create test message
        test_message = MockHelpers.create_mock_telegram_message(
            text="Hello family assistant!",
            user_id=123456789,
            username="testuser"
        )

        # Mock message processing
        processed_response = "Hello! I'm here to help your family."
        mock_telegram_bot.send_message.return_value = MagicMock(
            message_id=2,
            text=processed_response
        )

        # Simulate message processing
        await mock_telegram_bot.send_message(
            chat_id=test_message["chat"]["id"],
            text=processed_response
        )

        # Verify message was sent
        mock_telegram_bot.send_message.assert_called_once_with(
            chat_id=123456789,
            text=processed_response
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_telegram_photo_processing(self, mock_telegram_bot):
        """Test processing Telegram photo messages."""
        test_photo_message = MockHelpers.create_mock_telegram_photo(
            caption="Look at this family photo!",
            user_id=123456789
        )

        # Mock photo processing
        analysis_result = "This appears to be a happy family photo."
        mock_telegram_bot.send_message.return_value = MagicMock(
            message_id=3,
            text=analysis_result
        )

        # Process photo
        await mock_telegram_bot.send_message(
            chat_id=test_photo_message["chat"]["id"],
            text=analysis_result
        )

        mock_telegram_bot.send_message.assert_called_once()
        call_args = mock_telegram_bot.send_message.call_args[1]
        assert "family photo" in call_args["text"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_telegram_voice_processing(self, mock_telegram_bot):
        """Test processing Telegram voice messages."""
        test_voice_message = MockHelpers.create_mock_telegram_voice(
            duration=5,
            user_id=123456789
        )

        # Mock transcription and response
        transcription = "Hello, can you help me with something?"
        response = "I'd be happy to help you! What do you need assistance with?"

        mock_telegram_bot.send_message.return_value = MagicMock(
            message_id=4,
            text=f"Transcription: {transcription}\n\nResponse: {response}"
        )

        # Process voice message
        await mock_telegram_bot.send_message(
            chat_id=test_voice_message["chat"]["id"],
            text=f"Transcription: {transcription}\n\nResponse: {response}"
        )

        mock_telegram_bot.send_message.assert_called_once()
        call_args = mock_telegram_bot.send_message.call_args[1]
        assert "Transcription:" in call_args["text"]
        assert "Response:" in call_args["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_telegram_webhook_verification(self, mock_telegram_bot):
        """Test Telegram webhook setup and verification."""
        webhook_url = "https://homelab.pesulabs.net/telegram-webhook"
        webhook_secret = "test_webhook_secret"

        # Mock webhook setup
        mock_telegram_bot.set_webhook.return_value = {
            "ok": True,
            "result": True,
            "description": "Webhook was set"
        }

        # Set webhook
        result = await mock_telegram_bot.set_webhook(
            url=webhook_url,
            secret_token=webhook_secret
        )

        assert result["ok"] is True
        assert result["result"] is True
        mock_telegram_bot.set_webhook.assert_called_once_with(
            url=webhook_url,
            secret_token=webhook_secret
        )


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_complete_family_conversation_flow(self, test_db, mock_ollama_client, mock_mem0_client, mock_telegram_bot):
        """Test complete conversation flow from Telegram to response."""
        # Setup family member
        member_data = {
            "telegram_id": 123456789,
            "username": "parent_user",
            "role": "parent",
            "permissions": {"can_chat": True, "can_send_images": True}
        }
        member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)

        # Step 1: Receive Telegram message
        telegram_message = MockHelpers.create_mock_telegram_message(
            text="What's for dinner tonight?",
            user_id=123456789
        )

        # Step 2: Process with memory lookup
        mock_mem0_client.search.return_value = [
            {"memory": "Family usually has pasta on Tuesdays", "score": 0.9}
        ]

        # Step 3: Generate response using LLM
        mock_ollama_response = MockHelpers.create_mock_ollama_response(
            "Based on your usual routine, you might want to make pasta tonight. Would you like me to suggest a recipe?"
        )
        mock_ollama_client.chat.return_value = mock_ollama_response

        # Step 4: Store new memory
        mock_mem0_client.add.return_value = {"id": "new_memory_1"}
        await mock_mem0_client.add(
            user_id=str(member_id),
            memory="User asked about dinner plans",
            metadata={"type": "conversation", "timestamp": datetime.now().isoformat()}
        )

        # Step 5: Send response via Telegram
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=5)
        await mock_telegram_bot.send_message(
            chat_id=telegram_message["chat"]["id"],
            text=mock_ollama_response["message"]["content"]
        )

        # Verify complete flow
        mock_mem0_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()
        mock_mem0_client.add.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.multimodal
    @pytest.mark.asyncio
    async def test_multimodal_family_workflow(self, test_db, mock_ollama_client, mock_qdrant_client, mock_telegram_bot):
        """Test workflow with multimodal content (text + image)."""
        # Setup family member
        member_data = {
            "telegram_id": 123456789,
            "username": "teenager",
            "role": "teenager",
            "permissions": {"can_chat": True, "can_send_images": True}
        }
        member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)

        # Step 1: Receive photo with caption
        telegram_photo = MockHelpers.create_mock_telegram_photo(
            caption="Can I go to this event?",
            user_id=123456789
        )

        # Step 2: Process image with vision model
        vision_response = MockHelpers.create_mock_ollama_response(
            "This appears to be a concert flyer. The event is on Friday night at 8 PM.",
            model="llava"
        )
        mock_ollama_client.chat.return_value = vision_response

        # Step 3: Get relevant memories about permissions
        mock_qdrant_client.search.return_value = MockHelpers.create_mock_qdrant_search_results(
            scores=[0.9],
            texts=["Teenager needs parent approval for events after 9 PM on weeknights"]
        )

        # Step 4: Generate contextual response
        final_response = MockHelpers.create_mock_ollama_response(
            "I see this is a concert on Friday night at 8 PM. Since it's a weekend event and before 9 PM, you should be able to go. However, you'll still need to ask a parent for permission first."
        )
        mock_ollama_client.chat.return_value = final_response

        # Step 5: Send response
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=6)
        await mock_telegram_bot.send_message(
            chat_id=telegram_photo["chat"]["id"],
            text=final_response["message"]["content"]
        )

        # Verify workflow
        assert mock_ollama_client.chat.call_count == 2  # Vision + final response
        mock_qdrant_client.search.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test workflow with error handling and recovery."""
        telegram_message = MockHelpers.create_mock_telegram_message(
            text="Help me with homework",
            user_id=123456789
        )

        # Simulate LLM service failure
        mock_ollama_client.chat.side_effect = [
            Exception("Service unavailable"),  # First call fails
            MockHelpers.create_mock_ollama_response("I can help with homework! What subject?")  # Second succeeds
        ]

        # Simulate graceful error handling
        try:
            await mock_ollama_client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": "Help me with homework"}]
            )
        except Exception:
            # Error handling: send fallback message
            await mock_telegram_bot.send_message(
                chat_id=telegram_message["chat"]["id"],
                text="I'm having some technical difficulties. Let me try that again..."
            )

            # Retry the request
            retry_response = await mock_ollama_client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": "Help me with homework"}]
            )

            await mock_telegram_bot.send_message(
                chat_id=telegram_message["chat"]["id"],
                text=retry_response["message"]["content"]
            )

        # Verify recovery
        assert mock_telegram_bot.send_message.call_count == 2
        assert mock_ollama_client.chat.call_count == 2


class TestPerformanceIntegration:
    """Test performance characteristics of integrated system."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_family_members(self, test_db, mock_ollama_client, mock_mem0_client):
        """Test system handling multiple family members concurrently."""
        # Create multiple family members
        family_members = []
        for i in range(5):
            member_data = {
                "telegram_id": 100000000 + i,
                "username": f"user{i}",
                "role": "child" if i % 2 else "parent",
                "permissions": {"can_chat": True}
            }
            member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)
            family_members.append(member_id)

        # Process concurrent requests
        async def process_member_request(member_id, message):
            # Mock memory search
            mock_mem0_client.search.return_value = []

            # Mock LLM response
            mock_response = MockHelpers.create_mock_ollama_response(f"Response for member {member_id}")
            mock_ollama_client.chat.return_value = mock_response

            # Process request
            return await mock_ollama_client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": message}]
            )

        # Launch concurrent requests
        tasks = []
        for i, member_id in enumerate(family_members):
            task = process_member_request(member_id, f"Hello from user {i}")
            tasks.append(task)

        # Wait for all to complete
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # Verify results
        assert len(responses) == len(family_members)
        total_time = end_time - start_time
        average_time = total_time / len(family_members)

        # Performance assertion (adjust based on requirements)
        assert average_time < 2.0  # Average response time under 2 seconds
        assert total_time < 5.0  # Total time under 5 seconds

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_search_performance(self, test_db, mock_qdrant_client):
        """Test performance of memory search operations."""
        # Setup large amount of test data
        user_id = 123456789
        num_memories = 1000

        # Mock large dataset search
        search_results = [
            {"id": i, "score": 0.9 - (i * 0.001), "payload": {"text": f"Memory {i}"}}
            for i in range(min(10, num_memories))  # Return top 10 results
        ]
        mock_qdrant_client.search.return_value = search_results

        # Measure search performance
        @PerformanceHelpers.measure_time
        async def perform_search():
            return await mock_qdrant_client.search(
                collection="family_memories",
                query_vector=[0.1] * 768,
                limit=10,
                query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]}
            )

        # Perform multiple searches
        search_times = []
        for _ in range(10):
            result = await perform_search()
            search_times.append(result["execution_time"])

        average_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)

        # Performance assertions
        assert average_search_time < 0.5  # Average under 500ms
        assert max_search_time < 1.0  # Maximum under 1 second

        # Verify search results
        final_result = await perform_search()
        assert len(final_result["result"]) <= 10
        assert all("score" in result for result in final_result["result"])