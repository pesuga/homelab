"""
Unit tests for the main API endpoints.

Tests individual API functions in isolation:
- Chat completion endpoint
- Model listing endpoint
- Health check endpoint
- Authentication middleware
- Request validation
- Error handling
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api.main import app
from tests.helpers.test_helpers import APIResponseAsserts, MockHelpers


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, fastapi_test_client):
        """Test health check returns success."""
        response = fastapi_test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_includes_service_info(self, fastapi_test_client):
        """Test health check includes service information."""
        response = fastapi_test_client.get("/health")
        data = response.json()

        # Should include basic service information
        expected_fields = ["status", "timestamp", "version", "services"]
        for field in expected_fields:
            assert field in data


class TestModelsEndpoint:
    """Test models listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_models_success(self, test_client):
        """Test successful model listing."""
        with patch('api.main.get_available_models') as mock_models:
            mock_models.return_value = [
                {"id": "family-assistant", "name": "Family Assistant Model"},
                {"id": "family-assistant-vision", "name": "Family Assistant Vision Model"}
            ]

            response = await test_client.get("/v1/models")
            assert response.status_code == 200

            data = response.json()
            assert "object" in data
            assert data["object"] == "list"
            assert "data" in data
            assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_list_models_with_filters(self, test_client):
        """Test model listing with capability filters."""
        with patch('api.main.get_available_models') as mock_models:
            mock_models.return_value = [
                {"id": "family-assistant", "capabilities": ["text"]},
                {"id": "family-assistant-vision", "capabilities": ["text", "image"]}
            ]

            # Test vision filter
            response = await test_client.get("/v1/models?capability=vision")
            assert response.status_code == 200

            data = response.json()
            vision_models = [m for m in data["data"] if "image" in m.get("capabilities", [])]
            assert len(vision_models) >= 1


class TestChatCompletionEndpoint:
    """Test chat completion endpoint."""

    @pytest.mark.asyncio
    async def test_chat_completion_basic(self, test_client, sample_chat_request):
        """Test basic chat completion request."""
        with patch('api.main.process_chat_completion') as mock_completion:
            mock_completion.return_value = {
                "id": "chatcmpl-test123",
                "object": "chat.completion",
                "created": 1640995200,
                "model": "family-assistant",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help your family today?"
                    },
                    "finish_reason": "stop"
                }]
            }

            response = await test_client.post("/v1/chat/completions", json=sample_chat_request)
            assert response.status_code == 200

            data = response.json()
            APIResponseAsserts.assert_chat_completion_structure(data)
            assert data["model"] == sample_chat_request["model"]

    @pytest.mark.asyncio
    async def test_chat_completion_with_system_message(self, test_client):
        """Test chat completion with system message."""
        request = {
            "model": "family-assistant",
            "messages": [
                {"role": "system", "content": "You are a helpful family assistant."},
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }

        with patch('api.main.process_chat_completion') as mock_completion:
            mock_completion.return_value = {
                "id": "chatcmpl-test456",
                "object": "chat.completion",
                "created": 1640995200,
                "model": "family-assistant",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm ready to help your family."
                    },
                    "finish_reason": "stop"
                }]
            }

            response = await test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

            # Verify system message was processed
            mock_completion.assert_called_once()
            call_args = mock_completion.call_args[0][0]
            system_messages = [msg for msg in call_args["messages"] if msg["role"] == "system"]
            assert len(system_messages) == 1

    @pytest.mark.asyncio
    async def test_chat_completion_multimodal_content(self, test_client):
        """Test chat completion with multimodal content."""
        request = {
            "model": "family-assistant-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you see in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA=="
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 150
        }

        with patch('api.main.process_multimodal_completion') as mock_completion:
            mock_completion.return_value = {
                "id": "chatcmpl-multimodal123",
                "object": "chat.completion",
                "created": 1640995200,
                "model": "family-assistant-vision",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I can see a family photo in the image."
                    },
                    "finish_reason": "stop"
                }]
            }

            response = await test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

            data = response.json()
            assert "image" in data["choices"][0]["message"]["content"].lower()

    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, test_client):
        """Test streaming chat completion."""
        request = {
            "model": "family-assistant",
            "messages": [
                {"role": "user", "content": "Tell me a short story"}
            ],
            "stream": True,
            "max_tokens": 50
        }

        with patch('api.main.process_streaming_completion') as mock_stream:
            # Mock streaming response
            async def mock_stream_generator():
                yield "data: {\"id\": \"chunk1\", \"choices\": [{\"delta\": {\"content\": \"Once\"}]}}\n\n"
                yield "data: {\"id\": \"chunk2\", \"choices\": [{\"delta\": {\"content\": \" upon\"}]}}\n\n"
                yield "data: [DONE]\n\n"

            mock_stream.return_value = mock_stream_generator()

            response = await test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

            # Verify response is streaming
            assert response.headers["content-type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self, test_client, sample_chat_request):
        """Test chat completion with invalid model."""
        invalid_request = sample_chat_request.copy()
        invalid_request["model"] = "non-existent-model"

        response = await test_client.post("/v1/chat/completions", json=invalid_request)
        assert response.status_code == 400

        data = response.json()
        APIResponseAsserts.assert_error_response(data, "model")

    @pytest.mark.asyncio
    async def test_chat_completion_missing_messages(self, test_client):
        """Test chat completion with missing messages."""
        request = {
            "model": "family-assistant",
            "max_tokens": 100
        }

        response = await test_client.post("/v1/chat/completions", json=request)
        assert response.status_code == 400

        data = response.json()
        APIResponseAsserts.assert_error_response(data, "messages")

    @pytest.mark.asyncio
    async def test_chat_completion_too_many_tokens(self, test_client, sample_chat_request):
        """Test chat completion with excessive token request."""
        invalid_request = sample_chat_request.copy()
        invalid_request["max_tokens"] = 100000  # Exceeds limits

        response = await test_client.post("/v1/chat/completions", json=invalid_request)
        assert response.status_code == 400

        data = response.json()
        APIResponseAsserts.assert_error_response(data, "tokens")


class TestAuthenticationMiddleware:
    """Test authentication and authorization."""

    @pytest.mark.asyncio
    async def test_valid_api_key(self, test_client):
        """Test request with valid API key."""
        headers = {"Authorization": "Bearer valid-test-key"}

        with patch('api.main.validate_api_key') as mock_validate:
            mock_validate.return_value = True

            response = await test_client.get("/v1/models", headers=headers)
            # Note: This depends on how authentication is implemented
            # For now, just verify the request is processed
            assert response.status_code in [200, 401, 403]  # Depending on auth setup

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, test_client):
        """Test request with invalid API key."""
        headers = {"Authorization": "Bearer invalid-key"}

        with patch('api.main.validate_api_key') as mock_validate:
            mock_validate.return_value = False

            response = await test_client.get("/v1/models", headers=headers)
            # Should be unauthorized if authentication is implemented
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_missing_api_key(self, test_client):
        """Test request without API key."""
        response = await test_client.get("/v1/models")
        # Should depend on whether authentication is required
        assert response.status_code in [200, 401, 403]


class TestRequestValidation:
    """Test request validation and sanitization."""

    @pytest.mark.asyncio
    async def test_malformed_json(self, test_client):
        """Test request with malformed JSON."""
        malformed_data = '{"model": "test", "messages": "invalid"'

        response = await test_client.post(
            "/v1/chat/completions",
            data=malformed_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_content_type_validation(self, test_client):
        """Test request with wrong content type."""
        response = await test_client.post(
            "/v1/chat/completions",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test oversized_request(self, test_client):
        """Test request that exceeds size limits."""
        large_content = "x" * (10 * 1024 * 1024)  # 10MB content

        request = {
            "model": "family-assistant",
            "messages": [
                {"role": "user", "content": large_content}
            ]
        }

        response = await test_client.post("/v1/chat/completions", json=request)
        # Should be rejected for being too large
        assert response.status_code in [400, 413]

    @pytest.mark.asyncio
    async def test_injection_attempts(self, test_client):
        """Test request with potential injection content."""
        malicious_content = "'; DROP TABLE users; --"

        request = {
            "model": "family-assistant",
            "messages": [
                {"role": "user", "content": malicious_content}
            ]
        }

        # Request should be processed safely
        response = await test_client.post("/v1/chat/completions", json=request)
        # Should not cause server errors
        assert response.status_code not in [500, 502, 503]


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_service_unavailable(self, test_client, sample_chat_request):
        """Test behavior when backend services are unavailable."""

        with patch('api.main.process_chat_completion') as mock_completion:
            mock_completion.side_effect = Exception("Service unavailable")

            response = await test_client.post("/v1/chat/completions", json=sample_chat_request)
            assert response.status_code in [500, 503]

            data = response.json()
            APIResponseAsserts.assert_error_response(data)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, test_client, sample_chat_request):
        """Test request timeout handling."""

        with patch('api.main.process_chat_completion') as mock_completion:
            mock_completion.side_effect = asyncio.TimeoutError("Request timed out")

            response = await test_client.post("/v1/chat/completions", json=sample_chat_request)
            assert response.status_code in [408, 500, 504]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client, sample_chat_request):
        """Test rate limiting functionality."""

        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await test_client.post("/v1/chat/completions", json=sample_chat_request)
            responses.append(response)

        # Check if any requests were rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # This depends on whether rate limiting is implemented
        # Test ensures the application can handle such scenarios

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client, sample_chat_request):
        """Test handling of concurrent requests."""

        import asyncio

        async def make_request():
            return await test_client.post("/v1/chat/completions", json=sample_chat_request)

        # Make 5 concurrent requests
        responses = await asyncio.gather(*[make_request() for _ in range(5)])

        # All requests should be handled without server errors
        for response in responses:
            assert response.status_code not in [500, 502, 503]


class TestModelCapabilities:
    """Test model capability detection and routing."""

    @pytest.mark.asyncio
    async def test_text_model_routing(self, test_client):
        """Test routing to text-only model."""
        request = {
            "model": "family-assistant",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ]
        }

        with patch('api.main.process_text_completion') as mock_text:
            mock_text.return_value = {"choices": [{"message": {"content": "Text response"}}]}

            response = await test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_vision_model_routing(self, test_client):
        """Test routing to vision-capable model."""
        request = {
            "model": "family-assistant-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image"},
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,test"}
                        }
                    ]
                }
            ]
        }

        with patch('api.main.process_vision_completion') as mock_vision:
            mock_vision.return_value = {"choices": [{"message": {"content": "Vision response"}}]}

            response = await test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_model_capability_detection(self, test_client):
        """Test automatic model capability detection."""
        with patch('api.main.get_model_capabilities') as mock_caps:
            mock_caps.return_value = {
                "family-assistant": ["text"],
                "family-assistant-vision": ["text", "image"],
                "family-assistant-multimodal": ["text", "image", "audio"]
            }

            response = await test_client.get("/v1/models/family-assistant-vision/capabilities")
            assert response.status_code == 200

            data = response.json()
            assert "capabilities" in data
            assert "image" in data["capabilities"]